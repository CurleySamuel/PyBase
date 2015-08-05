import zk.client as zk
import region.client as region
from region.region import region_from_cell
from request import request
import logging
import logging.config
from intervaltree import IntervalTree
from threading import Lock
from time import sleep
from itertools import chain
from filters import _to_filter
import exceptions

# Using a tiered logger such that all submodules propagate through to this
# logger. Changing the logging level here should affect all other modules.
logger = logging.getLogger('pybase')
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': True
        }
    }
})

# This class represents the main Client that will be created by the user.
# All HBase interaction goes through this client.


class MainClient:

    def __init__(self, zkquorum):
        self.zkquorum = zkquorum
        # We need a persistent connection to the meta_client in order to
        # perform any meta lookups in the case that we get a cache miss.
        self.meta_client = None
        # IntervalTree data structure that allows me to create ranges
        # representing known row keys that fall within a specific region. Any
        # 'region look up' is then O(logn)
        self.region_cache = IntervalTree()
        # Takes a client's host:port as key and maps it to a client instance.
        self.reverse_client_cache = {}
        # Mutex used for all caching operations.
        self._cache_lock = Lock()

    """
        HERE LAY CACHE OPERATIONS
    """

    def _add_to_region_cache(self, new_region):
        stop_key = new_region.stop_key
        if stop_key == '':
            # This is hacky but our interval tree requires hard interval stops.
            # So what's the largest char out there? chr(255) -> '\xff'. If
            # you're using '\xff' as a prefix for your rows then this'll cause
            # a cache miss on every request.
            stop_key = '\xff'
        start_key = new_region.table + ',' + new_region.start_key
        stop_key = new_region.table + ',' + stop_key

        with self._cache_lock:
            overlapping_regions = self.region_cache[start_key:stop_key]
            self._close_old_regions(overlapping_regions)
            self.region_cache.remove_overlap(start_key, stop_key)
            self.region_cache[start_key:stop_key] = new_region
            new_region.region_client.regions.append(new_region)

    def _get_from_region_cache(self, table, key):
        with self._cache_lock:
            # We don't care about the last two characters ',:' in the meta_key.
            meta_key = self._construct_meta_key(table, key)[:-2]
            regions = self.region_cache[meta_key]
            try:
                a = regions.pop()
                return a.data
            except KeyError:
                return None

    def _delete_from_region_cache(self, table, start_key):
        # Don't acquire the lock because the calling function should have done
        # so already
        self.region_cache.remove_overlap(table + "," + start_key)

    """
        HERE LAY REQUESTS
    """

    def get(self, table, key, families={}, filters=None):
        # Step 1. Figure out where to send it.
        dest_region = self._find_hosting_region(table, key)
        # Step 2. Build the appropriate pb message.
        rq = request.get_request(dest_region, key, families, filters)
        # Step 3. Send the message and twiddle our thumbs
        response, err = dest_region.region_client._send_request(rq)
        if err is None:
            return Result(response)
        # Step 4. We have an error.

        def original_get():
            return self.get(table, key, families=families, filters=filters)
        return self._handle_remote_exceptions(err, dest_region, response, original_get)

    def put(self, table, key, values):
        dest_region = self._find_hosting_region(table, key)
        rq = request.put_request(dest_region, key, values)
        response, err = dest_region.region_client._send_request(rq)
        if err is None:
            return Result(response)

        def original_put():
            return self.put(table, key, values)
        return self._handle_remote_exceptions(err, dest_region, response, original_put)

    def delete(self, table, key, values):
        dest_region = self._find_hosting_region(table, key)
        rq = request.delete_request(dest_region, key, values)
        response, err = dest_region.region_client._send_request(rq)
        if err is None:
            return Result(response)

        def original_delete():
            return self.delete(table, key, values)
        return self._handle_remote_exceptions(err, dest_region, response, original_delete)

    def append(self, table, key, values):
        dest_region = self._find_hosting_region(table, key)
        rq = request.append_request(dest_region, key, values)
        response, err = dest_region.region_client._send_request(rq)
        if err is None:
            return Result(response)

        def original_append():
            return self.append(table, key, values)
        return self._handle_remote_exceptions(err, dest_region, response, original_append)

    def increment(self, table, key, values):
        dest_region = self._find_hosting_region(table, key)
        rq = request.increment_request(dest_region, key, values)
        response, err = dest_region.region_client._send_request(rq)
        if err is None:
            return Result(response)

        def original_increment():
            return self.increment(table, key, values)
        return self._handle_remote_exceptions(err, dest_region, response, original_increment)

    # Scan can get a bit gnarly - be prepared.
    def scan(self, table, start_key='', stop_key=None, families={}, filters=None):
        # We convert the filter immediately such that it doesn't have to be done
        # for every region. However if the filter has already been converted then
        # we can't convert it again.
        if filters is not None and type(filters).__name__ != "Filter":
            filters = _to_filter(filters)
        cur_region = self._find_hosting_region(table, start_key)
        response_set = Result(None)
        while True:
            region_response_set = Result(None)
            rq = request.scan_request(
                cur_region, start_key, stop_key, families, filters, False, None)
            response, err = cur_region.region_client._send_request(rq)
            if err is not None:
                def current_scan():
                    # We want it to only scan this region then return back here. Otherwise we could face a problem where if
                    # every region misses we now have a stack N recursive calls
                    # deep where N is the total number of regions.
                    return self.scan(table, start_key=cur_region.start_key, stop_key=cur_region.stop_key, families=families, filters=filters)
                region_response_set._append_response(
                    self._handle_remote_exceptions(err, cur_region, response, current_scan))
                if cur_region.stop_key >= stop_key or cur_region.stop_key == '':
                    response_set._append_response(region_response_set)
                    break
                cur_region = self._find_hosting_region(
                    table, cur_region.stop_key)
                continue
            region_response_set._append_response(response)
            while response.more_results_in_region:
                rq = request.scan_request(
                    cur_region, start_key, stop_key, families, filters, False, response.scanner_id)
                # Getting an error here should be very rare as we've already confirmed the region's running. However we
                # gotta be comprehensive :(. We're going to handle the region dying in the middle of a scan by tossing out ONLY
                # this region's partial result and rescanning just this region.
                response, err = cur_region.region_client._send_request(rq)
                if err is not None:
                    def current_scan():
                        return self.scan(table, start_key=cur_region.start_key, stop_key=cur_region.stop_key, families=families, filters=filters)
                    region_response_set = Result(None)
                    region_response_set._append_response(
                        self._handle_remote_exceptions(err, cur_region, response, current_scan))
                    # Region may have been resized when it went unavailable. We need to re-fetch it so locating the next region
                    # works as expected.
                    cur_region = self._find_hosting_region(
                        table, cur_region.start_key)
                    break
                else:
                    region_response_set._append_response(response)
            else:
                rq = request.scan_request(
                    cur_region, start_key, stop_key, families, filters, True, response.scanner_id)
                response, err = cur_region.region_client._send_request(rq)
            response_set._append_response(region_response_set)
            if cur_region.stop_key == '' or (stop_key is not None and cur_region.stop_key > stop_key):
                break
            cur_region = self._find_hosting_region(table, cur_region.stop_key)
        return response_set

    def _handle_remote_exceptions(self, err, rg, response, original_request):
        if err == "RegionServerException":
            # RS is dead. Clear our caches and retry.
            logger.warn("Region server %s:%s refusing connections. Purging cache, sleeping, retrying.",
                        rg.region_client.host, rg.region_client.port)
            self._purge_client(rg.region_client)
            sleep(1.0)
            return original_request()
        elif err == "MasterServerException":
            # Master server be dead. Reestablish and retry.
            self._recreate_meta_client()
            return original_request()
        elif err == "MalformedResponseException":
            # Not much we can do here. HBase response failed to parse.
            logger.warn(
                "Remote Exception: Received an invalid message length in the response from HBase.")
            raise exceptions.MalformedResponseException(
                "Received an invalid message length in the response from HBase")

        elif err == "NoSuchColumnFamilyException":
            logger.warn("Remote Exception: Invalid column family specified.")
            raise exceptions.NoSuchColumnFamilyException(
                "Invalid column family specified")

        elif err == "RegionMovedException":
            logger.warn(
                "Remote Exception: Region moved to a new Region Server.")
            self._purge_region(rg)
            return original_request()

        elif err == "NotServingRegionException":
            logger.warn(
                "Remote Exception: Region is not online. Retrying after 1 second.")
            self._purge_region(rg)
            sleep(1.0)
            return original_request()
        else:
            raise exceptions.PyBaseException(err)

    """
        HERE LAY REGION AND CLIENT DISCOVERY
    """

    def _find_hosting_region(self, table, key):
        dest_region = self._get_from_region_cache(table, key)
        if dest_region is None:
            # We couldn't find the region in our cache.
            logger.info('Region cache miss! Table: %s, Key: %s', table, key)
            dest_region, err = self._discover_region(table, key)
            if err is None:
                return dest_region
            raise exceptions.NoSuchTableException("Invalid table specified.")
        return dest_region

    def _discover_region(self, table, key):
        if self.meta_client is None:
            self._recreate_meta_client()
        meta_key = self._construct_meta_key(table, key)
        meta_rq = request.meta_request(meta_key)
        try:
            response, err = self.meta_client._send_request(meta_rq)
        except AttributeError:
            # self.meta_client is None. Set err and fall to standard
            # error handling below.
            err = "MasterServerException"
        if err is not None:
            # Master is either dead or no longer master. TODO: The region could
            # also just be unavailable.
            logger.warn(
                "Master is either dead or no longer master. Attempting to reestablish.")
            self._recreate_meta_client()
            if self.meta_client is None:
                raise exceptions.MasterServerException(
                    "Master server is unresponsive.")
            response, err = self.meta_client._send_request(meta_rq)
            if err == "NotServingRegionException":
                # So...master is screwed up and not serving the meta region
                # (but ZK claims it's still master). Let's just fail.
                raise exceptions.MasterServerException(
                    "Master not serving META region.")
            return self._discover_region(table, key)

        region, err = self._create_new_region(response, table)
        if err is None:
            return region, None
        elif err == "NoSuchTableException":
            return None, err
        # Master gave us bad information. Sleep and retry.
        logger.warn(
            "Received dead RegionServer information from MasterServer. Retrying in 1 second")
        sleep(1.0)
        return self._discover_region(table, key)

    def _create_new_region(self, response, table):
        cells = response.result.cell
        if len(cells) == 0:
            return None, "NoSuchTableException"
        for cell in cells:
            if cell.qualifier == "regioninfo":
                new_region = region_from_cell(cell)
            elif cell.qualifier == "server":
                server_loc = cell.value
                host, port = cell.value.split(':')
            else:
                continue
        if server_loc in self.reverse_client_cache:
            new_region.region_client = self.reverse_client_cache[server_loc]
        else:
            new_client, err = region.NewClient(host, port)
            if err is not None:
                return None, err
            logger.info("Created new Client for RegionServer %s", server_loc)
            self.reverse_client_cache[server_loc] = new_client
            new_region.region_client = new_client
        self._add_to_region_cache(new_region)
        logger.info("Successfully discovered new region %s", new_region)
        return new_region, None

    def _recreate_meta_client(self):
        if self.meta_client is not None:
            self.meta_client.close()
        ip, port = zk.LocateMeta(self.zkquorum)
        self.meta_client, err = region.NewClient(ip, port)
        if err is not None:
            logger.warn("Cannot reestablish connection to master server")
            return self._recreate_meta_client

    """
        HERE LAY THE MISCELLANEOUS
    """

    def _close_old_regions(self, overlapping_region_intervals):
        for reg in overlapping_region_intervals:
            reg.data.region_client.close()

    def _purge_client(self, region_client):
        with self._cache_lock:
            for reg in region_client.regions:
                self._delete_from_region_cache(reg.table, reg.start_key)
            self.reverse_client_cache.pop(
                region_client.host + ":" + region_client.port, None)
            region_client.close()

    def _construct_meta_key(self, table, key):
        return table + "," + key + ",:"

    def close(self):
        logger.info("Main client received close request.")
        if self.meta_client is not None:
            self.meta_client.close()
        self.region_cache.clear()
        for location, client in self.reverse_client_cache.items():
            client.close()
        self.reverse_client_cache = {}


class Result:

    def __init__(self, rsp):
        self.stale = False
        self.cells = []
        if rsp is not None:
            # We're a mutate/get
            self.cells = rsp.result.cell
            self.exists = rsp.result.exists
            self.stale = self.stale or rsp.result.stale
            try:
                self.processed = rsp.processed
            except AttributeError:
                # We're a get. Don't need no processed.
                pass

    def flatten_cells(self):
        try:
            return list(chain.from_iterable(self.cells))
        except TypeError:
            # We have a single cell.
            return self.cells

    def _append_response(self, rsp):
        try:
            self.cells.extend([result.cell for result in rsp.results])
            self.stale = self.stale or rsp.stale
        except AttributeError as e:
            # This is a result object we're merging instead.
            self.cells.extend(rsp.cells)
            self.stale = self.stale or rsp.stale

# Entrypoint into the whole system. Given a string representing the
# location of ZooKeeper this function will ask ZK for the location of the
# meta table and create the region client responsible for future meta
# lookups (metaclient). Returns an instance of MainClient


def NewClient(zkquorum):
    a = MainClient(zkquorum)
    a._recreate_meta_client()
    return a


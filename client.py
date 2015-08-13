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
from exceptions import *

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

    def __init__(self, zkquorum, pool_size):
        self.zkquorum = zkquorum
        self.pool_size = pool_size
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
        self._meta_lookup_lock = Lock()

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
        try:
            dest_region = None
            # Step 1. Figure out where to send it.
            dest_region = self._find_hosting_region(table, key)
            # Step 2. Build the appropriate pb message.
            rq = request.get_request(dest_region, key, families, filters)
            # Step 3. Send the message and twiddle our thumbs
            response = dest_region.region_client._send_request(rq)
            return Result(response)
            # Step 4. We have an error.
        except PyBaseException as e:
            e._handle_exception(self, dest_region=dest_region)
            return self.get(table, key, families=families, filters=filters)

    def put(self, table, key, values):
        return self._mutate(table, key, values, request.put_request)

    def delete(self, table, key, values):
        return self._mutate(table, key, values, request.delete_request)

    def append(self, table, key, values):
        return self._mutate(table, key, values, request.append_request)

    def increment(self, table, key, values):
        return self._mutate(table, key, values, request.increment_request)

    def _mutate(self, table, key, values, rq_type):
        try:
            dest_region = None
            dest_region = self._find_hosting_region(table, key)
            rq = rq_type(dest_region, key, values)
            response = dest_region.region_client._send_request(rq)
            return Result(response)
        except PyBaseException as e:
            e._handle_exception(self, dest_region=dest_region)
            return self._mutate(table, key, values, rq_type)

    # Scan can get a bit gnarly - be prepared.
    def scan(self, table, start_key='', stop_key=None, families={}, filters=None):
        # We convert the filter immediately such that it doesn't have to be done
        # for every region. However if the filter has already been converted then
        # we can't convert it again.
        if filters is not None and type(filters).__name__ != "Filter":
            filters = _to_filter(filters)
        previous_stop_key = start_key
        result_set = Result(None)
        while True:
            first_response, cur_region = self._scan_hit_region_once(
                previous_stop_key, table, start_key, stop_key, families, filters)
            try:
                second_response = self._scan_region_while_more_results(
                    cur_region, first_response)
            except PyBaseException as e:
                # The RS died in the middle of a scan. Lets restart the scan just
                # for this interval of keys.
                e._handle_exception(self, dest_region=cur_region)
                result_set._append_response(self.scan(
                    table, start_key=previous_stop_key, stop_key=cur_region.stop_key, families=families, filters=filters))
                previous_stop_key = cur_region.stop_key
                continue
            result_set._append_response(first_response)
            result_set._append_response(second_response)
            previous_stop_key = cur_region.stop_key
            if previous_stop_key == '' or (stop_key is not None and previous_stop_key > stop_key):
                break
        return result_set

    def _scan_hit_region_once(self, previous_stop_key, table, start_key, stop_key, families, filters):
        try:
            cur_region = self._find_hosting_region(
                table, previous_stop_key)
        except PyBaseException as e:
            e._handle_exception(self)
            return self._scan_hit_region_once(previous_stop_key, table, start_key, stop_key, families, filters)
        rq = request.scan_request(
            cur_region, start_key, stop_key, families, filters, False, None)
        try:
            response = cur_region.region_client._send_request(rq)
        except PyBaseException as e:
            e._handle_exception(self, dest_region=cur_region)
            return self._scan_hit_region_once(previous_stop_key, table, start_key, stop_key, families, filters)
        return response, cur_region

    def _scan_region_while_more_results(self, cur_region, response):
        response_set = Result(None)
        scanner_id = response.scanner_id
        rq = request.scan_request(
            cur_region, None, None, None, None, False, scanner_id)
        while response.more_results_in_region:
            response = cur_region.region_client._send_request(rq)
            response_set._append_response(response)
        # Now close the scanner.
        rq = request.scan_request(
            cur_region, None, None, None, None, True, scanner_id)
        _ = cur_region.region_client._send_request(rq)
        return response_set

    """
        HERE LAY REGION AND CLIENT DISCOVERY
    """

    def _find_hosting_region(self, table, key):
        dest_region = self._get_from_region_cache(table, key)
        if dest_region is None:
            # Not ideal that we have to lock every thread.
            with self._meta_lookup_lock:
                dest_region = self._get_from_region_cache(table, key)
                if dest_region is None:
                    # We couldn't find the region in our cache.
                    logger.info(
                        'Region cache miss! Table: %s, Key: %s', table, key)
                    dest_region = self._discover_region(table, key)
        return dest_region

    def _discover_region(self, table, key):
        meta_key = self._construct_meta_key(table, key)
        meta_rq = request.meta_request(meta_key)
        try:
            # This will throw standard Region/RegionServer exceptions.
            # We need to catch them and convert them to the Master equivalent.
            response = self.meta_client._send_request(meta_rq)
        except (AttributeError, RegionServerException, RegionException):
            raise MasterServerException(
                self.meta_client.host, self.meta_client.port)
        return self._create_new_region(response, table)

    def _create_new_region(self, response, table):
        cells = response.result.cell
        if len(cells) == 0:
            raise NoSuchTableException("Table does not exist.")
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
            new_client = region.NewClient(host, port, self.pool_size)
            if new_client is None:
                raise RegionServerException(host=host, port=port)
            logger.info("Created new Client for RegionServer %s", server_loc)
            self.reverse_client_cache[server_loc] = new_client
            new_region.region_client = new_client
        self._add_to_region_cache(new_region)
        logger.info("Successfully discovered new region %s", new_region)
        return new_region

    def _recreate_meta_client(self):
        if self.meta_client is not None:
            self.meta_client.close()
        ip, port = zk.LocateMeta(self.zkquorum)
        try:
            self.meta_client = region.NewClient(ip, port, self.pool_size)
        except RegionServerException:
            raise MasterServerException(ip, port)

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

    def _purge_region(self, reg):
        with self._cache_lock:
            self._delete_from_region_cache(reg.table, reg.start_key)
            try:
                reg.region_client.regions.remove(reg)
            except ValueError:
                pass

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


def NewClient(zkquorum, socket_pool_size=1):
    a = MainClient(zkquorum, socket_pool_size)
    a._recreate_meta_client()
    return a


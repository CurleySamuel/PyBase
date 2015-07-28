"""
    TODO: Put in DESIGN.md
    
    So has anyone really been far even as decided to use even go want to do look more like? 
    (What's involved in an HBase client?) Before we get into that be sure to get intimate with 
    the following terminology - 

    - RPC:              Generic term I throw around. My intended meaning is any HBase operation 
                        [Get, Put, Append, Increment, Scan, ...] etc.

    - Client:           Entrypoint for all RPC requests. Returned to the user in NewClient() the 
                        user will then funnel all operations through this client (client.get(), 
                        client.scan(), etc)

    - Region Client:    This is a slight misnomer but we create an instance of a Region Client 
                        class once for every RegionServer. Any operations that interact with that 
                        RegionServer then go through the appropriate Region Client.

    - Meta Client:      A special case of a Region Client, the Meta client's sole purpose in life 
                        is to look up information about which region a specific table/key is 
                        stored in and then where that region lives.

    - Region:           C'mon, you should know this one. A region represents a slice of rows that 
                        exist together as a blob in HBase. An example region could be 
                        { "table": "hodor", "start_key": 1500, "end_key": 4000 }. This means that 
                        all data in table hodor between keys 1500 and 4000 is hosted by this region.

    - Region Server:    Region Servers (RS for short) are physical servers in HBase clusters that 
                        hold a bunch of regions. If we want information for a specific key we have 
                        to find which region that key falls into, which RS hosts that region and 
                        then ask that RS for the juicy deets on that key.

    
    With that out of the way - let's begin. Given a get request, below is the simplified flow.

    Step 0.             Create a meta client instance if not already exists. This involves going to 
                        ZK and asking ZK which server is hosting the meta information for HBase. 
                        We then send a special hello message including details about protocols, 
                        compression, etc.

    Step 1.             Locate the region and RS that holds this key

        Step 1.1        Consult our IntervalTree cache of ranges of rows -> region information. If 
                        we get a cache hit, grab the region client instance from a different cache 
                        and GOTO Step 2.

        Step 1.2        Cache miss? Go to the Meta Client and ask them for the region and region 
                        location for a specific key. If a Region Client doesn't already exist for 
                        that RegionServer (that the region is located on) then create that puppy.

        Step 1.3        Take this fancy new information and insert it into our caches so subsequent 
                        requests can avoid having to ping the meta client.

    Step 2.             Construct the appropriate RPC and send it over the wire.

        Step 2.x        RegionServer ded? Purge the caches of all relevant information and run back
                        to the meta client to get the new deets on regions and region locations. 
                        Create the appropriate clients. GOTO Step 2.

        Step 2.x        RegionServer threw a remote exception back at you? (ex. 'Region not served' 
                        which means there was a split or regions or being shuffled in the 
                        background) Handle it appropriately and either purge your caches and look 
                        up the new location or do something else.    

        Step 2.x        There's room for improvement here where we can try to batch requests going 
                        to the same region. This will introduce some latency but should decrease 
                        network load.

    Step 3.             Listen for the RS's response. Then do a few fancy things to decode the 
                        response and build the results. We want to hide the protobuf layer so 
                        there's some code which alias's pb types and returns a 'Result' object. 
                        Note that because I didn't want to do a O(n) operation over every cell to 
                        copy them to my own type, 'Cell' is still the pb type.


    Easy right? That's the general flow for most RPCs, although Scan's get a little more complex. 
    A scan has to do Steps 1-3 above, N times where N is the number of regions you're scanning over.

    Step 1.             Find the region + RS hosting the start_key of your scan. This is either the 
                        start of the table or a specified start_key if you know it.

    Step 2.             Create a new Scan RPC and send it to the RS. The RS will respond with some 
                        data and a scanner_id. If not all the return data from this region could be
                        fit into one response you have to repeatedly ping this same region until 
                        you've exhausted the scanner.

    Step 3.             Is the end_key of this region greater than the user specified end_key 
                        (or is it the last region for a table?). Woohoo, you're done! Return the 
                        results. Otherwise keep going.

    Step 4.             Given the end_key of the region you just scanned, locate the next region 
                        you should scan. Don't have the region in your caches? Run back to the 
                        meta client and ask nicely then create any appropriate clients. Once you 
                        know the region information, GOTO Step 2 and append your partial result.

"""
import zk.client as zk
import region.client as region
from pb.Client_pb2 import GetRequest, MutateRequest, ScanRequest
from helpers.helpers import families_to_columns, values_to_column_values
import region.region_info as region_info
import logging
import logging.config
from intervaltree import IntervalTree
from collections import defaultdict
from itertools import chain
from threading import Lock
from filters import _to_filter
from socket import error as sockerr

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


# Table + Family used when requesting meta information from the
# MetaRegionServer
metaTableName = "hbase:meta,,1"
metaInfoFamily = {"info": []}


# This class represents the main Client that will be created by the user.
# All HBase interaction goes through this client.
class MainClient:
    # So far we only need to maintain two class variables:
    #   - zkquorum represents the location of ZooKeeper
    #   - meta_client is a client that maintains a persistent connection
    # to the meta regionserver used to discover regions when we get a cache
    # miss on our region cache.

    def __init__(self, zkquorum, client):
        self.zkquorum = zkquorum
        # We need a persistent connection to the meta_client in order to
        # perform any meta lookups in the case that we get a cache miss.
        self.meta_client = client
        # Cache 1
        # IntervalTree data structure that allows me to create ranges
        # representing known row keys that fall within a specific region. Any
        # 'region look up' is then O(logn)
        self.region_inf_cache = IntervalTree()
        # Cache 2
        # Simple dictionary that takes a known region and maps it to our Client
        # instance that serves that region (clients serve entire RegionServers,
        # each of which will serve several regions)
        self.region_client_cache = {}
        # Cache 2.5
        # Opposite of cache 2. Takes a client's host:port as key and maps
        # it to a tuple (instance of client, a list of regions it serves).
        # This allows us to 1) When we discover a new region check if we've
        # already created a Client for that RegionServer and if so, use that
        # one (otherwise create a new). 2) Keep track of how many known regions
        # a given Client serves. If we're purging stale region information and
        # discover a Client no longer tracks any legitimate regions we can
        # close the client and clear up resources.
        self.reverse_region_client_cache = defaultdict(lambda: (None, []))
        # Mutex used for all caching operations.
        self._cache_lock = Lock()

    def _find_hosting_region_client(self, table, key, return_stop=False):
        # We can probably refactor 'return_stop' out as it's only used for Scan
        # RPCs (we need to know a region's stopping key to know where to start
        # scanning next). Leaving the code smell for now.
        meta_key = self._construct_meta_key(table, key)
        region_inf = self._get_from_meta_key_to_region_inf_cache(meta_key)
        if region_inf is None:
            # We couldn't find the region in our cache.
            logger.info('Region cache miss! Table: %s, Key: %s', table, key)
            return self._discover_region(meta_key, return_stop)
        region_name = region_inf.region_name
        region_client = self._get_from_region_name_to_region_client_cache(
            region_name)
        if region_client is None:
            logger.warn('Client cache miss! region_name: %s', region_name)
            # This should very rarely happen. When a region is discovered it's paired with
            # a RegionClient instance. If we have knowledge of the region but
            # not the RegionClient hosting it then that's pretty bad.
            #
            # TODO: We need to handle this properly but for now just
            # re-discover the whole region.
            return self._discover_region(meta_key, return_stop)
        if return_stop:
            return region_client, region_name, region_inf.stop_key
        return region_client, region_name

    # Constructs the string used to query the MetaClient
    def _construct_meta_key(self, table, key):
        return table + "," + key + ",:"

    # This function takes a meta_key and queries the MetaClient for the
    # RegionServer hosting that region.
    def _discover_region(self, meta_key, return_stop):
        rq = GetRequest()
        rq.get.row = meta_key
        rq.get.column.extend(families_to_columns(metaInfoFamily))
        rq.get.closest_row_before = True
        rq.region.type = 1
        rq.region.value = metaTableName
        rsp = self.meta_client._send_rpc(rq, "Get")
        client, region_inf = self._create_new_region(rsp)
        if return_stop:
            return client, region_inf.region_name, region_inf.stop_key
        return client, region_inf.region_name

    # This function takes the result of a MetaQuery, parses it, creates a new
    # RegionClient if necessary then insert into both caches.
    def _create_new_region(self, rsp):
        # Response comes down in different cells, each cell giving different
        # information. Iterate over them and pull what we need.
        for cell in rsp.result.cell:
            if cell.qualifier == "regioninfo":
                region_inf = region_info.region_info_from_cell(cell)
            elif cell.qualifier == "server":
                value = cell.value.split(':')
                host = value[0]
                port = int(value[1])
            else:
                continue
        # Check if we already have a client serving this RegionServer
        client = self.reverse_region_client_cache[host + ":" + str(port)][0]
        if client is None:
            logger.info(
                "Creating new Client for RegionServer %s:%s", host, port)
            client = region.NewClient(host, port)
        # Add to the caches!
        self._add_to_region_name_to_region_client_cache(
            region_inf.region_name, client)
        self._add_to_meta_key_to_region_inf_cache(region_inf)
        logger.info(
            "Successfully discovered new region %s", region_inf.region_name)
        return client, region_inf

    def _add_to_meta_key_to_region_inf_cache(self, region_inf):
        stop_key = region_inf.stop_key
        if stop_key == '':
            # This is hacky but our interval tree requires hard interval stops.
            # So what's the largest char out there? chr(255) -> '\xff'. If
            # you're using '\xff' as a prefix for your rows then this'll cause
            # a cache miss on every request.
            stop_key = '\xff'
        start_key = region_inf.table + ',' + region_inf.start_key
        stop_key = region_inf.table + ',' + stop_key
        # We remove any intervals that overlap with our new range (they're
        # stale data and will cause a HBase region not served error as there
        # was a split). Before we remove them we want to grab them so we can
        # remove stale data from the other cache.
        self._cache_lock.acquire()
        old_regions = self.region_inf_cache[start_key:stop_key]
        self._purge_old_region_clients(old_regions)
        self.region_inf_cache.remove_overlap(start_key, stop_key)
        self.region_inf_cache[start_key:stop_key] = region_inf
        self._cache_lock.release()

    def _get_from_meta_key_to_region_inf_cache(self, meta_key):
        self._cache_lock.acquire()
        # We don't care about the last two characters ',:' in the meta_key.
        meta_key = meta_key[:-2]
        regions = self.region_inf_cache[meta_key]
        self._cache_lock.release()
        if len(regions) == 0:
            return None
        return regions.pop().data

    def _add_to_region_name_to_region_client_cache(self, region_name, region_client):
        self.region_client_cache[region_name] = region_client
        key = region_client.host + ":" + str(region_client.port)
        # Annoying but need to do the below and tuples are immutable -
        #       "host:port": (None, [])
        #        -->
        #       "host:port": (client_instance, [region1])
        self.reverse_region_client_cache[key][1].append(region_name)
        self.reverse_region_client_cache[key] = (
            region_client, self.reverse_region_client_cache[key][1])

    def _get_from_region_name_to_region_client_cache(self, region_name):
        self._cache_lock.acquire()
        to_return = None
        if region_name in self.region_client_cache:
            to_return = self.region_client_cache[region_name]
        self._cache_lock.release()
        return to_return

    def _purge_old_region_clients(self, old):
        for interval in old:
            region_name = interval.data.region_name
            client = self.region_client_cache.pop(region_name, None)
            if client is not None:
                key = client.host + ":" + client.port
                try:
                    # Be aware that .remove is a O(n) operation where n =
                    # number of regions in a RegionServer. Not ideal but this
                    # function should be pretty rare and only really called
                    # during splits.
                    self.reverse_region_client_cache[
                        key][1].remove(region_name)
                except (KeyError, ValueError):
                    pass
                if len(self.reverse_region_client_cache[key][1]) == 0:
                    client.close()
                    self.reverse_region_client_cache.pop(key, None)

    def get(self, table, key, families={}, filters=None):
        pbFilter = _to_filter(filters)

        # Step 1. Figure out where to send it.
        region_client, region_name = self._find_hosting_region_client(
            table, key)

        # Step 2. Build the appropriate pb message.
        rq = GetRequest()
        rq.get.row = key
        rq.get.column.extend(families_to_columns(families))
        rq.region.type = 1
        rq.region.value = region_name
        if pbFilter is not None:
            rq.get.filter.CopyFrom(pbFilter)

        # Step 3. Send the message and twiddle our thumbs
        try:
            response = region_client._send_rpc(rq, "Get")
        except sockerr:
            # Something's bad with the RegionServer. It could be temporary or
            # permanent but we're going to purge our cache for everything in
            # that server and ask Meta for more deets.

            # The parameters here are funky. Here's an explanation -
            #   self._handle_bad_region_server( first, second )
            #           first : a tuple containing the region_client instance and region_name
            #           second : a tuple containing:
            #                           - the name of the function that this call originated from
            #                           - a list of all the original arguments for this call
            return self._handle_bad_region_server((region_client, region_name), ("_get", (table, key, families, filters)))

            # Step 4. Profit
        return Result(response)

    # Little unfortunate we need this function but the region re-establishment
    # code is generic across all request types. Because requests take
    # different arguments (some of which are named) this function takes a list
    # of arguments and calls get with the named arguments properly 'named'
    def _get(self, table, key, families, filters):
        return self.get(table, key, families=families, filters=filters)

    def scan(self, table, start_key=None, stop_key=None, families={}, filters=None):
        pbFilter = _to_filter(filters)
        return self._scan_helper(table, start_key, stop_key, families, pbFilter, None, Result(None))

    def _scan_helper(self, table, start_key, stop_key, families, filters, scanner_id, partial_result):
        cells_to_return = []
        # Create the initial scanner for this region at the specified
        # start_key.
        region_client, rq, region_stop_key = self._scan_build_object(
            table, start_key, stop_key, families, filters, None, False)
        response = region_client._send_rpc(rq, "Scan")
        partial_result._append_response(response)
        # Response returns a boolean 'more_results_in_region' which indicates
        # exactly what you'd think. If it's true then we need to send another
        # query to the same region with a 'scanner_id' that we got back from
        # the response. We don't need to include all the other data as that's
        # persisted across scanner ids.
        while response.more_results_in_region:
            # Keep scanning using the scanner_id and append cells until no more
            # results in region
            region_client, rq, region_stop_key = self._scan_build_object(
                table, start_key, None, None, None, response.scanner_id, False)
            response = region_client._send_rpc(rq, "Scan")
            partial_result._append_response(response)

        # This region's done. Close the region's scanner.
        region_client, rq, region_stop_key = self._scan_build_object(
            table, start_key, None, None, None, response.scanner_id, True)
        response = region_client._send_rpc(rq, "Scan")

        # Should we move on to the next region?
        if region_stop_key == '' or (stop_key is not None and region_stop_key > stop_key):
            return partial_result

        # We should move on!
        # Recursively keep scanning the next region.
        # WARNING - Maximum recursion depth is 998. If we're scanning more than
        # 998 regions then we'll get a stack overflow.
        # TODO: Don't use recursion.
        return self._scan_helper(table, region_stop_key, stop_key, families, filters, None, partial_result)

    def _scan_build_object(self, table, start_key, stop_key, families, filters, scanner_id, close):
        region_client, region_name, region_stop_key = self._find_hosting_region_client(
            table, start_key or '', return_stop=True)
        rq = ScanRequest()
        rq.region.type = 1
        rq.region.value = region_name
        # TODO: configurable. Stole 128 from asynchbase
        rq.number_of_rows = 128
        if close:
            rq.close_scanner = close
        if scanner_id is not None:
            rq.scanner_id = scanner_id
            # Don't need to include the other data if we have a scanner_id set.
            return region_client, rq, region_stop_key
        rq.scan.column.extend(families_to_columns(families))
        rq.scan.start_row = start_key or ''
        if stop_key is not None:
            rq.scan.stop_row = stop_key
        if filters is not None:
            rq.scan.filter.CopyFrom(filters)
        return region_client, rq, region_stop_key

    # All mutate requests (PUT/DELETE/APP/INC) require a values field that looks like:
    #
    #   {
    #      "cf1": {
    #           "mycol": "hodor",
    #           "mycol2": "alsohodor"
    #      },
    #      "cf2": {
    #           "mycolumn7": 24
    #      }
    #   }
    #
    def put(self, table, key, values):
        # Step 1
        region_client, region_name = self._find_hosting_region_client(
            table, key)

        # Step 2
        rq = MutateRequest()
        rq.region.type = 1
        rq.region.value = region_name
        rq.mutation.row = key
        rq.mutation.mutate_type = 2
        rq.mutation.column_value.extend(values_to_column_values(values))

        # Step 3
        try:
            response = region_client._send_rpc(rq, "Mutate")
        except sockerr:
            return self._handle_bad_region_server((region_client, region_name), ("put", (table, key, values)))

        # Step 4
        return Result(response)

    def delete(self, table, key, values):
        # Step 1
        region_client, region_name = self._find_hosting_region_client(
            table, key)

        # Step 2
        rq = MutateRequest()
        rq.region.type = 1
        rq.region.value = region_name
        rq.mutation.row = key
        rq.mutation.mutate_type = 3
        rq.mutation.column_value.extend(
            values_to_column_values(values, delete=True))

        # Step 3
        try:
            response = region_client._send_rpc(rq, "Mutate")
        except sockerr:
            return self._handle_bad_region_server((region_client, region_name), ("delete", (table, key, values)))

        # Step 4
        return Result(response)

    def app(self, table, key, values):
        # Step 1
        region_client, region_name = self._find_hosting_region_client(
            table, key)

        # Step 2
        rq = MutateRequest()
        rq.region.type = 1
        rq.region.value = region_name
        rq.mutation.row = key
        rq.mutation.mutate_type = 0
        rq.mutation.column_value.extend(values_to_column_values(values))

        # Step 3
        try:
            response = region_client._send_rpc(rq, "Mutate")
        except sockerr:
            return self._handle_bad_region_server((region_client, region_name), ("app", (table, key, values)))

        # Step 4
        return Result(response)

    def inc(self, table, key, values):
        # Step 1
        region_client, region_name = self._find_hosting_region_client(
            table, key)

        # Step 2
        rq = MutateRequest()
        rq.region.type = 1
        rq.region.value = region_name
        rq.mutation.row = key
        rq.mutation.mutate_type = 1
        rq.mutation.column_value.extend(values_to_column_values(values))

        # Step 3
        try:
            response = region_client._send_rpc(rq, "Mutate")
        except sockerr:
            return self._handle_bad_region_server((region_client, region_name), ("inc", (table, key, values)))

        # Step 4
        return Result(response)

    # TODO: I /think/ this is threadsafe but needs to be tested.
    #
    # Pretty much any failed socket operations in the region clients will
    # cause this puppy to be called. Purges all cache entries that relate to
    # this region server, closes the client for the server, locates the
    # request's region's new location, establishes a connection with that
    # RegionServer if it doesn't exist already and then redoes the request.
    def _handle_bad_region_server(self, region_tuple, rq_tuple):
        region_client = region_tuple[0]
        key = region_client.host + ":" + str(region_client.port)
        region_name = region_tuple[1]
        logger.warn(
            'Issue detected on RegionServer %s for Region %s', key, region_name)

        # Step 1. Grab the cache mutex
        self._cache_lock.acquire()

        # Step 2. Purge the caches of relevant information.
        # This is our way of removing redundant work. If another thread has
        # already come in here then they'll have generated a new client and
        # deleted the old entry.
        old_client, regions_to_kill = self.reverse_region_client_cache.pop(
            key, (None, None))
        if old_client is not None:
            logger.warn(
                'Purging all cache entries for RegionServer %s and Region %s', key, region_name)
            # We're the first! Purge ALL the caches!
            for region in regions_to_kill:
                self.region_client_cache.pop(region, None)
                # Parse the region_name and construct the meta_key for the
                # start of the region.
                meta_key = region_name[:region_name.rfind(',')]
                del self.region_inf_cache[meta_key]

            # Step 2.5. Close the client for the RegionServer.
            old_client.close()

        # Step 3. Send 'er off again.
        self._cache_lock.release()
        func = getattr(self, rq_tuple[0], None)
        if func is None:
            raise RuntimeError("this should never happen")
        # Recall whatever function failed with the original params.
        return func(*rq_tuple[1])


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
        self.cells.extend([result.cell for result in rsp.results])
        self.stale = self.stale or rsp.stale


# Entrypoint into the whole system. Given a string representing the
# location of ZooKeeper this function will ask ZK for the location of the
# meta table and create the region client responsible for future meta
# lookups (metaclient). Returns an instance of MainClient
def NewClient(zkquorum):
    ip, port = zk.LocateMeta(zkquorum)
    meta_client = region.NewClient(ip, port)
    return MainClient(zkquorum, meta_client)


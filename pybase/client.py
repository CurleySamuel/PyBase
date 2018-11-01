"""
   Copyright 2015 Samuel Curley

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import logging.config
from itertools import chain
from threading import Lock

import pybase.region.client as region
import pybase.zk.client as zk
from intervaltree import IntervalTree

from .exceptions import (MasterServerException, NoSuchTableException,
                         PyBaseException, RegionException, RegionServerException)
from .filters import _to_filter
from .region.region import region_from_cell
from .request import request

# Using a tiered logger such that all submodules propagate through to this
# logger. Changing the logging level here should affect all other modules.
logger = logging.getLogger('pybase')


class MainClient(object):

    def __init__(self, zkquorum, pool_size):
        # Location of the ZooKeeper quorum (csv)
        self.zkquorum = zkquorum
        # Connection pool size per region server (and master!)
        self.pool_size = pool_size
        # Persistent connection to the master server.
        self.master_client = None
        # IntervalTree data structure that allows me to create ranges
        # representing known row keys that fall within a specific region. Any
        # 'region look up' is then O(logn)
        self.region_cache = IntervalTree()
        # Takes a client's host:port as key and maps it to a client instance.
        self.reverse_client_cache = {}
        # Mutex used for all caching operations.
        self._cache_lock = Lock()
        # Mutex used so only one thread can request meta information from
        # the master at a time.
        self._master_lookup_lock = Lock()

    """
        HERE LAY CACHE OPERATIONS
    """

    def _add_to_region_cache(self, new_region):
        stop_key = new_region.stop_key
        if stop_key == b'':
            # This is hacky but our interval tree requires hard interval stops.
            # So what's the largest char out there? chr(255) -> '\xff'. If
            # you're using '\xff' as a prefix for your rows then this'll cause
            # a cache miss on every request.
            stop_key = b'\xff'
        # Keys are formatted like: 'tablename,key'
        start_key = new_region.table + b',' + new_region.start_key
        stop_key = new_region.table + b',' + stop_key

        # Only let one person touch the cache at once.
        with self._cache_lock:
            # Get all overlapping regions (overlapping == stale)
            overlapping_regions = self.region_cache[start_key:stop_key]
            # Close the overlapping regions.
            self._close_old_regions(overlapping_regions)
            # Remove the overlapping regions.
            self.region_cache.remove_overlap(start_key, stop_key)
            # Insert my region.
            self.region_cache[start_key:stop_key] = new_region
            # Add this region to the region_client's internal
            # list of all the regions it serves.
            new_region.region_client.regions.append(new_region)

    def _get_from_region_cache(self, table, key):
        # Only let one person touch the cache at once.
        with self._cache_lock:
            # We don't care about the last two characters ',:' in the meta_key.
            # 'table,key,:' --> 'table,key'
            meta_key = self._construct_meta_key(table, key)[:-2]
            # Fetch the region that serves this key
            regions = self.region_cache[meta_key]
            try:
                # Returns a set. Pop the element from the set.
                # (there shouldn't be more than 1 elem in the set)
                a = regions.pop()
                return a.data
            except KeyError:
                # Returned set is empty? Cache miss!
                return None

    def _delete_from_region_cache(self, table, start_key):
        # Don't acquire the lock because the calling function should have done
        # so already
        self.region_cache.remove_overlap(table + b"," + start_key)

    """
        HERE LAY REQUESTS
    """

    def get(self, table, key, families={}, filters=None):
        """
        get a row or specified cell with optional filter
        :param table: hbase table
        :param key: row key
        :param families: (optional) specifies columns to get,
          e.g., {"columnFamily1":["col1","col2"], "colFamily2": "col3"}
        :param filters: (optional) column filters
        :return: response with cells
        """
        try:
            # Step 0. Set dest_region to None so if an exception is
            # thrown in _find_hosting_region, the exception handling
            # doesn't break trying to reference dest_region.
            dest_region = None
            # Step 1. Figure out where to send it.
            dest_region = self._find_hosting_region(table, key)
            # Step 2. Build the appropriate pb message.
            rq = request.get_request(dest_region, key, families, filters)
            # Step 3. Send the message and twiddle our thumbs.
            response = dest_region.region_client._send_request(rq)
            # Step 4. Success.
            return Result(response)
        except PyBaseException as e:
            # Step X. Houston, we have an error. The cool thing about how
            # this is coded is that exceptions know how to handle themselves.
            # All we need to do is call _handle_exception and everything should
            # be happy! If it cannot handle itself (unrecoverable) then it will
            # re-raise the exception in the handle method and we'll die too.
            #
            # We pass dest_region in because the handling code needs to know
            # which region or region_client it needs to reestablish.
            e._handle_exception(self, dest_region=dest_region)
            # Everything should be dandy now. Repeat the request!
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
        # Same exact methodology as 'get'. Because all mutate requests have
        # equivalent code I've combined them into a single function.
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
        # we can't convert it again. This means that even though we send out N RPCs
        # we only have to package the filter pb type once.
        if filters is not None and type(filters).__name__ != "Filter":
            filters = _to_filter(filters)
        previous_stop_key = start_key
        # Holds the contents of all responses. We return this at the end.
        result_set = Result(None)
        # We're going to need to loop over every relevant region. Break out
        # of this loop once we discover there are no more regions left to scan.
        while True:
            # Finds the first region and sends the initial message to it.
            first_response, cur_region = self._scan_hit_region_once(
                previous_stop_key, table, start_key, stop_key, families, filters)
            try:
                # Now we need to keep pinging this region for more results until
                # it has no more results to return. We can change how many rows it
                # returns for each call in the Requests module but I picked a
                # pseudo-arbitrary figure (alright, fine, I stole it from
                # asynchbase)
                #
                # We pass in first_response so it can pull out the scanner_id
                # from the first response.
                second_response = self._scan_region_while_more_results(
                    cur_region, first_response)
            except PyBaseException as e:
                # Something happened to the region/region client in the middle
                # of a scan. We're going to handle it by...
                #
                # Handle the exception.
                e._handle_exception(self, dest_region=cur_region)
                # Recursively scan JUST this range of keys in the region (it could have been split
                # or merged so this recursive call may be scanning multiple regions or only half
                # of one region).
                result_set._append_response(self.scan(
                    table, start_key=previous_stop_key, stop_key=cur_region.stop_key,
                    families=families, filters=filters))
                # We continue here because we don't want to append the
                # first_response results to the result_set. When we did the
                # recursive scan it rescanned whatever the first_response
                # initially contained. Appending both will produce duplicates.
                previous_stop_key = cur_region.stop_key
                if previous_stop_key == b'' or \
                        (stop_key is not None and previous_stop_key > stop_key):
                    break
                continue
            # Both calls succeeded! Append the results to the result_set.
            result_set._append_response(first_response)
            result_set._append_response(second_response)
            # Update the new previous_stop_key (so the next iteration can
            # lookup the next region to scan)
            previous_stop_key = cur_region.stop_key
            # Stopping criteria. This region is either the end ('') or the end of this region is
            # beyond the specific stop_key.
            if previous_stop_key == '' or (stop_key is not None and previous_stop_key > stop_key):
                break
        return result_set

    def _scan_hit_region_once(self, previous_stop_key, table, start_key, stop_key, families,
                              filters):
        try:
            # Lookup the next region to scan by searching for the
            # previous_stop_key (region keys are inclusive on the start and
            # exclusive on the end)
            cur_region = self._find_hosting_region(
                table, previous_stop_key)
        except PyBaseException as e:
            # This means that either Master is down or something's funky with the META region.
            # Try handling it and recursively perform the same call again.
            e._handle_exception(self)
            return self._scan_hit_region_once(previous_stop_key, table, start_key, stop_key,
                                              families, filters)
        # Create the scan request object. The last two values are 'Close' and
        # 'Scanner_ID' respectively.
        rq = request.scan_request(
            cur_region, start_key, stop_key, families, filters, False, None)
        try:
            # Send the request.
            response = cur_region.region_client._send_request(rq)
        except PyBaseException as e:
            # Uh oh. Probably a region/region server issue. Handle it and try
            # again.
            e._handle_exception(self, dest_region=cur_region)
            return self._scan_hit_region_once(previous_stop_key, table, start_key, stop_key,
                                              families, filters)
        return response, cur_region

    def _scan_region_while_more_results(self, cur_region, response):
        # Create our own intermediate response set.
        response_set = Result(None)
        # Grab the scanner_id from the first_response.
        scanner_id = response.scanner_id
        # We only need to specify the scanner_id here because the region we're
        # pinging remembers our query based on the scanner_id.
        rq = request.scan_request(
            cur_region, None, None, None, None, False, scanner_id)
        while response.more_results_in_region:
            # Repeatedly hit it until empty. Note that we're not handling any
            # exceptions here, instead letting them bubble up because if any
            # of these calls fail we need to rescan the whole region (it seems
            # like a lot of work to search the results for the max row key that
            # we've received so far and rescan from there up)
            response = cur_region.region_client._send_request(rq)
            response_set._append_response(response)
        # Now close the scanner.
        rq = request.scan_request(
            cur_region, None, None, None, None, True, scanner_id)
        cur_region.region_client._send_request(rq)
        # Close it and return the results!
        return response_set

    """
        HERE LAY REGION AND CLIENT DISCOVERY
    """

    def _find_hosting_region(self, table, key):
        # Check if it's in the cache already.
        dest_region = self._get_from_region_cache(table, key)
        if dest_region is None:
            # We have to reach out to master for the results.
            with self._master_lookup_lock:
                # Not ideal that we have to lock every thread however we limit
                # concurrent meta requests to one. This is because of the case
                # where 1000 greenlets all fail simultaneously we don't want
                # 1000 requests shot off to the master (all looking for the
                # same response). My solution is to only let one through at a
                # time and then when it's your turn, check the cache again to
                # see if one of the greenlets let in before you already fetched
                # the meta or not. We can't bucket greenlets and selectively
                # wake them up simply because we have no idea which key falls
                # into which region. We can bucket based on key but that's a
                # lot of overhead for an unlikely scenario.
                dest_region = self._get_from_region_cache(table, key)
                if dest_region is None:
                    # Nope, still not in the cache.
                    logger.debug(
                        'Region cache miss! Table: %s, Key: %s', table, key)
                    # Ask master for region information.
                    dest_region = self._discover_region(table, key)
        return dest_region

    def _discover_region(self, table, key):
        meta_key = self._construct_meta_key(table, key)
        # Create the appropriate meta request given a meta_key.
        meta_rq = request.master_request(meta_key)
        try:
            # This will throw standard Region/RegionServer exceptions.
            # We need to catch them and convert them to the Master equivalent.
            response = self.master_client._send_request(meta_rq)
        except (AttributeError, RegionServerException, RegionException):
            if self.master_client is None:
                # I don't know why this can happen but it does.
                raise MasterServerException(None, None)
            raise MasterServerException(
                self.master_client.host, self.master_client.port)
        # Master gave us a response. We need to run and parse the response,
        # then do all necessary work for entering it into our structures.
        return self._create_new_region(response, table)

    def _create_new_region(self, response, table):
        cells = response.result.cell
        # We have a valid response but no cells? Apparently that means the
        # table doesn't exist!
        if len(cells) == 0:
            raise NoSuchTableException("Table does not exist.")
        # We get ~4 cells back each holding different information. We only care
        # about two of them.
        for cell in cells:
            if cell.qualifier == "regioninfo":
                # Take the regioninfo information and parse it into our own
                # Region representation.
                new_region = region_from_cell(cell)
            elif cell.qualifier == "server":
                # Grab the host, port of the Region Server that this region is
                # hosted on.
                server_loc = cell.value
                host, port = cell.value.split(':')
            else:
                continue
        # Do we have an existing client for this region server already?
        if server_loc in self.reverse_client_cache:
            # If so, grab it!
            new_region.region_client = self.reverse_client_cache[server_loc]
        else:
            # Otherwise we need to create a new region client instance.
            new_client = region.NewClient(host, port, self.pool_size)
            if new_client is None:
                # Welp. We can't connect to the server that the Master
                # supplied. Raise an exception.
                raise RegionServerException(host=host, port=port)
            logger.info("Created new Client for RegionServer %s", server_loc)
            # Add it to the host,port -> instance of region client map.
            self.reverse_client_cache[server_loc] = new_client
            # Attach the region_client to the region.
            new_region.region_client = new_client
        # Region's set up! Add this puppy to the cache so future requests can
        # use it.
        self._add_to_region_cache(new_region)
        logger.info("Successfully discovered new region %s", new_region)
        return new_region

    def _recreate_master_client(self):
        if self.master_client is not None:
            # yep, still no idea why self.master_client can be set to None.
            self.master_client.close()
        # Ask ZooKeeper for the location of the Master.
        ip, port = zk.LocateMaster(self.zkquorum)
        try:
            # Try creating a new client instance and setting it as the new
            # master_client.
            self.master_client = region.NewClient(ip, port, self.pool_size)
        except RegionServerException:
            # We can't connect to the address that ZK supplied. Raise an
            # exception.
            raise MasterServerException(ip, port)

    """
        HERE LAY THE MISCELLANEOUS
    """

    def _close_old_regions(self, overlapping_region_intervals):
        # Loop over the regions to close and close whoever their
        # attached client is.
        #
        # TODO: ...should we really be killing a client unneccessarily?
        for reg in overlapping_region_intervals:
            reg.data.region_client.close()

    def _purge_client(self, region_client):
        # Given a client to close, purge all of it's known hosted regions from
        # our cache, delete the reverse lookup entry and close the client
        # clearing up any file descriptors.
        with self._cache_lock:
            for reg in region_client.regions:
                self._delete_from_region_cache(reg.table, reg.start_key)
            self.reverse_client_cache.pop(
                region_client.host + ":" + region_client.port, None)
            region_client.close()

    def _purge_region(self, reg):
        # Given a region, deletes it's entry from the cache and removes itself
        # from it's region client's region list.
        with self._cache_lock:
            self._delete_from_region_cache(reg.table, reg.start_key)
            try:
                reg.region_client.regions.remove(reg)
            except ValueError:
                pass

    def _construct_meta_key(self, table, key):
        return table + b"," + key + b",:"

    def close(self):
        logger.info("Main client received close request.")
        # Close the master client.
        if self.master_client is not None:
            self.master_client.close()
        # Clear the region cache.
        self.region_cache.clear()
        # Close each open region client.
        for location, client in self.reverse_client_cache.items():
            client.close()
        self.reverse_client_cache = {}


class Result(object):

    # Called like Result(my_response), takes all the wanted data from
    # my_response and puts it into our own result structure.
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

    # Scans come back with an embedded list of cells (each sublist represents
    # a row so a scan over 1000 rows => [[cell1,cell2]*1000])
    #
    # This is a quick helper that flattens the list of lists into a single
    # list of cells. Picked chain to flatten as apparently it's pretty quick.
    def flatten_cells(self):
        try:
            return list(chain.from_iterable(self.cells))
        except TypeError:
            # We have a single cell.
            return self.cells

    # Result(my_rsp1)._append_response(my_rsp2) will concatenate the results
    # of the two responses. If any of the N responses are stale I set the
    # stale bit for everything.
    def _append_response(self, rsp):
        try:
            self.cells.extend([result.cell for result in rsp.results])
            self.stale = self.stale or rsp.stale
        except AttributeError:
            # This is a single result object we're merging instead.
            self.cells.extend(rsp.cells)
            self.stale = self.stale or rsp.stale


# Entrypoint into the whole system. Given a string representing the
# location of ZooKeeper this function will ask ZK for the location of the
# meta table and create the region client responsible for future meta
# lookups (masterclient). Returns an instance of MainClient
def NewClient(zkquorum, socket_pool_size=1):
    # Create the main client.
    a = MainClient(zkquorum, socket_pool_size)
    # Create the master client.
    a._recreate_master_client()
    return a

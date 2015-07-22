import zk.client as zk
import region.client as region
from pb.Client_pb2 import GetRequest, MutateRequest
from helpers.helpers import families_to_columns, values_to_column_values
import region.region_info as region_info
import sys
import logging
import logging.config

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
        self.meta_client = client

    def _find_hosting_region_client(self, table, key):
        meta_key = self._construct_meta_key(table, key)
        region_name = self._get_from_meta_key_to_region_name_cache(meta_key)
        if region_name is None:
            # We couldn't find the region in our cache.
            logger.info('Region cache miss! Table: %s, Key: %s', table, key)
            return self._discover_region(meta_key)
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
            return self._discover_region(meta_key)
        return region_client, region_name

    # Constructs the string used to query the MetaClient
    def _construct_meta_key(self, table, key):
        return table + "," + key + ",:"

    # This function takes a meta_key and queries the MetaClient for the
    # RegionServer hosting that region.
    def _discover_region(self, meta_key):
        rq = GetRequest()
        rq.get.row = meta_key
        rq.get.column.extend(families_to_columns(metaInfoFamily))
        rq.get.closest_row_before = True
        rq.region.type = 1
        rq.region.value = metaTableName
        rsp = self.meta_client._send_rpc(rq, "Get")
        return self._create_new_region(rsp)

    # This function takes the result of a MetaQuery, parses it, creates a new
    # RegionClient if necessary then insert into both caches.
    def _create_new_region(self, rsp):
        for cell in rsp.result.cell:
            if cell.qualifier == "regioninfo":
                region_inf = region_info.region_info_from_cell(cell)
            elif cell.qualifier == "server":
                value = cell.value.split(':')
                host = value[0]
                port = int(value[1])
            else:
                continue
        client = self._get_from_region_inf_to_region_client_cache(region_inf)
        if client is None:
            client = region.NewClient(host, port)
        self._add_to_meta_key_to_region_name_cache(region_inf)
        self._add_to_region_inf_to_region_client_cache(region_inf, client)
        return client, region_inf.region_name

    def _add_to_meta_key_to_region_name_cache(self, region_inf):
        return None

    def _get_from_meta_key_to_region_name_cache(self, meta_key):
        return None

    def _add_to_region_inf_to_region_client_cache(self, region_inf, region_client):
        return None

    def _get_from_region_inf_to_region_client_cache(self, region_name):
        return None

    def get(self, table, key, families={}, filters=None):

        # Step 1. Figure out where to send it.
        region_client, region_name = self._find_hosting_region_client(
            table, key)

        # Step 2. Build the appropriate pb message.
        rq = GetRequest()
        rq.get.row = key
        rq.get.column.extend(families_to_columns(families))
        rq.region.type = 1
        rq.region.value = region_name

        # Step 3. Send the message and twiddle our thumbs
        response = region_client._send_rpc(rq, "Get")

        # Step 4. Profit
        return response.result.cell

    def scan(self, table, families={}, filters=None):
        # Scan is much harder. TODO
        pass

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
        response = region_client._send_rpc(rq, "Mutate")

        # Step 4
        # Do we need to return anything?

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
        response = region_client._send_rpc(rq, "Mutate")

        # Step 4
        # Do we need to return anything?

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
        response = region_client._send_rpc(rq, "Mutate")

        # Step 4
        # Do we need to return anything?

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
        response = region_client._send_rpc(rq, "Mutate")

        # Step 4
        # Do we need to return anything?


# Entrypoint into the whole system. Given a string representing the
# location of ZooKeeper this function will ask ZK for the location of the
# meta table and create the region client responsible for future meta
# lookups (metaclient). Returns an instance of MainClient
def NewClient(zkquorum):
    ip, port = zk.LocateMeta(zkquorum)
    meta_client = region.NewClient(ip, port)
    return MainClient(zkquorum, meta_client)


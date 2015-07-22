import zk.client as zk
import region.client as region
from pb.Client_pb2 import GetRequest
from helpers.helpers import families_to_columns
import region.region_info as region_info

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

    # Given a table and key, locate the appropriate RegionServer by searching
    # our cache and then defaulting to asking the MetaClient where it's at.
    def _find_region_client_by_key(self, table, key):
        meta_key = self._construct_meta_key(table, key)
        region_client = self._search_cache_for_region(meta_key)
        if region_client is None:
            region_client = self._discover_region(meta_key)
        return region_client

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

    # This function takes the result of a MetaQuery and parses it to create the
    # corresponding region client.
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
        new_client = region.NewClient(host, port)
        return self._add_region_to_cache(region_inf, new_client)

    # Given a recently created region client and it's respective information,
    # store it in our caches so future requests for the same region don't get
    # a cache miss as well.
    def _add_region_to_cache(self, region_inf, new_client):
        return new_client

    # Given a meta_key, return the region client serving that region or return
    # None if no region clients are serving that region
    def _search_cache_for_region(self, meta_key):
        return None


# Entrypoint into the whole system. Given a string representing the
# location of ZooKeeper this function will ask ZK for the location of the
# meta table and create the region client responsible for future meta
# lookups (metaclient). Returns an instance of MainClient
def NewClient(zkquorum):
    ip, port = zk.LocateMeta(zkquorum)
    meta_client = region.NewClient(ip, port)
    return MainClient(zkquorum, meta_client)


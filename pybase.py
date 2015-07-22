import zk.client as zk
import region.client as region
from pb.Client_pb2 import GetRequest, Column

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
        region_client = self._discover_region(meta_key)
        return region_client

    # Constructs the string used to query the MetaClient
    def _construct_meta_key(self, table, key):
        return table + "," + key + ",:"

    # This function takes a meta_key and queries the MetaClient for the
    # RegionServer hosting that region.
    def _discover_region(self, key):
        rq = GetRequest()
        rq.get.row = key
        rq.get.column.extend(_families_to_columns(metaInfoFamily))
        rq.get.closest_row_before = True
        rq.region.type = 1
        rq.region.value = metaTableName
        rsp = self.meta_client._send_rpc(rq, "Get")
        return rsp


# Entrypoint into the whole system. Given a string representing the
# location of ZooKeeper this function will ask ZK for the location of the
# meta table and create the region client responsible for future meta
# lookups (metaclient). Returns an instance of MainClient
def NewClient(zkquorum):
    ip, port = zk.LocateMeta(zkquorum)
    meta_client = region.NewClient(ip, port)
    return MainClient(zkquorum, meta_client)


#  Converts a dictionary specifying ColumnFamilys -> Qualifiers into the protobuf type.
#
#    Families should look like
#    {
#        "columnFamily1": [
#            "qual1",
#            "qual2"
#        ],
#        "columnFamily2": [
#            "qual3"
#        ]
#    }
def _families_to_columns(fam):
    cols = []
    for key in fam.keys():
        c = Column()
        c.family = key
        c.qualifier.extend(fam[key])
        cols.append(c)
    return cols


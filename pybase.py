import zk.client as zk
import region.client as region
from pb.HBase_pb2 import RegionInfo
from pb.Client_pb2 import GetRequest
from pb.RPC_pb2 import RequestHeader
from struct import pack


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

    # Prototype function that allows me to test functionality. Will be
    # reworked.
    def _find_region(self):
        return self.meta_client._find_region_by_key("test", "20")


# Entrypoint into the whole system. Given a string representing the
# location of ZooKeeper this function will ask ZK for the location of the
# meta table and create the region client responsible for future meta
# lookups (metaclient). Returns an instance of MainClient
def NewClient(zkquorum):
    ip, port = zk.LocateMeta(zkquorum)
    meta_client = region.NewClient(ip, port)
    return MainClient(zkquorum, meta_client)


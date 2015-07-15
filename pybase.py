import zk.zk as zk
import region.region as region
from pb.HBase_pb2 import RegionInfo
from pb.Client_pb2 import GetRequest
from pb.RPC_pb2 import RequestHeader
from struct import pack


class MainClient:

    def __init__(self, zkquorum, client):
        self.zkquorum = zkquorum
        self.meta_client = client

    def _find_region(self):
        return self.meta_client._find_region_by_key("test", "20")


def NewClient(zkquorum):
    ip, port = zk.LocateMeta(zkquorum)
    meta_client = region.NewClient(ip, port)
    return MainClient(zkquorum, meta_client)


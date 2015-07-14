import zk.zk as zk
import region.region as region


class Client:
    def __init__(self, zkquorum, client):
        self.zkquorum = zkquorum
        self.meta_client = client


def NewClient(zkquorum):
    ip, port = zk.LocateMeta(zkquorum)
    meta_client = region.NewClient(ip, port)
    return Client(zkquorum, meta_client)

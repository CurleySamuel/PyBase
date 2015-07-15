from kazoo.client import KazooClient
from pb.ZooKeeper_pb2 import MetaRegionServer
from struct import unpack
import logging
logging.basicConfig()

znode = "/hbase"


def LocateMeta(zkquorum):
    zk = KazooClient(hosts=zkquorum)
    zk.start()
    rsp, znodestat = zk.get(znode + "/meta-region-server")
    zk.stop()
    if len(rsp) == 0:
        raise Exception
    first_byte, meta_length = unpack(">cI", rsp[:5])
    if first_byte != '\xff':
        raise Exception
    if meta_length < 1 or meta_length > 65000:
        raise Exception
    magic = unpack(">I", rsp[meta_length+5:meta_length+9])[0]
    if magic != 1346524486:
        # 4 bytes: PBUF
        raise Exception
    rsp = rsp[meta_length+9:]
    meta = MetaRegionServer()
    meta.ParseFromString(rsp)
    return meta.server.host_name, meta.server.port

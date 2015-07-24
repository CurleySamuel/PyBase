from kazoo.client import KazooClient
from kazoo.handlers.threading import KazooTimeoutError
from kazoo.exceptions import NoNodeError
from pb.ZooKeeper_pb2 import MetaRegionServer
from struct import unpack
import logging
logger = logging.getLogger('pybase.' + __name__)
logger.setLevel(logging.DEBUG)

znode = "/hbase"


# LocateMeta takes a string representing the location of the ZooKeeper
# quorum. It then asks ZK for the location of the MetaRegionServer,
# returning a tuple containing (host_name, port).
def LocateMeta(zkquorum):

    # Using Kazoo for interfacing with ZK
    zk = KazooClient(hosts=zkquorum)
    try:
        zk.start(timeout=5)
    except KazooTimeoutError:
        raise RuntimeError(
            "Cannot connect to ZooKeeper at {}".format(zkquorum))
    # MetaRegionServer information is located at /hbase/meta-region-server
    try:
        rsp, znodestat = zk.get(znode + "/meta-region-server")
    except NoNodeError:
        raise RuntimeError(
            "ZooKeeper does not contain meta-region-server node.")
    # We don't need to maintain a connection to ZK. If we need it again we'll
    # recreate the connection. A possible future implementation can subscribe
    # to ZK and listen for when RegionServers go down, then pre-emptively
    # reestablish those regions instead of waiting for a failed rpc to come
    # back. Only issue is that if too many clients subscribe ZK may become
    # overloaded.
    zk.stop()
    if len(rsp) == 0:
        # Empty response is bad.
        raise RuntimeError("ZooKeeper returned an empty response")
    # The first byte must be \xff and the next four bytes are a little-endian
    # uint32 containing the length of the meta.
    first_byte, meta_length = unpack(">cI", rsp[:5])
    if first_byte != '\xff':
        # Malformed response
        raise RuntimeError("ZooKeeper returned an invalid response")
    if meta_length < 1 or meta_length > 65000:
        # Is this really an error?
        raise RuntimeError("ZooKeeper returned too much meta information")
    # ZNode data in HBase are serialized protobufs with a four byte magic
    # 'PBUF' prefix.
    magic = unpack(">I", rsp[meta_length + 5:meta_length + 9])[0]
    if magic != 1346524486:
        # 4 bytes: PBUF
        raise RuntimeError(
            "ZooKeeper returned an invalid response (are you running a version of HBase supporting Protobufs?)")
    rsp = rsp[meta_length + 9:]
    meta = MetaRegionServer()
    meta.ParseFromString(rsp)
    logger.info('Discovered MetaClient at %s:%s',
                meta.server.host_name, meta.server.port)
    return meta.server.host_name, meta.server.port


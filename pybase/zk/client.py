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
from __future__ import absolute_import, print_function

import logging
from struct import unpack
from time import sleep

from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError
from kazoo.handlers.threading import KazooTimeoutError

from ..exceptions import (ZookeeperConnectionException,
                          ZookeeperResponseException, ZookeeperZNodeException)
from ..pb.ZooKeeper_pb2 import MetaRegionServer

logger = logging.getLogger('pybase.' + __name__)
logger.setLevel(logging.DEBUG)

znode = "/hbase"


# LocateMeta takes a string representing the location of the ZooKeeper
# quorum. It then asks ZK for the location of the MetaRegionServer,
# returning a tuple containing (host_name, port).
def LocateMaster(zkquorum, establish_connection_timeout=5, missing_znode_retries=5, zk=None):

    if zk is None:
        # Using Kazoo for interfacing with ZK
        zk = KazooClient(hosts=zkquorum)
    try:
        zk.start(timeout=establish_connection_timeout)
    except KazooTimeoutError:
        raise ZookeeperConnectionException(
            "Cannot connect to ZooKeeper at {}".format(zkquorum))
    # MetaRegionServer information is located at /hbase/meta-region-server
    try:
        rsp, znodestat = zk.get(znode + "/meta-region-server")
    except NoNodeError:
        if missing_znode_retries == 0:
            raise ZookeeperZNodeException(
                "ZooKeeper does not contain meta-region-server node.")
        logger.warn("ZooKeeper does not contain meta-region-server node. Retrying in 2 seconds. "
                    "(%s retries remaining)", missing_znode_retries)
        sleep(2.0)
        return LocateMaster(zkquorum, establish_connection_timeout=establish_connection_timeout,
                            missing_znode_retries=missing_znode_retries - 1, zk=zk)
    # We don't need to maintain a connection to ZK. If we need it again we'll
    # recreate the connection. A possible future implementation can subscribe
    # to ZK and listen for when RegionServers go down, then pre-emptively
    # reestablish those regions instead of waiting for a failed rpc to come
    # back. Only issue is that if too many clients subscribe ZK may become
    # overloaded.
    zk.stop()
    if len(rsp) == 0:
        # Empty response is bad.
        raise ZookeeperResponseException(
            "ZooKeeper returned an empty response")
    # The first byte must be \xff and the next four bytes are a little-endian
    # uint32 containing the length of the meta.
    first_byte, meta_length = unpack(">cI", rsp[:5])
    if first_byte != '\xff':
        # Malformed response
        raise ZookeeperResponseException(
            "ZooKeeper returned an invalid response")
    if meta_length < 1 or meta_length > 65000:
        # Is this really an error?
        raise ZookeeperResponseException(
            "ZooKeeper returned too much meta information")
    # ZNode data in HBase are serialized protobufs with a four byte magic
    # 'PBUF' prefix.
    magic = unpack(">I", rsp[meta_length + 5:meta_length + 9])[0]
    if magic != 1346524486:
        # 4 bytes: PBUF
        raise ZookeeperResponseException("ZooKeeper returned an invalid response (are you running "
                                         "a version of HBase supporting Protobufs?)")
    rsp = rsp[meta_length + 9:]
    meta = MetaRegionServer()
    meta.ParseFromString(rsp)
    logger.info('Discovered Master at %s:%s',
                meta.server.host_name, meta.server.port)
    return meta.server.host_name, meta.server.port

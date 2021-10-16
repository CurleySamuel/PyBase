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
from struct import unpack
from time import sleep

from kazoo.client import KazooClient
from kazoo.exceptions import NoNodeError
from kazoo.handlers.threading import KazooTimeoutError

from ..exceptions import (ZookeeperConnectionException,
                          ZookeeperResponseException, ZookeeperZNodeException)
from ..pb.ZooKeeper_pb2 import MetaRegionServer

logger = logging.getLogger(__name__)

znode = "/hbase"


def connect(zkquorum, establish_connection_timeout=5):
    zk = KazooClient(hosts=zkquorum)

    try:
        zk.start(timeout=establish_connection_timeout)
    except KazooTimeoutError:
        raise ZookeeperConnectionException("Cannot connect to ZooKeeper at {}".format(zkquorum))

    return zk


def _parse_master_info(resp):
    if len(resp) == 0:
        # Empty response is bad.
        raise ZookeeperResponseException("ZooKeeper returned an empty response")
    # The first byte must be \xff and the next four bytes are a little-endian
    # uint32 containing the length of the meta.
    first_byte, meta_length = unpack(">cI", resp[:5])
    if first_byte != b'\xff':
        # Malformed response
        raise ZookeeperResponseException("ZooKeeper returned an invalid response")
    if meta_length < 1 or meta_length > 65000:
        # Is this really an error?
        raise ZookeeperResponseException("ZooKeeper returned too much meta information")
    # ZNode data in HBase are serialized protobufs with a four byte magic
    # 'PBUF' prefix.
    magic = unpack(">I", resp[meta_length + 5:meta_length + 9])[0]
    if magic != 1346524486:
        # 4 bytes: PBUF
        raise ZookeeperResponseException("ZooKeeper returned an invalid response (are you running "
                                         "a version of HBase supporting Protobufs?)")
    rsp = resp[meta_length + 9:]
    meta = MetaRegionServer()
    meta.ParseFromString(rsp)
    logger.info('Discovered Master at %s:%s', meta.server.host_name, meta.server.port)
    return meta.server.host_name, meta.server.port


def get_master_info(zk, watch_fn, missing_znode_retries=5):
    def _wrapped_watch(resp, stat):
        watch_fn(*_parse_master_info(resp))

    try:
        resp, _ = zk.get(znode + "/meta-region-server", watch=_wrapped_watch)

        return _parse_master_info(resp)
    except NoNodeError:
        if missing_znode_retries == 0:
            raise ZookeeperZNodeException(
                "ZooKeeper does not contain meta-region-server node.")
        logger.warn("ZooKeeper does not contain meta-region-server node. Retrying in 2 seconds. "
                    "(%s retries remaining)", missing_znode_retries)
        sleep(2.0)
        return get_master_info(zk, missing_znode_retries - 1)

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
import socket
from io import BytesIO
from struct import pack, unpack
from threading import Condition, Lock

from ..exceptions import (NoSuchColumnFamilyException, NotServingRegionException, PyBaseException,
                          RegionMovedException, RegionOpeningException, RegionServerException)
from ..helpers import varint
from ..pb.Client_pb2 import GetResponse, MutateResponse, ScanResponse
from ..pb.RPC_pb2 import ConnectionHeader, RequestHeader, ResponseHeader

logger = logging.getLogger(__name__)

# Used to encode and decode varints in a format protobuf expects.
encoder = varint.encodeVarint
decoder = varint.decodeVarint

# We need to know how to interpret an incoming proto.Message. This maps
# the request_type to the response_type.
response_types = {
    b"Get": GetResponse,
    b"Mutate": MutateResponse,
    b"Scan": ScanResponse
}


# This Client is created once per RegionServer. Handles all communication
# to and from this specific RegionServer.
class Client(object):
    # Variables are as follows:
    #   - Host: The hostname of the RegionServer
    #   - Port: The port of the RegionServer
    #   - Sock: An open connection to the RegionServer
    #   - call_id: A monotonically increasing int used as a sequence number for rpcs. This way
    #   we can match incoming responses with the rpc that made the request.

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.pool_size = 0
        # We support connection pools so have lists of sockets and read/write
        # mutexes on them.
        self.sock_pool = []
        self.write_lock_pool = []
        self.read_lock_pool = []
        # Why yes, we do have a mutex protecting a single variable.
        self.call_lock = Lock()
        self.call_id = 0
        # This dictionary and associated sync primitives are for when _receive_rpc
        # receives an RPC that isn't theirs. If a thread gets one that isn't
        # theirs it means there's another thread who also just sent an RPC. The
        # other thread will also get the wrong call_id. So how do we make them
        # switch RPCs?
        #
        # Receive an RPC with incorrect call_id?
        #       1. Acquire lock
        #       2. Place raw data into missed_rpcs with key call_id
        #       3. Notify all other threads to wake up (nothing will happen until you release the
        #          lock)
        #       4. WHILE: Your call_id is not in the dictionary
        #               4.5  Call wait() on the conditional and get comfy.
        #       5. Pop your data out
        #       6. Release the lock
        self.missed_rpcs = {}
        self.missed_rpcs_lock = Lock()
        self.missed_rpcs_condition = Condition(self.missed_rpcs_lock)
        # Set to true when .close is called - this allows threads/greenlets
        # stuck in _bad_call_id to escape into the error handling code.
        self.shutting_down = False
        # We would like the region client to keep track of the regions that it
        # hosts. That way if we detect a Region server issue when touching one
        # region, we can close them all at the same time (saving us a significant
        # amount of meta lookups).
        self.regions = []

    # Sends an RPC over the wire then calls _receive_rpc and returns the
    # response RPC.
    #
    # The raw bytes we send over the wire are composed (in order) -
    #
    #   1. little-endian uint32 representing the total-length of the following message.
    #   2. A single byte representing the length of the serialized RequestHeader.
    #   3. The serialized RequestHeader.
    #   4. A varint representing the length of the serialized RPC.
    #   5. The serialized RPC.
    #
    def _send_request(self, rq):
        with self.call_lock:
            my_id = self.call_id
            self.call_id += 1
        serialized_rpc = rq.pb.SerializeToString()
        header = RequestHeader()
        header.call_id = my_id
        header.method_name = rq.type
        header.request_param = True
        serialized_header = header.SerializeToString()
        # Consult the DESIGN.md for an explanation as to how Send/Receive
        # messages are composed.
        rpc_length_bytes = _to_varint(len(serialized_rpc))
        total_length = 4 + 1 + \
            len(serialized_header) + \
            len(rpc_length_bytes) + len(serialized_rpc)
        # Total length doesn't include the initial 4 bytes (for the
        # total_length uint32)
        to_send = pack(">IB", total_length - 4, len(serialized_header))
        to_send += serialized_header + rpc_length_bytes + serialized_rpc

        pool_id = my_id % self.pool_size
        try:
            with self.write_lock_pool[pool_id]:
                logger.debug('Sending %s RPC to %s:%s on pool port %s',
                             rq.type, self.host, self.port, pool_id)
                self.sock_pool[pool_id].send(to_send)
        except socket.error:
            # RegionServer dead?
            raise RegionServerException(region_client=self)
        # Message is sent! Now go listen for the results.
        return self._receive_rpc(my_id, rq)

    # Called after sending an RPC, listens for the response and builds the
    # correct pbResponse object.
    #
    # The raw bytes we receive are composed (in order) -
    #
    #   1. little-endian uint32 representing the total-length of the following message.
    #   2. A varint representing the length of the serialized ResponseHeader.
    #   3. The serialized ResponseHeader.
    #   4. A varint representing the length of the serialized ResponseMessage.
    #   5. The ResponseMessage.
    #
    def _receive_rpc(self, call_id, rq, data=None):
        # If the field data is populated that means we should process from that
        # instead of the socket.
        full_data = data
        if data is None:
            pool_id = call_id % self.pool_size
            # Total message length is going to be the first four bytes
            # (little-endian uint32)
            with self.read_lock_pool[pool_id]:
                try:
                    msg_length = self._recv_n(self.sock_pool[pool_id], 4)
                    if msg_length is None:
                        raise
                    msg_length = unpack(">I", msg_length)[0]
                    # The message is then going to be however many bytes the first four
                    # bytes specified. We don't want to overread or underread as that'll
                    # cause havoc.
                    full_data = self._recv_n(
                        self.sock_pool[pool_id], msg_length)
                except socket.error:
                    raise RegionServerException(region_client=self)
        # Pass in the full data as well as your current position to the
        # decoder. It'll then return two variables:
        #       - next_pos: The number of bytes of data specified by the varint
        #       - pos: The starting location of the data to read.
        next_pos, pos = decoder(full_data, 0)
        header = ResponseHeader()
        header.ParseFromString(full_data[pos: pos + next_pos])
        pos += next_pos
        if header.call_id != call_id:
            # call_ids don't match? Looks like a different thread nabbed our
            # response.
            return self._bad_call_id(call_id, rq, header.call_id, full_data)
        elif header.exception.exception_class_name != '':
            # If we're in here it means a remote exception has happened.
            exception_class = header.exception.exception_class_name
            if exception_class in \
                    {'org.apache.hadoop.hbase.regionserver.NoSuchColumnFamilyException',
                     "java.io.IOException"}:
                raise NoSuchColumnFamilyException()
            elif exception_class == 'org.apache.hadoop.hbase.exceptions.RegionMovedException':
                raise RegionMovedException()
            elif exception_class == 'org.apache.hadoop.hbase.NotServingRegionException':
                raise NotServingRegionException()
            elif exception_class == \
                    'org.apache.hadoop.hbase.regionserver.RegionServerStoppedException':
                raise RegionServerException(region_client=self)
            elif exception_class == 'org.apache.hadoop.hbase.exceptions.RegionOpeningException':
                raise RegionOpeningException()
            else:
                raise PyBaseException(
                    exception_class + ". Remote traceback:\n%s" % header.exception.stack_trace)
        next_pos, pos = decoder(full_data, pos)
        rpc = response_types[rq.type]()
        rpc.ParseFromString(full_data[pos: pos + next_pos])
        # The rpc is fully built!
        return rpc

    # Receive an RPC with incorrect call_id?
    #       1. Acquire lock
    #       2. Place raw data into missed_rpcs with key call_id
    #       3. Notify all other threads to wake up (nothing will happen until you release the lock)
    #       4. WHILE: Your call_id is not in the dictionary
    #               4.5  Call wait() on the conditional and get comfy.
    #       5. Pop your data out
    #       6. Release the lock
    def _bad_call_id(self, my_id, my_request, msg_id, data):
        with self.missed_rpcs_lock:
            logger.debug(
                "Received invalid RPC ID. Got: %s, Expected: %s.", msg_id, my_id)
            self.missed_rpcs[msg_id] = data
            self.missed_rpcs_condition.notifyAll()
            while my_id not in self.missed_rpcs:
                if self.shutting_down:
                    raise RegionServerException(region_client=self)
                self.missed_rpcs_condition.wait()
            new_data = self.missed_rpcs.pop(my_id)
            logger.debug("Another thread found my RPC! RPC ID: %s", my_id)
        return self._receive_rpc(my_id, my_request, data=new_data)

    # Receives exactly n bytes from the socket. Will block until n bytes are
    # received. If a socket is closed (RegionServer died) then raise an
    # exception that goes all the way back to the main client
    def _recv_n(self, sock, n):
        partial_str = BytesIO()
        partial_len = 0
        while partial_len < n:
            packet = sock.recv(n - partial_len)
            if not packet:
                raise socket.error()
            partial_len += len(packet)
            partial_str.write(packet)
        return partial_str.getvalue()

    # Do any work to close open file descriptors, etc.
    def close(self):
        self.shutting_down = True
        for sock in self.sock_pool:
            sock.close()
        # We could still have greenlets waiting in the bad_call_id pools! Wake
        # them up so they can fail to error handling as well.
        self.missed_rpcs_condition.acquire()
        self.missed_rpcs_condition.notifyAll()
        self.missed_rpcs_condition.release()


# Creates a new RegionServer client. Creates the socket, initializes the
# connection and returns an instance of Client.
def NewClient(host, port, pool_size):
    c = Client(host, port)
    try:
        c.pool_size = pool_size
        for x in range(pool_size):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, int(port)))
            _send_hello(s)
            s.settimeout(2)
            c.sock_pool.append(s)
            c.read_lock_pool.append(Lock())
            c.write_lock_pool.append(Lock())
    except (socket.error, socket.timeout):
        return None
    return c


# Given an open socket, sends a ConnectionHeader over the wire to
# initialize the connection.
def _send_hello(sock):
    ch = ConnectionHeader()
    ch.user_info.effective_user = "pybase"
    ch.service_name = "ClientService"
    serialized = ch.SerializeToString()
    # Message is serialized as follows -
    #   1. "HBas\x00\x50". Magic prefix that HBase requires.
    #   2. Little-endian uint32 indicating length of serialized ConnectionHeader
    #   3. Serialized ConnectionHeader
    message = b"HBas\x00\x50" + pack(">I", len(serialized)) + serialized
    sock.send(message)


# Little helper function that will return a byte-string representing the
# val encoded as a varint
def _to_varint(val):
    temp = []
    encoder(temp.append, val)
    return b"".join(temp)

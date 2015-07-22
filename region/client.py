import socket
from struct import pack, unpack
from pb.RPC_pb2 import ConnectionHeader, RequestHeader, ResponseHeader
from pb.Client_pb2 import GetResponse, MutateResponse, ScanResponse
from helpers import varint
import logging
logger = logging.getLogger('pybase.' + __name__)
logger.setLevel(logging.DEBUG)


# Used to encode and decode varints in a format protobuf expects.
encoder = varint.encodeVarint
decoder = varint.decodeVarint

# We need to know how to interpret an incoming proto.Message. This maps
# the request_type to the response_type.
response_types = {
    "Get": GetResponse,
    "Mutate": MutateResponse,
    "Scan": ScanResponse
}

# This Client is created once per RegionServer. Handles all communication
# to and from this specific RegionServer.


class Client:
    # Variables are as follows:
    #   - Host: The hostname of the RegionServer
    #   - Port: The port of the RegionServer
    #   - Sock: An open connection to the RegionServer
    #   - call_id: A monotonically increasing int used as a sequence number for rpcs. This way
    #   we can match incoming responses with the rpc that made the request.

    def __init__(self, host, port, sock):
        self.host = host
        self.port = port
        self.sock = sock
        self.call_id = 0

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
    def _send_rpc(self, rpc, request_type):
        logger.info(
            'Sending %s RPC to %s:%s', request_type, self.host, self.port)
        # Serialize the RPC
        serialized_rpc = rpc.SerializeToString()

        header = RequestHeader()
        header.call_id = self.call_id
        header.method_name = request_type
        header.request_param = True
        serialized_header = header.SerializeToString()

        rpc_length_bytes = _to_varint(len(serialized_rpc))
        total_length = 4 + 1 + \
            len(serialized_header) + \
            len(rpc_length_bytes) + len(serialized_rpc)
        # Total length doesn't include the initial 4 bytes (for the
        # total_length uint32)
        to_send = pack(">IB", total_length - 4, len(serialized_header))
        to_send += serialized_header + rpc_length_bytes + serialized_rpc

        self.call_id += 1
        self.sock.send(to_send)
        # Message is sent! Now go listen for the results.
        return self._receive_rpc(self.call_id - 1, request_type)

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
    def _receive_rpc(self, call_id, request_type):
        # Total message length is going to be the first four bytes
        # (little-endian uint32)
        msg_length = self._recv_n(4)
        if msg_length is None:
            return 1 / 0  # TODO
        msg_length = unpack(">I", msg_length)[0]
        # The message is then going to be however many bytes the first four
        # bytes specified. We don't want to overread or underread as that'll
        # cause havoc.
        full_data = self._recv_n(msg_length)
        # Pass in the full data as well as your current position to the
        # decoder. It'll then return two variables:
        #       - next_pos: The number of bytes of data specified by the varint
        #       - pos: The starting location of the data to read.
        next_pos, pos = decoder(full_data, 0)
        header = ResponseHeader()
        header.ParseFromString(full_data[pos: pos + next_pos])
        pos += next_pos
        if header.call_id != call_id:
            # call_ids don't match? Something's wrong.
            return 1 / 0  # TODO
        elif header.exception.exception_class_name != u'':
            # Any remote exceptions will be specified here.
            return 1 / 0  # TODO
        next_pos, pos = decoder(full_data, pos)
        rpc = response_types[request_type]()
        rpc.ParseFromString(full_data[pos: pos + next_pos])
        # The rpc is fully built!
        return rpc

    # Receives exactly n bytes from the socket. Will block until n bytes are
    # received.
    def _recv_n(self, n):
        data = ''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data


# Creates a new RegionServer client. Creates the socket, initializes the
# connection and returns an instance of Client.
def NewClient(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    _send_hello(s)
    return Client(host, port, s)


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
    message = "HBas\x00\x50" + pack(">I", len(serialized)) + serialized
    sock.send(message)


# Little helper function that will return a byte-string representing the
# val encoded as a varint
def _to_varint(val):
    temp = []
    encoder(temp.append, val)
    return "".join(temp)


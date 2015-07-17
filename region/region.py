import socket
from struct import pack, unpack
from pb.RPC_pb2 import ConnectionHeader, RequestHeader
from pb.HBase_pb2 import RegionInfo
from pb.Client_pb2 import GetRequest, Column

metaTableName = "hbase:meta,,1"
metaInfoFamily = {"info": []}


class Client:

    def __init__(self, host, port, sock):
        self.host = host
        self.port = port
        self.sock = sock
        self.call_id = 0

    def _send_rpc(self, rpc, request_type):
        serialized_rpc = rpc.SerializeToString()
        header = RequestHeader()
        header.call_id = self.call_id
        header.method_name = request_type
        header.request_param = True
        serialized_header = header.SerializeToString()

        rpc_length_bytes = _encode_varint(len(serialized_rpc))
        total_length = 4 + 1 + \
            len(serialized_header) + \
            len(rpc_length_bytes) + len(serialized_rpc)
        to_send = pack(">IB", total_length - 4, len(serialized_header))
        to_send += serialized_header + rpc_length_bytes + serialized_rpc

        self.sock.send(to_send)
        print self.sock.recv(4096)
        self.call_id += 1

    def _find_region_by_key(self, table, key):
        meta_key = self._construct_meta_key(table, key)
        region = self._find_region_by_meta_key(meta_key)
        return region

    def _construct_meta_key(self, table, key):
        return table + "," + key + ",:"

    def _find_region_by_meta_key(self, key):
        rq = GetRequest()
        rq.get.row = key
        rq.get.column.extend(_families_to_columns(metaInfoFamily))
        rq.get.closest_row_before = True
        rq.region.type = 1
        rq.region.value = metaTableName
        rsp = self._send_rpc(rq, "Get")


def NewClient(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    _send_hello(s)
    return Client(host, port, s)


def _send_hello(sock):
    ch = ConnectionHeader()
    ch.user_info.effective_user = "pybase"
    ch.service_name = "ClientService"
    serialized = ch.SerializeToString()
    message = "HBas\x00\x50" + pack(">I", len(serialized)) + serialized
    sock.send(message)


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


# varint functions were pulled from the below URL. Don't put too much faith in them.
# https://github.com/remoun/python-protobuf/blob/master/google/protobuf/internal/encoder.py
def _encode_varint(value):
    pieces = []
    write = pieces.append
    bits = value & 0x7f
    value >>= 7
    while value:
        write(chr(0x80 | bits))
        bits = value & 0x7f
        value >>= 7
    write(chr(bits))
    return "".join(pieces)


# I made some personal modifications to _decode_varint. It seems to work
# but may fail with edge-case testing
def _decode_varint(value):
    pos = 0
    result = 0
    shift = 0
    while 1:
        b = ord(value[pos])
        result |= ((b & 0x7f) << shift)
        pos += 1
        if not (b & 0x80):
            return result
        shift += 7
        if shift >= 64:
            raise ValueError("Too many bytes while decoding")


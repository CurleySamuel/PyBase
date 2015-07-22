import socket
from struct import pack, unpack
from pb.RPC_pb2 import ConnectionHeader, RequestHeader, ResponseHeader
from pb.HBase_pb2 import RegionInfo
from pb.Client_pb2 import GetRequest, Column, GetResponse, MutateResponse, ScanResponse
from helpers import varint

metaTableName = "hbase:meta,,1"
metaInfoFamily = {"info": []}
encoder = varint.encodeVarint
decoder = varint.decodeVarint

response_types = {
    "Get": GetResponse,
    "Mutate": MutateResponse,
    "Scan": ScanResponse
}


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

        rpc_length_bytes = _to_varint(len(serialized_rpc))
        total_length = 4 + 1 + \
            len(serialized_header) + \
            len(rpc_length_bytes) + len(serialized_rpc)
        to_send = pack(">IB", total_length - 4, len(serialized_header))
        to_send += serialized_header + rpc_length_bytes + serialized_rpc

        self.call_id += 1
        self.sock.send(to_send)
        return self._receive_rpc(self.call_id - 1, request_type)

    def _receive_rpc(self, call_id, request_type):
        msg_length = self._recv_n(4)
        if msg_length is None:
            return 1 / 0  # TODO
        msg_length = unpack(">I", msg_length)[0]
        full_data = self._recv_n(msg_length)
        next_pos, pos = decoder(full_data, 0)
        header = ResponseHeader()
        header.ParseFromString(full_data[pos: pos + next_pos])
        pos += next_pos
        if header.call_id != call_id:
            return 1 / 0  # TODO
        elif header.exception.exception_class_name != u'':
            return 1 / 0  # TODO
        next_pos, pos = decoder(full_data, pos)
        rpc = response_types[request_type]()
        rpc.ParseFromString(full_data[pos: pos + next_pos])
        return rpc

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

    def _recv_n(self, n):
        data = ''
        while len(data) < n:
            packet = self.sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data


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


#  Converts a dictionary specifying ColumnFamilys -> Qualifiers into the protobuf type.
#
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


def _to_varint(val):
    temp = []
    encoder(temp.append, val)
    return "".join(temp)


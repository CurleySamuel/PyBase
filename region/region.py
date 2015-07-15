import socket
from struct import pack
from pb.RPC_pb2 import ConnectionHeader, RequestHeader
from pb.HBase_pb2 import RegionInfo
from pb.Client_pb2 import GetRequest


metaTableName = "hbase:meta"


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

        rpc_length = len(serialized_rpc)
        total_length = rpc_length + len(serialized_header) + 1 + 4 + 4
        to_send = pack(">Ib", total_length - 4, len(serialized_header)
                       ) + serialized_header + pack(">I", rpc_length) + serialized_rpc

        self.sock.send(to_send)
        import ipdb
        ipdb.set_trace()
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




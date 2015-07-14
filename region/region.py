import socket
from struct import pack, unpack
from pb.RPC_pb2 import ConnectionHeader, UserInformation

class Client:
    def __init__(self, host, port, sock):
        s.host = host
        s.port = port
        s.sock = sock


def NewClient(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    _send_hello(s)
    return


def _send_hello(sock):
    ch = ConnectionHeader()
    ch.user_info.effective_user = "pybase"
    ch.service_name = "ClientService"
    serialized = ch.SerializeToString()
    message = "HBas\x00\x50" + pack(">I", len(serialized)) + serialized
    sock.send(message)

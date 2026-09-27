import socket

from enocean.protocol.packet import Packet


def send_to_tcp_socket(host: str, port: int, packet: Packet) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(bytearray(packet.build()))
    sock.close()

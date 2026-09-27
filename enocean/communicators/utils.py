import socket


def send_to_tcp_socket(host, port, packet):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    sock.sendall(bytearray(packet.build()))
    sock.close()

# Echo client program
import socket


HOST = 'localhost'        # The remote host
PORT = 8080                 # The same port as used by the server
MSGLEN = 12

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    msg = b'Hello world!'
    assert len(msg) == MSGLEN
    totalsent = 0
    while totalsent < MSGLEN:
        sent = s.send(msg[totalsent:])
        if sent == 0:
            raise RuntimeError("socket connection broken")
        totalsent = totalsent + sent
    chunks = []
    bytes_recd = 0
    while bytes_recd < MSGLEN:
        chunk = s.recv(min(MSGLEN - bytes_recd, 6))
        if chunk == b'':
            raise RuntimeError("socket connection broken")
        chunks.append(chunk)
        bytes_recd = bytes_recd + len(chunk)
    data = b''.join(chunks)
print('Received', repr(data))

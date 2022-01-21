import socket
import logging
import threading
from optparse import OptionParser


class MyServer:

    def __init__(self, host: str, port: int, max_workers: int = 3):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.num_workers = max_workers
        self.server_socket.bind((self.host, self.port))
        self.__shutdown_request = False

    def send_answer(self, data, client_socket):
        totalsent = 0
        while totalsent < len(data):
            sent = client_socket.send(data[totalsent:])
            if sent == 0:
                raise RuntimeError('socket connection broken')
            totalsent = totalsent + sent

    def handle_client_connection(self, client_socket, maxlen=1024):
        request = client_socket.recv(maxlen)
        logging.info('Received {}'.format(request))
        self.send_answer(b'ACK!\r\n', client_socket)

    def serve_forever(self):
        logging.info('Listening at {}:{}...'.format(self.host, self.port))
        self.server_socket.listen(5)
        while not self.__shutdown_request:
            client_socket, addr = self.server_socket.accept()
            logging.info('Connected by %r' % repr(addr))
            client_handler = threading.Thread(
                target=self.handle_client_connection,
                args=(client_socket,)
            )
            client_handler.start()

    def close(self):
        self.__shutdown_request = True
        self.server_socket.close()


if __name__ == '__main__':
    op = OptionParser()
    # op.add_option("-h", "--host", action="store", type=str, default="")
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log, level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S'
    )
    server = MyServer(host='localhost', port=opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.close()

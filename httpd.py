import socket
import logging
import threading
import uuid
from queue import Queue
from optparse import OptionParser


class Worker(threading.Thread):
    """
    Consumes task from queue.
    """
    def __init__(self, queue, handler, _id=str(uuid.uuid4())[:4]):
        threading.Thread.__init__(self)
        self.queue = queue
        self.handler = handler
        self.__id = _id
        self.__shutdown_request = False
        logging.info('Worker {} inited'.format(self.__id))

    def run(self):
        logging.info('Worker {} started'.format(self.__id))
        while not self.__shutdown_request:
            client_socket, addr = self.queue.get()
            if client_socket is None and addr is None:
                break
            logging.info('Worker {} manages request from {}'.format(
                self.__id, addr))
            try:
                self.handler(client_socket)
            except Exception as exc:
                logging.error(
                    'Worker {} cannot handle {}. Error: {}'.format(
                        self.__id, addr, exc))
            else:
                logging.info('Worker {} finished with {}'.format(
                    self.__id, addr))
            finally:
                logging.info('Closing socket...')
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
                self.queue.task_done()
                logging.info('Task done')


class MyServer:

    def __init__(self, host: str, port: int, max_workers: int = 10,
                 timeout: float = 5.0):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.max_workers = max_workers
        self.timeout = timeout
        self.server_socket.bind((self.host, self.port))
        self.__shutdown_request = False
        self.queue = Queue()
        self.worker_pool = []
        assert self.init_workers(), (
            f'Not all the workers inited '
            f'({len(self.worker_pool)} of {self.max_workers})'
        )

    def init_workers(self):
        for number in range(self.max_workers):
            self.worker_pool.append(
                Worker(self.queue, self.handle_client_connection,
                       _id=(number + 1))
            )
        return len(self.worker_pool) == self.max_workers

    def start_workers(self):
        [worker.start() for worker in self.worker_pool]

    def stop_workers(self):
        logging.info('Killing workers...')
        for worker in self.worker_pool:
            self.queue.put((None, None))
            worker.__shutdown_request = True
            worker.join(timeout=0.5)

    @staticmethod
    def send_answer(data, client_socket):
        client_socket.sendall(data)
        logging.info('Send {} to {}'.format(data, client_socket))

    @staticmethod
    def handle_client_connection(client_socket, chunklen=1024):
        logging.info('Handling request')
        fragments = []
        while True:
            chunk = client_socket.recv(chunklen)
            logging.info('Got a chunk: {}'.format(chunk))
            if not chunk:
                logging.info('Breaking (zero chunk)')
                break
            if chunk.decode('utf-8').endswith('\r\n\r\n'):
                fragments.append(chunk.decode('utf-8'))
                break
            fragments.append(chunk.decode('utf-8'))
        request = ''.join(fragments)
        logging.info('Received {}'.format(request))
        MyServer.send_answer(b'ACK!\r\n', client_socket)

    def serve_forever(self):
        logging.info('Starting workers...')
        self.start_workers()
        logging.info('Listening at {}:{}...'.format(self.host, self.port))
        self.server_socket.listen(5)
        while not self.__shutdown_request:
            client_socket, addr = self.server_socket.accept()
            logging.info('Connected by %r' % repr(addr))
            client_socket.settimeout(self.timeout)
            self.queue.put((client_socket, addr))

    def close(self):
        logging.info('Got a shutdown request...')
        self.__shutdown_request = True
        self.server_socket.close()
        self.stop_workers()


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

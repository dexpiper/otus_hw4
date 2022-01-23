import socket
import logging
import threading
from typing import NamedTuple
import uuid
import os
from datetime import datetime
from pathlib import Path
from queue import Queue
from optparse import OptionParser
from collections import namedtuple


class HTTPhelper:
    OK = 200
    FORBIDDEN = 403
    NOT_FOUND = 404
    NOT_ALLOWED = 405
    codes = {200: 'OK', 403: 'FORBIDDEN', 404: 'NOT FOUND', 405: 'NOT ALLOWED'}
    version = 'HTTP/1.0'
    servername = 'OTUServer by AlexK'
    headers = ['Date', 'Server', 'Content-Length', 'Content-Type',
               'Connection']
    methods = ['GET', 'HEAD']
    content_types = {
        '.html': 'text/html',
        '.css': 'text/css',
        '.js': 'text/javascript',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.swf': 'application/x-shockwave-flash',
        'default': 'text/plain'
    }
    request = namedtuple('Request', ['method', 'address', 'version'])

    @staticmethod
    def make_heads(**kwargs) -> str:
        """
        kwargs expected:
        * length - len(<content>)
        * type - Path('file.suff').suffix()
        """
        dct = {h: '' for h in HTTPhelper.headers}
        dct['Date'] = HTTPhelper.httpdate()
        dct['Server'] = HTTPhelper.servername
        dct['Content-Length'] = kwargs.get('length', '')
        dct['Content-Type'] = HTTPhelper.content_types[
            kwargs.get('type', 'default')
        ]
        dct['Connection'] = 'close'
        return '\r\n'.join([f'{h}: {v}' for h, v in dct.items() if v])

    @staticmethod
    def make_answer(code, file=None, head=False):
        lead = f'{HTTPhelper.version} {code} {HTTPhelper.codes[code]}'
        if not code == 200:
            return bytes(lead.encode('utf-8'))
        if file:
            suffix = file.suffix()
            length = os.path.getsize(file)
            with open(file, 'rb') as f:
                bytes_read = f.read()
        heads = HTTPhelper.make_heads()

    @staticmethod
    def get_request(arg: str) -> NamedTuple:
        splitted_first_string = arg.split('\r\n')[0].split()
        method = splitted_first_string[0]
        address = splitted_first_string[1]
        version = splitted_first_string[2]
        return HTTPhelper.request(method, address, version)

    @staticmethod
    def httpdate(dt: datetime = datetime.now()) -> str:
        """
        Return a string representation of a date according to RFC 1123
        (HTTP/1.1)
        """
        weekday = ["Mon", "Tue", "Wed", "Thu",
                   "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul",
                 "Aug", "Sep", "Oct", "Nov", "Dec"][dt.month - 1]
        string = "%s, %02d %s %04d %02d:%02d:%02d GMT" % (
            weekday, dt.day, month,
            dt.year, dt.hour, dt.minute, dt.second
        )
        return string


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
                self.queue.task_done()
                logging.info('Task done')


class MyServer:

    def __init__(self, host: str, port: int, max_workers: int = 3,
                 timeout: float = 5.0, basedir: str = '.'):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.max_workers = max_workers
        self.timeout = timeout
        self.basedir = Path(basedir)
        if not self.basedir.is_dir():
            raise LookupError(f'{basedir} is not a directory')
        self.server_socket.bind((self.host, self.port))
        self.__shutdown_request = False
        self.queue = Queue()
        self.worker_pool = []
        self.init_workers()

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
    def handle_client_connection(client_socket, chunklen=2048):
        logging.info('Handling request')
        data = client_socket.recv(chunklen)
        logging.info('Received {}'.format(data.decode('utf-8')))
        MyServer.send_answer(
            b'HTTP/1.0 200 OK\r\nContent-type: text/html\r\n'
            b'Content-length: 3\r\n\nOK!', client_socket)
        client_socket.close()

    def serve_forever(self):
        logging.info('Starting workers...')
        self.start_workers()
        logging.info('Listening at {}:{}...'.format(self.host, self.port))
        logging.info('Serving files from: {}'.format(self.basedir.absolute()))
        self.server_socket.listen(5)
        while not self.__shutdown_request:
            client_socket, addr = self.server_socket.accept()
            logging.info('Connected by {}'.format(repr(addr)))
            client_socket.settimeout(self.timeout)
            self.queue.put((client_socket, addr))

    def close(self):
        logging.info('Got a shutdown request...')
        self.__shutdown_request = True
        self.server_socket.close()
        self.stop_workers()


if __name__ == '__main__':
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-r", "--root", action="store", type='string', default='.')
    op.add_option("-w", "--workers", action="store", type=int, default=3)
    op.add_option("-t", "--timeout", action="store", type=float, default=3.0)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log, level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S'
    )
    server = MyServer(host=args[0] if len(args) else '', port=opts.port,
                      max_workers=opts.workers,
                      timeout=opts.timeout, basedir=opts.root)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.close()

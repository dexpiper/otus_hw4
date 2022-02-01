import logging
import mimetypes
import os
import socket
import threading
import uuid
from collections import namedtuple
from datetime import datetime
from http import HTTPStatus
from optparse import OptionParser
from pathlib import Path
from queue import Queue
from typing import NamedTuple
from urllib.parse import unquote


class HTTPhelper:
    version = 'HTTP/1.0'
    servername = 'OTUServer by AlexK'
    headers = ['Date', 'Server', 'Content-Length', 'Content-Type',
               'Connection']
    request = namedtuple(
        'Request', ['method', 'address', 'version', 'query_string'],
        defaults=(None,))


def make_heads(**kwargs) -> str:
    """
    kwargs expected:
    * length - len(<content>)
    * type - Path('file.suff').suffix()
    """
    dct = {h: '' for h in HTTPhelper.headers}
    dct['Date'] = httpdate()
    dct['Server'] = HTTPhelper.servername
    dct['Content-Length'] = kwargs.get('length', '')
    file = kwargs.get('file')
    if file:
        dct['Content-Type'] = mimetypes.guess_type(
            kwargs.get('file'))[0] or 'text/plain'
    dct['Connection'] = 'close'
    result_string = '\r\n'.join([f'{h}: {v}' for h, v in dct.items() if v])
    result_string += '\r\n'
    return bytes(result_string.encode('utf-8'))


def make_answer(code: HTTPStatus, file: Path or None = None,
                method: str or None = None) -> bytes:
    """
    Cook HTTP-answer with provided args.
    """
    string = f'{HTTPhelper.version} {code.value} {code.phrase}'
    lead = bytes(string.encode('utf-8'))
    if not code == 200 or not file:
        headers = make_heads()
        return b'\r\n'.join((lead, headers))
    length = os.path.getsize(file)
    headers = make_heads(length=length, file=file)
    if method == 'GET':
        with open(file, 'rb') as f:
            bytes_read = f.read()
        return b'\r\n'.join((lead, headers, bytes_read))
    elif method == 'HEAD':  # only headers without content
        headers += b'\r\n'
        return b'\r\n'.join((lead, headers))


def get_request(arg: str) -> NamedTuple or None:
    splitted_first_string = arg.split('\r\n')[0].split()
    if len(splitted_first_string) != 3:
        raise ValueError('Bad request')
    method = splitted_first_string[0]
    if method not in ('GET', 'HEAD'):
        raise ValueError(f'Ansupported method {method}')
    address = unquote(splitted_first_string[1])
    version = splitted_first_string[2]
    if '?' in address:
        address, query_string = address.split('?')
        return HTTPhelper.request(method, address, version, query_string)
    return HTTPhelper.request(method, address, version)


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
        logging.info(f'Worker {self.__id} started')
        while not self.__shutdown_request:
            client_socket, addr = self.queue.get()
            if client_socket is None and addr is None:
                break
            logging.debug(f'Worker {self.__id} manages request from {addr}')
            try:
                self.handler(client_socket)
            except Exception as exc:
                logging.error(
                    f'Worker {self.__id} cannot handle {addr}. '
                    f'Error: {exc.with_traceback(exc.__traceback__)}'
                )
            else:
                logging.debug(f'Worker {self.__id} finished with {addr}')
            finally:
                try:
                    client_socket.close()
                except Exception:
                    pass
                self.queue.task_done()


class MyServer:

    def __init__(self, host: str, port: int, max_workers: int = 3,
                 timeout: float = 5.0, basedir: str = '.',
                 bind: bool = True, chunklen=24):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.max_workers = max_workers
        self.timeout = timeout
        self.basedir = Path(basedir)
        if not self.basedir.is_dir():
            raise FileNotFoundError(f'{basedir} is not a directory')
        self.__shutdown_request = False
        self.queue = Queue()
        self.worker_pool = []
        self.chunklen = chunklen
        self._bind = bind
        if bind:
            self.bind_server_socket()

    def bind_server_socket(self):
        try:
            self.server_socket.bind((self.host, self.port))
        except Exception:
            self.close()
            raise

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
        if len(data) > 70:
            data = data[:70]
        logging.debug(f'Send {data} to {client_socket}')

    def check_file_path(self, request, client_socket) -> Path or None:
        if request.address.endswith('/') and len(request.address) > 3:
            addr = request.address[1:-1]  # get rid of starting and ending /
            file = self.basedir / Path(addr) / Path('index.html')
        elif request.address == '/':
            file = self.basedir / Path('index.html')
        else:
            file = self.basedir / Path(request.address[1:])
        if self.basedir.resolve() not in file.resolve().parents:
            logging.info('Someone tried to escape basedir. Forbidden')
            MyServer.send_answer(
                make_answer(code=HTTPStatus.FORBIDDEN),
                client_socket
            )
            client_socket.close()
            return
        return file

    def get_and_check_request(self, data, client_socket) -> NamedTuple:
        try:
            request = get_request(data)
            return request
        except Exception as exc:
            logging.error(f'Bad request. Exc: {exc}')
            MyServer.send_answer(
                make_answer(code=HTTPStatus.METHOD_NOT_ALLOWED),
                client_socket
            )
            client_socket.close()

    def read_response(self, client_socket) -> str:
        buf = b''
        delim = b'\r\n\r\n'
        while True:
            r = client_socket.recv(self.chunklen)
            buf += r
            if delim in buf:
                buf = buf.split(delim)[0]
                break
            elif not r:
                raise socket.error('Server closed connection')
        logging.debug(f'Received {buf}')
        return buf.decode('utf-8')

    def handle_client_connection(self, client_socket):
        data = self.read_response(client_socket)
        request = self.get_and_check_request(data, client_socket)
        if not request:
            return
        file = self.check_file_path(request, client_socket)
        if not file:
            return
        if file.is_file():
            answer = make_answer(code=HTTPStatus.OK,
                                 file=file,
                                 method=request.method)
            logging.debug('Sending back valid answer')
            MyServer.send_answer(answer, client_socket)
        else:
            logging.info(f'No such file {repr(file)}')
            MyServer.send_answer(
                make_answer(code=HTTPStatus.NOT_FOUND),
                client_socket
            )
        client_socket.close()

    def serve_forever(self):
        if not self._bind:
            self.bind_server_socket()
        self.init_workers()
        logging.info('Starting workers...')
        self.start_workers()
        logging.info(f'Listening at {self.host}:{self.port}...')
        logging.info(f'Serving files from: {self.basedir.absolute()}')
        self.server_socket.listen(5)
        while not self.__shutdown_request:
            client_socket, addr = self.server_socket.accept()
            logging.info(f'Connected by {repr(addr)}')
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
    op.add_option("-v", "--level", action="store", type=int, default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(
        filename=opts.log, level=opts.level or logging.INFO,
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

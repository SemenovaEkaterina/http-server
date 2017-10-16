import socket
import os
import sys
import select
import configparser
from pathlib import Path

from handler import HttpHandler

config = configparser.ConfigParser()
if not Path("/etc/httpd.conf").is_file():
    config.read_file(open(r'./default.conf'))
else:
    config.read_file(open(r'/etc/httpd.conf'))

DOCUMENT_ROOT = config.get('server-config', 'document_root')
PORT = int(config.get('server-config', 'port'))
FILE_BLOCK_SIZE = int(config.get('server-config', 'file_block_size'))
CPU_COUNT = int(config.get('server-config', 'cpu_count'))
READ_CHUNK_SIZE = int(config.get('server-config', 'read_chunk_size'))
WRITE_CHUNK_SIZE = int(config.get('server-config', 'write_chunk_size'))

if len(sys.argv) > 1 and sys.argv[1] == 'dev':
    DOCUMENT_ROOT = './http-test-suite'


class Handler:
    def __init__(self):
        self.ready_to_read = True
        self.ready_to_write = False
        self.ready = False
        self.has_file = False

    def read(self):
        pass


class FileHandler(Handler):
    def __init__(self, file, connection):
        super().__init__()
        self.file = file
        self.conn = connection

    def read(self):
        buffer = os.read(self.file, FILE_BLOCK_SIZE)
        if buffer:
            return buffer
        else:
            self.ready_to_read = False
            self.ready = True
            return b''


class ConnectionHandler(Handler):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.data = b''
        self.out_data = b''
        self.httpHandler = HttpHandler()
        self.file_end = False

    def read_data(self):
        try:
            chunk = self.connection.recv(READ_CHUNK_SIZE)
            self.data += chunk
            if len(chunk) < READ_CHUNK_SIZE:
                self.data += chunk
                self.ready_to_read = False
                self.__handle()
        except:
            self.ready = True

    def __handle(self):
        self.out_data = self.httpHandler.parse_request(self.data, DOCUMENT_ROOT)
        self.ready_to_write = True

        if self.httpHandler.file is not None:
            self.has_file = True
            self.file = self.httpHandler.file
        else:
            self.file_end = True

    def write_data(self):
        try:
            sent = self.connection.send(self.out_data)
            if self.file_end and len(self.out_data) == sent:
                self.ready = True
                self.ready_to_write = False
            self.out_data = self.out_data[sent:]
        except (BrokenPipeError, ConnectionResetError):
            self.ready = True
            self.ready_to_write = False

    def add_data(self, data):
        self.out_data += data


class ListenHandler(Handler):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock


class Selector:
    def __init__(self, sock):
        self.sock = sock
        self.handlers_map = {}

    def register(self, fileno, handler):
        self.handlers_map[fileno] = handler

    def start(self):
        while True:
            ready_to_read = []
            ready_to_write = []
            for handler in list(self.handlers_map):
                if self.handlers_map[handler].ready_to_read:
                    ready_to_read.append(handler)
                if self.handlers_map[handler].ready_to_write:
                    ready_to_write.append(handler)
                if self.handlers_map[handler].has_file:
                    self.register(self.handlers_map[handler].file,
                                  FileHandler(self.handlers_map[handler].file, handler))
                    self.handlers_map[handler].has_file = False
                    ready_to_read.append(self.handlers_map[handler].file)

                if self.handlers_map[handler].ready:
                    if type(self.handlers_map[handler]) == FileHandler:
                        if self.handlers_map[handler].conn in self.handlers_map:
                            self.handlers_map[self.handlers_map[handler].conn].file_end = True
                        os.close(handler)
                    if type(self.handlers_map[handler]) == ConnectionHandler:
                        self.handlers_map[handler].connection.close()
                    del self.handlers_map[handler]

            try:
                r, w, e = select.select(ready_to_read, ready_to_write, self.handlers_map)
            except OSError:
                r, w, e = [], [], []

            for readable in r:
                if readable not in self.handlers_map:
                    continue
                if type(self.handlers_map[readable]) == ListenHandler:
                    try:
                        conn, addr = self.sock.accept()
                        conn.setblocking(0)
                        self.register(conn.fileno(), ConnectionHandler(conn))
                    except:
                        pass

                if type(self.handlers_map[readable]) == ConnectionHandler:
                    self.handlers_map[readable].read_data()

                if type(self.handlers_map[readable]) == FileHandler:
                    if self.handlers_map[readable].conn in self.handlers_map:
                        self.handlers_map[self.handlers_map[readable].conn].add_data(self.handlers_map[readable].read())
                    else:
                        self.handlers_map[readable].ready = True

            for writable in w:
                if writable not in self.handlers_map:
                    continue
                if type(self.handlers_map[writable]) == ConnectionHandler:
                    self.handlers_map[writable].write_data()


class Server:
    def __init__(self, port, document_root, cpu_count):
        self.port = port
        self.document_root = document_root
        self.cpu_count = cpu_count

    def start(self):
        print("Starting server on port {}, document root: {}".format(self.port, self.document_root))

        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind(("", self.port))
        sock.listen(1)

        selector = Selector(sock)

        for i in range(self.cpu_count-1):
            pid = os.fork()
            if pid == 0:
                break

        selector.register(sock.fileno(), ListenHandler(sock))

        selector.start()


server = Server(PORT, DOCUMENT_ROOT, CPU_COUNT)

server.start()

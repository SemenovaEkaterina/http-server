import socket

from handler import handle

config = {
    'DOCUMENT_ROOT': './http-test-suite'
}


class Server:
    def __init__(self):
        pass

    @staticmethod
    def start():
        print("running server")
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", 80))
        sock.listen(1)

        while True:
            conn, addr = sock.accept()
            data = conn.recv(2024)
            response = handle(data, config)

            conn.send(response)

            conn.close()


server = Server()

server.start()

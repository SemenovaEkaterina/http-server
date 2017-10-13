from enum import Enum
import fcntl

from request import Request
from response import Response, ResponseCode

import os


class ContentTypes(Enum):
    html = 'text/html'
    css = 'text/css'
    js = 'text/javascript'
    jpg = 'image/jpeg'
    jpeg = 'image/jpeg'
    png = 'image/png'
    swf = 'application/x-shockwave-flash'
    gif = 'image/gif'
    txt = 'text/txt'


class HttpHandler:
    def __init__(self):
        self.response = None
        self.file = None

    def parse_request(self, data, document_root):
        request = Request(data)

        if request.error:
            self.response = Response(ResponseCode.NOT_ALLOWED, request.protocol)

        else:
            self.protocol = request.protocol
            if request.url[-1:] == '/':
                file_url = request.url[1:] + 'index.html'
            else:
                file_url = request.url[1:]

            if len(file_url.split('../')) > 1:
                self.response = Response(ResponseCode.FORBIDDEN, request.protocol)
                self.file = None

            else:
                try:
                    self.file = os.open(os.path.join(document_root, file_url), os.O_RDONLY)
                    flag = fcntl.fcntl(self.file, fcntl.F_GETFL)
                    fcntl.fcntl(self.file, fcntl.F_SETFL, flag | os.O_NONBLOCK)
                except (FileNotFoundError, IsADirectoryError):
                    if (request.url[-1:]) == '/':
                        return Response(ResponseCode.FORBIDDEN, request.protocol).build()
                    else:
                        return Response(ResponseCode.NOT_FOUND, request.protocol).build()
                except OSError:
                    print(request.url)
                    return Response(ResponseCode.NOT_FOUND, request.protocol).build()
                try:
                    self.content_type = ContentTypes[file_url.split('.')[-1]].value
                except KeyError:
                    self.content_type = 'text/plain'

                self.content_length = os.path.getsize(os.path.join(document_root, file_url))

                self.response = Response(ResponseCode.OK, request.protocol, self.content_type, self.content_length)

                if request.method == 'HEAD':
                    self.file = None

        return self.response.build()
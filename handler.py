from enum import Enum

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


def handle(data, config):
    request = Request(data)

    if request.error:
        response = Response(ResponseCode.NOT_ALLOWED, request.protocol)

    else:
        try:
            if request.url[-1:] == '/':
                file_url = request.url[1:] + 'index.html'
            else:
                file_url = request.url[1:]

            f = open(os.path.join(config['DOCUMENT_ROOT'], file_url), 'rb')
            if len(file_url.split('../')) > 1:
                response = Response(ResponseCode.FORBIDDEN, request.protocol)

            else:
                try:
                    content_type = ContentTypes[file_url.split('.')[-1]].value
                except KeyError:
                    content_type = 'text/plain'

                content_length = os.path.getsize(os.path.join(config['DOCUMENT_ROOT'], file_url))
                if request.method == 'HEAD':
                    response = Response(ResponseCode.OK, request.protocol, content_type, content_length)
                else:
                    response = Response(ResponseCode.OK, request.protocol, content_type, content_length, f.read())
        except (FileNotFoundError, IsADirectoryError):
            if (request.url[-1:]) == '/':
                response = Response(ResponseCode.FORBIDDEN, request.protocol)
            else:
                response = Response(ResponseCode.NOT_FOUND, request.protocol)

    print(response.build()[1:50])
    return response.build()

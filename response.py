import datetime

from enum import Enum


class ResponseCode(Enum):
    OK = '200 OK'
    NOT_FOUND = '404 Not Found'
    NOT_ALLOWED = '405 Method Not Allowed'
    FORBIDDEN = '403 Forbidden'


class Response:
    def __init__(self, code, protocol, content_type=None, content_length=0, data=b''):
        self.code = code
        self.protocol = protocol
        self.data = data
        self.content_type = content_type
        self.content_length = content_length
        self.date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    def __success(self):
        return 'HTTP/{} {}\r\n' \
               'Content-Type: {}\r\n' \
               'Content-Length: {}\r\n'\
               'Date: {}\r\n' \
               'Server: Server\r\n\r\n'.format(self.protocol,
                                               self.code.value,
                                               self.content_type,
                                               self.content_length,
                                               self.date)

    def __not_found(self):
        return 'HTTP/{} {}\r\n' \
               'Server: Server'.format(self.protocol, self.code.value)

    def build(self):
        if self.code == ResponseCode.OK:
            return self.__success().encode() + self.data
        if self.code == ResponseCode.NOT_FOUND \
                or self.code == ResponseCode.NOT_ALLOWED \
                or self.code == ResponseCode.FORBIDDEN:
            return self.__not_found().encode()

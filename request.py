import urllib.parse


class Request:
    def __init__(self, data):
        self.error = False
        self.data = data.decode('UTF-8')
        self.method = self.__parse_method()
        self.protocol = self.__parse_protocol()
        self.url = self.__parse_url()
        self.headers = self.__parse_headers()
        self.query = self.__parse_query()

        print(self.method, self.url)

    def __parse_method(self):
        method = self.data.split(' ')[0]
        if method not in ['HEAD', 'GET']:
            print('ERROR')
            self.error = True
        return method

    def __parse_protocol(self):
        try:
            return self.data.split('\r\n')[0].split(' ')[2].split('HTTP/')[1]
        except IndexError:
            return '1.0'

    def __parse_url(self):
        try:
            url = urllib.parse.unquote((self.data.split(' ')[1].split('?')[0]))
            if len(url) == 0:
                url += '/'
            return url
        except:
            print(self.data)
            print(self.data.split(' '))

    def __parse_query(self):
        params = {}
        try:
            for param in self.data.split(' ')[1].split('?')[1].split('&'):
                params[param.split('=')[0]] = param.split('=')[1]
            return params
        except IndexError:
            return None

    def __parse_headers(self):
        headers = {}

        try:
            for header in self.data.split('\r\n\r\n')[0].split('\r\n')[1:]:
                headers[header.split(':')[0]] = header.split(':')[1][1:]
            return headers
        except IndexError:
            return None
# -*- coding=utf8 -*-

from dracula import make_server


if __name__ == '__main__':
    server = make_server(1, 1, '127.0.0.1', 9998)
    server.serve()

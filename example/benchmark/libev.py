# -*- coding=utf8 -*-
from dracula import make_server
from dispatcher import (
    Dispatcher,
    hash_thrift,
)


if __name__ == '__main__':
    server = make_server(hash_thrift.HashService,
                         Dispatcher(), '127.0.0.1', 9998)
    server.serve()

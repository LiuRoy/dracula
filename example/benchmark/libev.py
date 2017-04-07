# -*- coding=utf8 -*-
import hashlib
import thriftpy
from dracula import make_server

hash_thrift = thriftpy.load("hash.thrift", module_name="hash_thrift")


class Dispatcher(object):
    def md_five(self, input_str):
        m1 = hashlib.md5()
        m1.update(input_str)
        return m1.hexdigest()

if __name__ == '__main__':
    server = make_server(hash_thrift.HashService,
                         Dispatcher(), '127.0.0.1', 9999)
    server.serve()

# -*- coding=utf8 -*-
import hashlib
import thriftpy
from dracula import make_server


test_thrift = thriftpy.load("test.thrift", module_name="test_thrift")


class Dispatcher(object):
    def get_md5(self, input_str):
        m2 = hashlib.md5()
        m2.update(input_str)
        return m2.hexdigest()


if __name__ == '__main__':
    server = make_server(test_thrift.TestService,
                         Dispatcher(), '127.0.0.1', 9998)
    server.serve()

# -*- coding=utf8 -*-
import thriftpy
from dracula import make_server


test_thrift = thriftpy.load("test.thrift", module_name="test_thrift")


class Dispatcher(object):
    def test(self, input_str, input_struct):
        print input_str
        print input_struct.__dict__
        return 'aaaaa'


if __name__ == '__main__':
    server = make_server(test_thrift.TestService,
                         Dispatcher(), '127.0.0.1', 9998)
    server.serve()

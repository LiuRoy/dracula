# -*- coding=utf8 -*-
import thriftpy
from thriftpy.rpc import make_client

if __name__ == '__main__':
    test_thrift = thriftpy.load("test.thrift", module_name="test_thrift")
    client = make_client(test_thrift.TestService, '127.0.0.1', 9998)
    print client.get_md5('asdfsfdsf')

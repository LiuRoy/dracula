# -*- coding=utf8 -*-
import thriftpy
from thriftpy.rpc import make_client

if __name__ == '__main__':
    test_thrift = thriftpy.load("test.thrift", module_name="test_thrift")
    client = make_client(test_thrift.TestService, '127.0.0.1', 9998)
    args = test_thrift.bbb(b1=3.4, b2=['aaa', 'bbb'], b3={
        '111': test_thrift.aaa(a1=1, a2='a2'),
        '222': test_thrift.aaa(a1=2, a2='a2')
    })
    print client.get_md5('a', args)

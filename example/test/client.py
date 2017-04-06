# -*- coding=utf8 -*-
import thriftpy
from thriftpy.rpc import make_client

if __name__ == '__main__':
    test_thrift = thriftpy.load("test.thrift", module_name="test_thrift")
    client = make_client(test_thrift.TestService, '127.0.0.1', 9998)
    args = test_thrift.bbb(b1=3.4, b2=['a', 'b', 'c'],
                           b3={'aaa': test_thrift.aaa(a1=1, a2='1'),
                               'bbb': test_thrift.aaa(a1=1, a2='1')},
                           b4=[test_thrift.aaa(a1=1, a2='1'), test_thrift.aaa(a1=1, a2='1')],
                           b5={'string': [test_thrift.aaa(a1=1, a2='1')]},
                           b6=[[test_thrift.aaa(a1=1, a2='1')]])
    print client.test('a' * 10000, args)
    client.close()


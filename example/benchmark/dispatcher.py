# -*- coding=utf8 -*-
import hashlib
import thriftpy

hash_thrift = thriftpy.load("hash.thrift", module_name="hash_thrift")


class Dispatcher(object):
    def md5(self, input_str):
        print input_str
        m1 = hashlib.md5()
        m1.update(input_str)
        return m1.hexdigest()

# -*- coding=utf8 -*-
from locust import (
    Locust,
    TaskSet,
    task
)
import thriftpy
from thriftpy.rpc import make_client

hash_thrift = thriftpy.load("hash.thrift", module_name="hash_thrift")
hash_client = make_client(hash_thrift.HashService, '127.0.0.1', 9998)


class MyTaskSet(TaskSet):
    @task
    def short(self):
        print hash_client.md5('aaaaaaaa')


class MyLocust(Locust):
    task_set = MyTaskSet
    min_wait = 5000
    max_wait = 15000

# -*- coding=utf8 -*-
import time
import thriftpy
from thriftpy.protocol import TBinaryProtocolFactory
from thriftpy.thrift import TClient
from thriftpy.transport import (
    TBufferedTransportFactory,
    TSocket,
)
from locust import (
    Locust,
    events,
    task,
    TaskSet,
)

# from thriftpy.rpc import make_client
# hash_thrift = thriftpy.load("hash.thrift", module_name="hash_thrift")
# client = make_client(hash_thrift.HashService, '127.0.0.1', 6001)
# print client.md_five('aaaaaa')


class ThriftClient(TClient):

    def __getattr__(self, name):

        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                func = super(ThriftClient, self).__getattr__(name)
                result = func(*args, **kwargs)
            except Exception as e:
                total_time = int((time.time() - start_time) * 1000)
                events.request_failure.fire(request_type="thrift", name=name,
                                            response_time=total_time,
                                            exception=e)
            else:
                total_time = int((time.time() - start_time) * 1000)
                events.request_success.fire(request_type="thrift", name=name,
                                            response_time=total_time,
                                            response_length=0)
                return result

        return wrapper


class ThriftLocust(Locust):
    def __init__(self):
        super(ThriftLocust, self).__init__()
        socket = TSocket('127.0.0.1', 6001)
        proto_factory = TBinaryProtocolFactory()
        trans_factory = TBufferedTransportFactory()
        transport = trans_factory.get_transport(socket)
        protocol = proto_factory.get_protocol(transport)
        transport.open()
        hash_thrift = thriftpy.load("hash.thrift", module_name="hash_thrift")
        self.client = ThriftClient(hash_thrift.HashService, protocol)


class ApiUser(ThriftLocust):
    min_wait = 100
    max_wait = 1000

    class task_set(TaskSet):
        @task(10)
        def short(self):
            self.client.md_five('aaaaa')

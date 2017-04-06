import time
from thriftpy.transport import TSocket
from locust import (
    Locust,
    events,
    task,
    TaskSet,
)


class SocketClient(TSocket):

    def __getattr__(self, name):

        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                self.write(name)
                result = self.read(len(name))
            except Exception as e:
                total_time = int((time.time() - start_time) * 1000)
                events.request_failure.fire(request_type="sock", name=name,
                                            response_time=total_time,
                                            exception=e)
            else:
                total_time = int((time.time() - start_time) * 1000)
                events.request_success.fire(request_type="sock", name=name,
                                            response_time=total_time,
                                            response_length=0)
                return result

        return wrapper


class ThriftLocust(Locust):
    def __init__(self):
        super(ThriftLocust, self).__init__()
        self.client = SocketClient('127.0.0.1', 9876)
        self.client.open()


class ApiUser(ThriftLocust):
    min_wait = 100
    max_wait = 1000

    class task_set(TaskSet):
        @task(10)
        def short(self):
            self.client.md_five('aaaaa')

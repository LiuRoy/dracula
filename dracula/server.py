# -*- coding=utf8 -*-
import signal
import socket
import logging

import pyev
from .request import Request

logging.basicConfig(level=logging.DEBUG)


class Server(object):
    """server"""
    def __init__(self, socket, service, handler):
        self.socket = socket
        self.service = service
        self.handler = handler
        self.loop = pyev.default_loop()

    def on_request(self, watcher, revents):
        """处理请求"""
        try:
            client_socket, address = self.socket.accept()
        except socket.error as err:
            logging.error('error accepting a connection')
        else:
            client_socket.setblocking(False)
            request = Request(client_socket, address,
                              self.service, self.handler, self.loop)
            request.io_watcher.start()

    def on_stop(self, watcher, revents):
        """处理STOP信号"""
        self.loop.stop(pyev.EVBREAK_ALL)
        watcher.stop()

    def start(self):
        accept_watcher = pyev.Io(
            self.socket, pyev.EV_READ, self.loop, self.on_request)
        accept_watcher.start()

        stop_watcher = pyev.Signal(signal.SIGTERM, self.loop, self.on_stop)
        stop_watcher.start()

        self.loop.start()

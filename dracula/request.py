# -*- coding=utf8 -*-
"""handle request"""
import socket
import pyev

from .const import (
    READ_BUFFER_SIZE,
    NOT_BLOCKING,
)


class Request(object):
    """request"""
    def __init__(self, socket, address, service, handler, loop):
        self.socket = socket
        self.address = address
        self.service = service
        self.handler = handler
        self.loop = loop

        self.io_watcher = pyev.Io(
            self.socket, pyev.EV_READ, self.loop, self.on_read)

    def on_read(self, watcher, revents):
        """读取数据"""
        try:
            buf = self.socket.read(READ_BUFFER_SIZE)
            print buf
        except socket.error as err:
            pass

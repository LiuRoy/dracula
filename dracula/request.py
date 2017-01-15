# -*- coding=utf8 -*-
"""handle request"""
import socket
import pyev

from .const import (
    READ_BUFFER_SIZE,
    NOT_BLOCKING,
    ReadState,
)
from .thrift import (
    TError,
    Decoder,
    Encoder,
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
            self.socket, pyev.EV_READ, self.loop, self.handle)
        self.decoder = Decoder(service, handler)
        self.read_state = None

    def handle(self, watcher, revents):
        if revents & pyev.EV_READ:
            self.on_read(watcher, revents)
        else:
            self.on_write(watcher, revents)

    def on_read(self, watcher, revents):
        """读取数据"""
        try:
            buf = self.socket.recv(READ_BUFFER_SIZE)
        except socket.error as err:
            if err.args[0] in NOT_BLOCKING:
                self.read_state = ReadState.not_done
            else:
                self.read_state = ReadState.aborted
        else:
            # result = self.decoder.parse(buf)
            # if self.decoder.error_code != TError.NO_ERROR:
            #     self.read_state = ReadState.done
            # elif result is None:
            #     self.read_state = ReadState.not_done
            # else:
            #     self.read_state = ReadState.done
            #     # todo 调用thrift生成结果
            self.read_state = ReadState.done

        if self.read_state == ReadState.aborted:
            # todo 发送具体结果
            self.close_connection()
        elif self.read_state == ReadState.done:
            watcher.stop()
            watcher.set(self.socket, pyev.EV_WRITE)
            watcher.start()

    def on_write(self, watcher, revents):
        """写入数据"""
        #todo 写入thrift数据
        try:
            sent = self.socket.send('aaaaa\n')
        except socket.error as err:
            if err.args[0] not in NOT_BLOCKING:
                self.close_connection()
        else:
            # todo发送完毕后keep alive
            watcher.stop()
            watcher.set(self.socket, pyev.EV_READ)
            watcher.start()

    def close_connection(self):
        """关闭socket"""
        self.loop.stop(pyev.EVBREAK_ALL)
        self.socket.close()

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
    TMessageType,
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
        self.encoder = None

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
            result = self.decoder.parse(buf)
            if self.decoder.error_code != TError.NO_ERROR:
                self.read_state = ReadState.done
            elif result is None:
                self.read_state = ReadState.not_done
            else:
                self.read_state = ReadState.done
                self.execute_method()

        if self.read_state == ReadState.aborted:
            # todo 发送异常
            pass
        elif self.read_state == ReadState.done:
            watcher.stop()
            watcher.set(self.socket, pyev.EV_WRITE)
            watcher.start()

    def on_write(self, watcher, revents):
        """写入数据"""
        encoder = Encoder(self.decoder.parse_data)
        try:
            sent = self.socket.send(encoder.encode_obj(TMessageType.REPLY))
        except socket.error as err:
            if err.args[0] not in NOT_BLOCKING:
                self.close_connection()
        else:
            watcher.stop()
            watcher.set(self.socket, pyev.EV_READ)
            watcher.start()
            self.decoder = Decoder(self.service, self.handler)

    def close_connection(self):
        """关闭socket"""
        self.loop.stop(pyev.EVBREAK_ALL)
        self.socket.close()

    def execute_method(self):
        """执行thrift method"""
        func = getattr(self.handler, self.decoder.parse_data.method_name)
        args = self.decoder.parse_data.method_args
        api_args = [args.thrift_spec[k][1] for k in sorted(args.thrift_spec)]
        try:
            self.decoder.parse_data.method_result.success = \
                func(*(args.__dict__[k] for k in api_args))
        except Exception as e:
            # raise if api don't have throws
            # todo 处理异常
            pass

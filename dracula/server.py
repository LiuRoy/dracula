# -*- coding=utf8 -*-
import signal
import socket
import logging

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

logging.basicConfig(level=logging.ERROR)


class ThreadInfo(object):
    """线程信息"""
    def __init__(self, service, handler):
        self.service = service
        self.handler = handler
        self.io_watcher = None


class Request(object):
    """request"""
    def __init__(self):
        self.io_watcher = None
        self.decoder = None
        self.read_state = None
        self.encoder = None


def server_run(socket, service, handler):
    """运行thrift server"""
    thread_info = ThreadInfo(service, handler)
    main_loop = pyev.Loop(0, data=thread_info)

    io_watcher = pyev.Io(
        socket.fileno(), pyev.EV_READ, main_loop, on_request)
    io_watcher.start()

    stop_watcher = pyev.Signal(signal.SIGINT, main_loop, on_stop)
    stop_watcher.start()

    main_loop.start()


def on_request(watcher, revents):
    try:
        # todo 根据watcher.fd生成sock
        client_socket, address = sock.accept()
    except socket.error as err:
        logging.error('error accepting a connection')
    else:
        client_socket.setblocking(False)
        request = Request()
        request.io_watcher = pyev.Io(
            client_socket, pyev.EV_READ, watcher.loop, on_read, data=request)
        request.io_watcher.start()


def on_stop(watcher, revents):
    watcher.loop.stop(pyev.EVBREAK_ALL)


def on_read(watcher, revents):
    """读取数据"""
    request = watcher.data
    try:
        # todo 根据watcher.fd生成sock
        buf = socket.recv(READ_BUFFER_SIZE)
    except socket.error as err:
        if err.args[0] in NOT_BLOCKING:
            request.read_state = ReadState.not_done
        else:
            request.read_state = ReadState.aborted
    else:
        result = request.decoder.parse(buf)
        if request.decoder.error_code != TError.NO_ERROR:
            request.read_state = ReadState.done
        elif result is None:
            request.read_state = ReadState.not_done
        else:
            request.read_state = ReadState.done
            execute_method(request, watcher.loop.data.handler)

    if request.read_state == ReadState.aborted:
        # todo 发送异常
        pass
    elif request.read_state == ReadState.done:
        watcher.stop()
        watcher.set(watcher.fd, pyev.EV_WRITE)
        watcher.callback = on_write
        watcher.start()


def on_write(watcher, revents):
    """写入数据"""
    request = watcher.data
    request.encoder = Encoder()
    try:
        socket.send(request.encoder.encode_obj(
            request.decoder.parse_data, TMessageType.REPLY))
    except socket.error as err:
        if err.args[0] not in NOT_BLOCKING:
            socket.close()
    else:
        watcher.stop()
        watcher.set(watcher.fd, pyev.EV_READ)
        watcher.start()
        thread_data = watcher.loop.data
        request.decoder = Decoder(thread_data.service, thread_data.handler)


def execute_method(request, handler):
    """执行thrift method"""
    func = getattr(handler, request.decoder.parse_data.method_name)
    args = request.decoder.parse_data.method_args
    api_args = [args.thrift_spec[k][1] for k in sorted(args.thrift_spec)]
    try:
        request.decoder.parse_data.method_result.success = \
            func(*(args.__dict__[k] for k in api_args))
    except Exception as e:
        # raise if api don't have throws
        # todo 处理异常
        pass

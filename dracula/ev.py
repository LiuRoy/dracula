# -*- coding=utf8 -*-
"""libev接收请求"""
import errno
import signal
import socket
import logging

import pyev
from .const import (
    READ_BUFFER_SIZE,
    ReadState,
)
from .thrift import (
    TError,
    Decoder,
    Encoder,
    TMessageType,
)

logging.basicConfig(level=logging.INFO)


class ThreadInfo(object):
    """线程信息"""
    def __init__(self, sock, service, handler):
        self.sock = sock
        self.service = service
        self.handler = handler
        self.io_watcher = None


class Request(object):
    """单个请求"""
    def __init__(self, sock, service, handler):
        self.sock = sock
        self.io_watcher = None
        self.decoder = Decoder(service, handler)
        self.read_state = None
        self.encoder = None


def server_run(sock, service, handler):
    """运行thrift server"""
    thread_info = ThreadInfo(sock, service, handler)
    main_loop = pyev.Loop(0, data=thread_info)

    io_watcher = pyev.Io(sock, pyev.EV_READ, main_loop, on_request)
    io_watcher.start()

    stop_watcher = pyev.Signal(signal.SIGINT, main_loop, on_stop)
    stop_watcher.start()

    main_loop.start()


def on_request(watcher, revents):
    thread_data = watcher.loop.data
    sock = thread_data.sock
    try:
        client_socket, address = sock.accept()
    except socket.error as err:
        logging.error('error accepting a connection: {}'.format(err))
    else:
        client_socket.setblocking(False)
        request = Request(
            client_socket, thread_data.service, thread_data.handler)
        request.io_watcher = pyev.Io(
            client_socket, pyev.EV_READ, watcher.loop, on_read, data=request)
        request.io_watcher.start()


def on_stop(watcher, revents):
    watcher.loop.stop(pyev.EVBREAK_ALL)


def on_read(watcher, revents):
    """读取数据"""
    request = watcher.data
    sock = request.sock
    try:
        buf = sock.recv(READ_BUFFER_SIZE)
    except socket.error as err:
        if err.errno == errno.EWOULDBLOCK:
            request.read_state = ReadState.not_done
        else:
            request.read_state = ReadState.aborted
    else:
        if not buf:
            # 客户端写完毕
            request.read_state = ReadState.done
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
        watcher.set(sock, pyev.EV_WRITE)
        watcher.callback = on_write
        watcher.start()


def on_write(watcher, revents):
    """写入数据"""
    request = watcher.data
    request.encoder = Encoder()
    sock = request.sock
    try:
        sock.send(request.encoder.encode_obj(
            request.decoder.parse_data, TMessageType.REPLY))
    except socket.error as err:
        logging.error('error writing: {}'.format(err))
        sock.close()
    else:
        sock.shutdown(socket.SHUT_WR)
        watcher.stop()


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

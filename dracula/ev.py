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

logging.basicConfig(level=logging.ERROR)

# python的垃圾回收机制可能会把socket都回收掉, 放在全局变量中避免此情况
all_requests = {}


class ThreadInfo(object):
    """线程信息"""
    def __init__(self, sock, service, handler):
        self.sock = sock
        self.service = service
        self.handler = handler
        self.io_watcher = None


class Request(object):
    """单个请求"""
    def __init__(self, sock, service, handler, address):
        self.sock = sock
        self.io_watcher = None
        self.decoder = Decoder(service, handler)
        self.read_state = None
        self.encoder = None
        self.address = address


def server_run(sock, service, handler):
    """运行thrift server"""
    thread_info = ThreadInfo(sock, service, handler)
    main_loop = pyev.Loop(0, data=thread_info)

    io_watcher = pyev.Io(sock, pyev.EV_READ, main_loop, on_request)
    io_watcher.start()

    stop_watcher = pyev.Signal(signal.SIGINT, main_loop, on_stop, priority=5)
    stop_watcher.start()

    main_loop.start()


def on_request(watcher, revents):
    thread_data = watcher.loop.data
    sock = thread_data.sock
    try:
        client_socket, address = sock.accept()
        logging.info("accept address: {}".format(address))
    except socket.error as err:
        logging.error('error accepting a connection: {}'.format(err))
    else:
        client_socket.setblocking(False)
        request = Request(
            client_socket, thread_data.service, thread_data.handler, address)
        request.io_watcher = pyev.Io(
            client_socket, pyev.EV_READ, watcher.loop, on_read,
            data=request)
        request.io_watcher.start()
        all_requests[address] = request


def on_stop(watcher, revents):
    thread_data = watcher.loop.data
    listen_sock = thread_data.sock

    watcher.loop.stop(pyev.EVBREAK_ALL)
    listen_sock.close()
    for _, request in all_requests.iteritems():
        request.sock.close()


def on_read(watcher, revents):
    """读取数据"""
    request = watcher.data
    sock = request.sock
    try:
        buf = sock.recv(READ_BUFFER_SIZE)
        logging.info("from {} receive size {}".format(request.address, len(buf)))
    except socket.error as err:
        if err.errno == errno.EWOULDBLOCK:
            request.read_state = ReadState.not_done
        else:
            request.read_state = ReadState.aborted
    else:
        if not buf:
            logging.info("close socket: {}".format(request.address))
            sock.close()
            watcher.stop()
            all_requests.pop(request.address)
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
        logging.info("write socket: {} finish".format(request.address))
    except socket.error as err:
        logging.exception(err)
        logging.info("close socket: {}".format(request.address))
        sock.close()
        watcher.stop()
        all_requests.pop(request.address)
    else:
        watcher.stop()
        watcher.set(sock, pyev.EV_READ)
        watcher.callback = on_read
        thread_data = watcher.loop.data
        request.decoder = Decoder(thread_data.service, thread_data.handler)
        request.read_state = None
        watcher.start()


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

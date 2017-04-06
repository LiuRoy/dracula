# -*- coding=utf8 -*-
"""thrift server"""
import socket
from .ev import server_run
from .const import LISTEN_BACKLOG


class ThriftServer(object):

    """thrift server

    Attributes:
        service: thrift service
        handler: thrift handler
        sock (socket)
    """
    def __init__(self, service, handler):
        self.sock = None
        self.service = service
        self.handler = handler

    def bind_and_listen(self, host, port, reuse_port):
        """绑定并监听端口"""
        self.sock = socket.socket()

        # 监听套接字设置为非阻塞
        self.sock.setblocking(False)

        # 允许多个进程使用同一端口 方便扩展
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if reuse_port:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        self.sock.bind((host, port))
        self.sock.listen(LISTEN_BACKLOG)

    def serve(self):
        """启动服务"""
        try:
            server_run(self.sock, self.service, self.handler)
        finally:
            self.sock.close()


def make_server(service, handler, host, port, reuse_port=False):
    """生成thrift server

    Args:
        service: thrift service
        handler: thrift handler
        host (basestring): 服务地址
        port (int): 服务端口
        reuse_port (bool): 是否多个进程监听同一端口

    Returns:
        ThriftServer
    """
    server = ThriftServer(service, handler)
    server.bind_and_listen(host, port, reuse_port)
    return server

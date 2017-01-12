# -*- coding=utf8 -*-
import struct
from cStringIO import StringIO
from .common import (
    VERSION_MASK,
    VERSION_1,
    TType,
    TState,
    TError,
)


def unpack_i8(buf):
    return struct.unpack("!b", buf)[0]


def unpack_i16(buf):
    return struct.unpack("!h", buf)[0]


def unpack_i32(buf):
    return struct.unpack("!i", buf)[0]


def unpack_i64(buf):
    return struct.unpack("!q", buf)[0]


def unpack_double(buf):
    return struct.unpack("!d", buf)[0]


class ParseData(object):
    """thrift解析数据"""
    sequence_id = 0
    method_name = None
    method_args = None
    method_result = None


class Decoder(object):
    """解析thrift二进制数据"""
    def __init__(self, service, handler, strict=True):
        self.service = service
        self.handler = handler
        self.strict = strict

        self.current_state = TState.S_VERSION
        self.latest_result = None
        self.parse_data = ParseData()
        self.error_code = TError.NO_ERROR

        self._left = ''
        self._buf = None
        self._process_stack = []

    def read(self, size):
        """从缓存中读取长度为size的内容

        Args:
            size (int): 读取的长度
        """
        result = self._buf.read(size)
        if len(result) != size:
            self._left = result
            self._buf = None
            return None
        return result

    def parse(self, data):
        """解析二级制数据

        Args:
             data (string): 待解析数据
        """
        self._buf = StringIO(self._left + data)

        while True:
            if self.error_code != TError.NO_ERROR:
                break

            if self.current_state == TState.S_VERSION:
                read_data = self.read(4)
                if not read_data:
                    break
                self.latest_result = unpack_i32(read_data)

                if self.latest_result < 0:
                    version = self.latest_result & VERSION_MASK
                    if version != VERSION_1:
                        self.error_code = TError.BAD_VERSION
                    self.current_state = TState.S_METHOD_SIZE
                else:
                    if self.strict:
                        self.error_code = TError.NO_PROTOCOL
                    self.current_state = TState.S_METHOD_NAME2

            elif self.current_state == TState.S_METHOD_SIZE:
                read_data = self.read(4)
                if not read_data:
                    break
                self.latest_result = unpack_i32(read_data)
                self.current_state = TState.S_METHOD_NAME

            elif self.current_state == TState.S_METHOD_NAME:
                read_data = self.read(self.latest_result)
                if not read_data:
                    break
                self.parse_data.method_name = read_data.decode('utf8')
                self.current_state = TState.S_SEQUENCE_ID

            elif self.current_state == TState.S_METHOD_NAME2:
                read_data = self.read(self.latest_result)
                if not read_data:
                    break
                self.parse_data.method_name = read_data.decode('utf8')
                self.current_state = TState.S_METHOD_TYPE

            elif self.current_state == TState.S_METHOD_TYPE:
                read_data = self.read(1)
                if not read_data:
                    break
                self.current_state = TState.S_SEQUENCE_ID

            elif self.current_state == TState.S_SEQUENCE_ID:
                read_data = self.read(4)
                if not read_data:
                    break
                self.parse_data.sequence_id = unpack_i32(read_data)

                if self.parse_data.method_name not in \
                        self.service.thrift_services:
                    self.error_code = TError.UNKNOWN_METHOD
                else:
                    self.parse_data.method_args = \
                        getattr(self.service, self.parse_data.method_name + "_args")()
                    self.parse_data.method_result = \
                        getattr(self.service, self.parse_data.method_name + "_result")()
                    self.current_state = TState.S_READ_FIELD_TYPE

            # todo

            elif self.current_state == TState.S_PARSE_DONE:
                break

            else:
                self.error_code = TError.INTERNAL_ERROR

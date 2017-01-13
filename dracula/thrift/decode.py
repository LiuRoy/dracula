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
    def __init__(self, service, handler, strict=True, decode_response=True):
        self.service = service
        self.handler = handler
        self.strict = strict
        self.decode_response = decode_response

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
        result = None

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
                    self._process_stack.append((TState.S_READ_FIELD_TYPE,
                                                self.parse_data.method_args, -1))

            elif self.current_state == TState.S_READ_FIELD_TYPE:
                read_data = self.read(4)
                if not read_data:
                    break
                self.latest_result = unpack_i8(read_data)
                if self.latest_result == TType.STOP:
                    top = self._process_stack.pop()
                    if self._process_stack:
                        self.current_state = self._process_stack[-1][0]
                    else:
                        result = top[1]
                        self.current_state = TState.S_PARSE_DONE
                else:
                    self.current_state = TState.S_READ_FIELD_ID

            elif self.current_state == TState.S_READ_FIELD_ID:
                read_data = self.read(2)
                if not read_data:
                    break
                self.latest_result = (self.latest_result, unpack_i16(read_data))
                f_type, fid = self.latest_result
                obj = self._process_stack[-1][1]
                if fid not in obj.thrift_spec:
                    pass
                    #todo skip(f_type)
                else:
                    if len(obj.thrift_spec[fid]) == 3:
                        sf_type, f_name, f_req = obj.thrift_spec[fid]
                        f_container_spec = None
                    else:
                        sf_type, f_name, f_container_spec, f_req = obj.thrift_spec[fid]

                    #todo read_val(f_type, f_container_spec,self.decode_response)
                    #todo setattr(obj, f_name, ..)

            elif self.current_state == TState.S_PARSE_DONE:
                break

            else:
                self.error_code = TError.INTERNAL_ERROR

        return result

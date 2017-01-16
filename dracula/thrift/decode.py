# -*- coding=utf8 -*-
import struct
from cStringIO import StringIO
from .common import (
    VERSION_MASK,
    VERSION_1,
    TType,
    TState,
    TError,
    BASIC_TYPE,
    ParseData,
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


class Decoder(object):
    """thrift解码"""
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

    def read_basic(self, f_type):
        """读取基本类型数据

        Args:
            f_type (int): 字段类型
        """
        if f_type == TType.BOOL:
            read_data = self.read(1)
            if read_data:
                return bool(unpack_i8(read_data))
        elif f_type == TType.BYTE:
            read_data = self.read(1)
            if read_data:
                return unpack_i8(read_data)
        elif f_type == TType.I16:
            read_data = self.read(2)
            if read_data:
                return unpack_i16(read_data)
        elif f_type == TType.I32:
            read_data = self.read(4)
            if read_data:
                return unpack_i32(read_data)
        elif f_type == TType.I64:
            read_data = self.read(8)
            if read_data:
                return unpack_i64(read_data)
        elif f_type == TType.DOUBLE:
            read_data = self.read(8)
            if read_data:
                return unpack_double(read_data)

    def next_state(self, f_type, f_spec=None):
        """根据当前类型决定下一状态

        Args:
            f_type (int): 字段类型
            f_spec (class)
        """
        if f_type in BASIC_TYPE:
            self.current_state = TState.S_READ_BASIC
        elif f_type == TType.STRING:
            self.current_state = TState.S_READ_STRING_SIZE
        elif f_type in (TType.LIST, TType.SET):
            self.current_state = TState.S_READ_LIST_TYPE
        elif f_type == TType.MAP:
            self.current_state = TState.S_READ_MAP_KEY_TYPE
        elif f_type == TType.STRUCT:
            self.current_state = TState.S_READ_FIELD_TYPE
            self._process_stack.append(
                [TState.S_READ_FIELD_TYPE, f_spec(), -1, None])
        else:
            self.error_code = TError.INTERNAL_ERROR

    def pop_stack(self):
        """回溯处理站"""
        result = None
        while True:
            top = self._process_stack[-1]
            if top[0] == TState.S_READ_LIST_TYPE:
                if top[2] <= 0:
                    self._process_stack.pop()
                    result = top[1]
                elif result is not None:
                    top[1].append(result)
                    top[2] -= 1
                else:
                    break
            elif top[0] == TState.S_READ_MAP_KEY_TYPE:
                if top[2] <= 0:
                    self._process_stack.pop()
                    result = dict(top[1])
                elif result is not None:
                    if not top[1]:
                        top[1].append((result, None))
                        break
                    else:
                        if top[1][-1][1] is None:
                            key, val = top[1].pop()
                            top[1].append((key, result))
                            top[2] -= 1
                        else:
                            top[1].append((result, None))
                            break
                else:
                    break
            else:
                if result is not None:
                    f_name = top[3][0]
                    setattr(top[1], f_name, result)
                break

    def get_type_spec(self):
        """根据栈顶信息找到要处理的type和spec信息"""
        top = self._process_stack[-1]
        if top[0] in (TState.S_READ_LIST_TYPE,
                      TState.S_READ_FIELD_TYPE):
            return top[3][1], top[3][2]

        if top[1]:
            if top[1][-1][1] is None:
                return top[3][3], top[3][4]
            return top[3][1], top[3][2]
        return top[3][1], top[3][2]

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
                    self._process_stack.append([TState.S_READ_FIELD_TYPE,
                                                self.parse_data.method_args,
                                                -1, None])

            elif self.current_state == TState.S_READ_FIELD_TYPE:
                read_data = self.read(1)
                if not read_data:
                    break
                self.latest_result = unpack_i8(read_data)
                if self.latest_result == TType.STOP:
                    top = self._process_stack.pop()
                    if self._process_stack:
                        stack_top = self._process_stack[-1]
                        if stack_top[0] == TState.S_READ_LIST_TYPE:
                            stack_top[2] -= 1
                            stack_top[1].append(top[1])
                            self.pop_stack()
                        elif stack_top[0] == TState.S_READ_MAP_KEY_TYPE:
                            if not stack_top[1]:
                                stack_top[1].append((top[1], None))
                            else:

                                if stack_top[1][-1][1] is None:
                                    stack_top[2] -= 1
                                    top_pair = stack_top[1].pop()
                                    stack_top[1].append(
                                        (top_pair[0], top[1]))
                                    self.pop_stack()
                                else:
                                    stack_top[1].append((top[1], None))
                        else:
                            f_name = stack_top[3][0]
                            setattr(stack_top[1], f_name, top[1])

                        if self._process_stack[-1][0] in (
                                TState.S_READ_LIST_TYPE,
                                TState.S_READ_MAP_KEY_TYPE):
                            f_spec, f_type = self.get_type_spec()
                            self.next_state(f_type, f_spec=f_spec)
                        else:
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
                f_type, fid = self.latest_result, unpack_i16(read_data)
                obj = self._process_stack[-1][1]
                if fid not in obj.thrift_spec:
                    self.error_code = TError.SKIP_ERROR
                else:
                    if len(obj.thrift_spec[fid]) == 3:
                        sf_type, f_name, f_req = obj.thrift_spec[fid]
                        f_container_spec = None
                    else:
                        sf_type, f_name, f_container_spec, f_req = obj.thrift_spec[fid]

                    if sf_type != f_type:
                        self.error_code = TError.SKIP_ERROR
                    else:
                        self._process_stack[-1][3] = (f_name, f_container_spec, f_type)
                        self.next_state(f_type, f_spec=f_container_spec)

            elif self.current_state == TState.S_READ_BASIC:
                _, f_type = self.get_type_spec()
                read_data = self.read_basic(f_type)
                if not read_data:
                    break
                stack_top = self._process_stack[-1]
                if stack_top[0] == TState.S_READ_LIST_TYPE:
                    stack_top[2] -= 1
                    stack_top[1].append(read_data)
                    self.pop_stack()
                elif stack_top[0] == TState.S_READ_MAP_KEY_TYPE:
                    if not stack_top[1]:
                        stack_top[1].append((read_data, None))
                    else:

                        if stack_top[1][-1][1] is None:
                            stack_top[2] -= 1
                            top_pair = stack_top[1].pop()
                            stack_top[1].append((top_pair[0], read_data))
                            self.pop_stack()
                        else:
                            stack_top[1].append((read_data, None))
                else:
                    f_name = stack_top[3][0]
                    setattr(stack_top[1], f_name, read_data)

                if self._process_stack[-1][0] in (TState.S_READ_LIST_TYPE,
                                                  TState.S_READ_MAP_KEY_TYPE):
                    f_spec, f_type = self.get_type_spec()
                    self.next_state(f_type, f_spec=f_spec)
                else:
                    self.current_state = self._process_stack[-1][0]

            elif self.current_state == TState.S_READ_STRING_SIZE:
                read_data = self.read(4)
                if not read_data:
                    break
                self.latest_result = unpack_i32(read_data)
                self.current_state = TState.S_READ_STRING

            elif self.current_state == TState.S_READ_STRING:
                read_data = self.read(self.latest_result)
                if not read_data:
                    break

                if self.decode_response:
                    try:
                        read_data = read_data.decode('utf-8')
                    except UnicodeDecodeError:
                        pass

                stack_top = self._process_stack[-1]
                if stack_top[0] == TState.S_READ_LIST_TYPE:
                    stack_top[2] -= 1
                    stack_top[1].append(read_data)
                    self.pop_stack()
                elif stack_top[0] == TState.S_READ_MAP_KEY_TYPE:
                    if not stack_top[1]:
                        stack_top[1].append((read_data, None))
                    else:

                        if stack_top[1][-1][1] is None:
                            stack_top[2] -= 1
                            top_pair = stack_top[1].pop()
                            stack_top[1].append((top_pair[0], read_data))
                            self.pop_stack()
                        else:
                            stack_top[1].append((read_data, None))
                else:
                    f_name = stack_top[3][0]
                    setattr(stack_top[1], f_name, read_data)

                if self._process_stack[-1][0] in (TState.S_READ_LIST_TYPE,
                                                  TState.S_READ_MAP_KEY_TYPE):
                    f_spec, f_type = self.get_type_spec()
                    self.next_state(f_type, f_spec=f_spec)
                else:
                    self.current_state = self._process_stack[-1][0]

            elif self.current_state == TState.S_READ_LIST_TYPE:
                read_data = self.read(1)
                if not read_data:
                    break
                self.latest_result = unpack_i8(read_data)
                self.current_state = TState.S_READ_LIST_SIZE

            elif self.current_state == TState.S_READ_LIST_SIZE:
                read_data = self.read(4)
                if not read_data:
                    break
                r_type, size = self.latest_result, unpack_i32(read_data)
                spec, _ = self.get_type_spec()
                if isinstance(spec, tuple):
                    v_type, v_spec = spec[0], spec[1]
                else:
                    v_type, v_spec = spec, None

                if r_type != v_type:
                    self.error_code = TError.SKIP_ERROR
                else:
                    self._process_stack.append([TState.S_READ_LIST_TYPE, [],
                                                size, (None, v_spec, v_type)])
                    if size <= 0:
                        import ipdb; ipdb.set_trace()
                        self.pop_stack()
                        self.current_state = self._process_stack[-1][0]
                    else:
                        self.next_state(v_type, f_spec=v_spec)

            elif self.current_state == TState.S_READ_MAP_KEY_TYPE:
                read_data = self.read(1)
                if not read_data:
                    break
                self.latest_result = unpack_i8(read_data)
                self.current_state = TState.S_READ_MAP_VALUE_TYPE

            elif self.current_state == TState.S_READ_MAP_VALUE_TYPE:
                read_data = self.read(1)
                if not read_data:
                    break
                self.latest_result = self.latest_result, unpack_i8(read_data)
                self.current_state = TState.S_READ_MAP_SIZE

            elif self.current_state == TState.S_READ_MAP_SIZE:
                read_data = self.read(4)
                if not read_data:
                    break
                size = unpack_i32(read_data)
                sk_type, sv_type = self.latest_result
                spec, _ = self.get_type_spec()
                if isinstance(spec[0], int):
                    k_type = spec[0]
                    k_spec = None
                else:
                    k_type, k_spec = spec[0]

                if isinstance(spec[1], int):
                    v_type = spec[1]
                    v_spec = None
                else:
                    v_type, v_spec = spec[1]

                if sk_type != k_type or sv_type != v_type:
                    self.error_code = TError.SKIP_ERROR
                else:
                    self._process_stack.append([TState.S_READ_MAP_KEY_TYPE, [],
                                                size, (None, k_spec, k_type, v_spec, v_type)])
                    if size <= 0:
                        self.pop_stack()
                        self.current_state = self._process_stack[-1][0]
                    else:
                        self.next_state(k_type, f_spec=k_spec)

            elif self.current_state == TState.S_PARSE_DONE:
                break

            else:
                self.error_code = TError.INTERNAL_ERROR

        return result

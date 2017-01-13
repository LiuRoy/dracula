# -*- coding=utf8 -*-

VERSION_MASK = -65536
VERSION_1 = -2147418112
TYPE_MASK = 0x000000ff


class TMessageType(object):
    CALL = 1
    REPLY = 2
    EXCEPTION = 3
    ONEWAY = 4


class TType(object):
    STOP = 0
    VOID = 1
    BOOL = 2
    BYTE = 3
    I08 = 3
    DOUBLE = 4
    I16 = 6
    I32 = 8
    I64 = 10
    STRING = 11
    UTF7 = 11
    BINARY = 11
    STRUCT = 12
    MAP = 13
    SET = 14
    LIST = 15
    UTF8 = 16
    UTF16 = 17


BASIC_TYPE = (TType.BOOL,
              TType.BYTE,
              TType.I16,
              TType.I32,
              TType.I64,
              TType.DOUBLE,)


class TState(object):
    S_VERSION = 0                # 读取版本号
    S_METHOD_SIZE = 1            # S_VERSION读取结果小于0 读取方法名字长度
    S_METHOD_NAME = 2            # S_METHOD_SIZE后读取方法名字
    S_METHOD_NAME2 = 3           # S_VERSION读取结果大于0, 直接读取方法名字
    S_METHOD_TYPE = 4            # S_METHOD_NAME2后读取方法类型
    S_SEQUENCE_ID = 5            # S_METHOD_NAME S_METHOD_TYPE后读取序列号

    S_SKIP_BASIC = 6             # 跳过基础类型
    S_SKIP_STING_SIZE = 7        # 跳过字符串长度
    S_SKIP_STRING = 8            # 跳过字符串
    S_SKIP_LIST_TYPE = 9         # 跳过list类型
    S_SKIP_LIST_SIZE = 10        # 跳过list长度
    S_SKIP_MAP_KEY_TYPE = 11     # 跳过map key类型
    S_SKIP_MAP_VALUE_TYPE = 12   # 跳过map value类型
    S_SKIP_MAP_SIZE = 13         # 跳过map长度
    S_SKIP_FIELD_TYPE = 14       # 跳过field类型
    S_SKIP_FIELD_ID = 15         # 跳过field id

    S_READ_BASIC = 18            # 读取基础类型
    S_READ_STRING_SIZE = 19      # 读取字符串长度
    S_READ_STRING = 20           # 读取字符串
    S_READ_LIST_TYPE = 21        # 读取list类型
    S_READ_LIST_SIZE = 22        # 读取list长度
    S_READ_MAP_KEY_TYPE = 22     # 读取map key类型
    S_READ_MAP_VALUE_TYPE = 23   # 读取map value类型
    S_READ_MAP_SIZE = 24         # 读取map长度
    S_READ_FIELD_TYPE = 25       # 读取field类型
    S_READ_FIELD_ID = 26         # 读取field id

    S_PARSE_DONE = 27            # 解析完成


class TError(object):
    NO_ERROR = 0
    INTERNAL_ERROR = 1

    BAD_VERSION = 2
    NO_PROTOCOL = 3

    UNKNOWN_METHOD = 4

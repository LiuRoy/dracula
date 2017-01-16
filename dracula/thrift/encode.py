# -*- coding=utf8 -*-
"""thrift编码"""
import struct
from cStringIO import StringIO
from .common import (
    VERSION_1,
    TType,
)


def pack_i8(byte):
    return struct.pack("!b", byte)


def pack_i16(i16):
    return struct.pack("!h", i16)


def pack_i32(i32):
    return struct.pack("!i", i32)


def pack_i64(i64):
    return struct.pack("!q", i64)


def pack_double(dub):
    return struct.pack("!d", dub)


def pack_string(string):
    return struct.pack("!i%ds" % len(string), len(string), string)


class Encoder(object):
    """thrift编码"""
    def __init__(self, parse_data, strict=True):
        self.parse_data = parse_data
        self.strict = strict
        self.buf = StringIO()

    def encode_obj(self, ttype):
        """编码数据
        
        Args:
            ttype (int): 编码数据类型
        """
        if self.strict:
            self.buf.write(pack_i32(VERSION_1 | ttype))
            self.buf.write(pack_string(self.parse_data.method_name.encode('utf-8')))
        else:
            self.buf.write(pack_string(self.parse_data.method_name.encode('utf-8')))
            self.buf.write(pack_i8(ttype))

        self.buf.write(pack_i32(self.parse_data.sequence_id))
        self.encode_val(TType.STRUCT, self.parse_data.method_result)

        self.buf.seek(0)
        return self.buf.read()

    def encode_field_begin(self, ttype, fid):
        self.buf.write(pack_i8(ttype) + pack_i16(fid))

    def encode_field_stop(self):
        self.buf.write(pack_i8(TType.STOP))

    def encode_list_begin(self, etype, size):
        self.buf.write(pack_i8(etype) + pack_i32(size))

    def encode_map_begin(self, ktype, vtype, size):
        self.buf.write(pack_i8(ktype) + pack_i8(vtype) + pack_i32(size))

    def encode_val(self, ttype, val, spec=None):
        if ttype == TType.BOOL:
            if val:
                self.buf.write(pack_i8(1))
            else:
                self.buf.write(pack_i8(0))
    
        elif ttype == TType.BYTE:
            self.buf.write(pack_i8(val))
    
        elif ttype == TType.I16:
            self.buf.write(pack_i16(val))
    
        elif ttype == TType.I32:
            self.buf.write(pack_i32(val))
    
        elif ttype == TType.I64:
            self.buf.write(pack_i64(val))
    
        elif ttype == TType.DOUBLE:
            self.buf.write(pack_double(val))
    
        elif ttype == TType.STRING:
            if not isinstance(val, bytes):
                val = val.encode('utf-8')
            self.buf.write(pack_string(val))
    
        elif ttype == TType.SET or ttype == TType.LIST:
            if isinstance(spec, tuple):
                e_type, t_spec = spec[0], spec[1]
            else:
                e_type, t_spec = spec, None
    
            val_len = len(val)
            self.encode_list_begin(e_type, val_len)
            for e_val in val:
                self.encode_val(e_type, e_val, t_spec)
    
        elif ttype == TType.MAP:
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
    
            self.encode_map_begin(k_type, v_type, len(val))
            for k in iter(val):
                self.encode_val(k_type, k, k_spec)
                self.encode_val(v_type, val[k], v_spec)
    
        elif ttype == TType.STRUCT:
            for fid in iter(val.thrift_spec):
                f_spec = val.thrift_spec[fid]
                if len(f_spec) == 3:
                    f_type, f_name, f_req = f_spec
                    f_container_spec = None
                else:
                    f_type, f_name, f_container_spec, f_req = f_spec
    
                v = getattr(val, f_name)
                if v is None:
                    continue
    
                self.encode_field_begin(f_type, fid)
                self.encode_val(f_type, v, f_container_spec)
            self.encode_field_stop()

# -*- coding=utf8 -*-
""""""
import struct
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


def write_message_begin(outbuf, name, ttype, seqid, strict=True):
    if strict:
        outbuf.write(pack_i32(VERSION_1 | ttype))
        outbuf.write(pack_string(name.encode('utf-8')))
    else:
        outbuf.write(pack_string(name.encode('utf-8')))
        outbuf.write(pack_i8(ttype))

    outbuf.write(pack_i32(seqid))


def write_field_begin(outbuf, ttype, fid):
    outbuf.write(pack_i8(ttype) + pack_i16(fid))


def write_field_stop(outbuf):
    outbuf.write(pack_i8(TType.STOP))


def write_list_begin(outbuf, etype, size):
    outbuf.write(pack_i8(etype) + pack_i32(size))


def write_map_begin(outbuf, ktype, vtype, size):
    outbuf.write(pack_i8(ktype) + pack_i8(vtype) + pack_i32(size))


def write_val(outbuf, ttype, val, spec=None):
    if ttype == TType.BOOL:
        if val:
            outbuf.write(pack_i8(1))
        else:
            outbuf.write(pack_i8(0))

    elif ttype == TType.BYTE:
        outbuf.write(pack_i8(val))

    elif ttype == TType.I16:
        outbuf.write(pack_i16(val))

    elif ttype == TType.I32:
        outbuf.write(pack_i32(val))

    elif ttype == TType.I64:
        outbuf.write(pack_i64(val))

    elif ttype == TType.DOUBLE:
        outbuf.write(pack_double(val))

    elif ttype == TType.STRING:
        if not isinstance(val, bytes):
            val = val.encode('utf-8')
        outbuf.write(pack_string(val))

    elif ttype == TType.SET or ttype == TType.LIST:
        if isinstance(spec, tuple):
            e_type, t_spec = spec[0], spec[1]
        else:
            e_type, t_spec = spec, None

        val_len = len(val)
        write_list_begin(outbuf, e_type, val_len)
        for e_val in val:
            write_val(outbuf, e_type, e_val, t_spec)

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

        write_map_begin(outbuf, k_type, v_type, len(val))
        for k in iter(val):
            write_val(outbuf, k_type, k, k_spec)
            write_val(outbuf, v_type, val[k], v_spec)

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

            write_field_begin(outbuf, f_type, fid)
            write_val(outbuf, f_type, v, f_container_spec)
        write_field_stop(outbuf)

# -*- coding=utf8 -*-
"""常数定义"""
LISTEN_BACKLOG = 128

READ_BUFFER_SIZE = 65536


class ReadState(object):
    """读状态"""
    aborted = 1
    not_done = 2
    done = 3

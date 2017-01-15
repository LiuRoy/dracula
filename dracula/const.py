# -*- coding=utf8 -*-
"""常数定义"""
import errno

LISTEN_BACKLOG = 1024

READ_BUFFER_SIZE = 64 * 1024

NOT_BLOCKING = (errno.EAGAIN, errno.EWOULDBLOCK)


class ReadState(object):
    """读状态"""
    aborted = 1
    not_done = 2
    done = 3

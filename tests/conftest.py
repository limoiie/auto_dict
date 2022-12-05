import sys


def support_positional_only():
    return sys.version_info >= (3, 8)


def support_literals():
    return sys.version_info >= (3, 8)

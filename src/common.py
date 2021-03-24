#!/usr/bin/env python3

import sys


def error_exit(message: str) -> None:
    sys.exit("{}: error: {}".format(sys.argv[0], message))

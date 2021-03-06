#!/usr/bin/env python

use_builtin_whirlpool = True

import hmac
import datetime

from darklight.aux import whirlpool

try:
    import hashlib
    hashlib.new("whirlpool")
    use_builtin_whirlpool = False
except (ImportError, ValueError):
    pass

def DarkHMAC(psk):
    if use_builtin_whirlpool:
        digest = whirlpool
    else:
        digest = lambda: hashlib.new("whirlpool")

    h = hmac.new(psk, digestmod=digest)

    message = str(datetime.datetime.now().day + 42)
    h.update(message)

    return h.digest()

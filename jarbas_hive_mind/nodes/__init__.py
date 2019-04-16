__author__ = "jarbas"

import base64
import os


def gen_key():
    k = os.urandom(32)
    k = base64.urlsafe_b64encode(k)
    k = "HIVE" + str(k)

    k = k[:-1]
    return k

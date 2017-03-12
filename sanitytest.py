#!/bin/python
#author: tobias mueller 13.6.13
#byteplay test

from sys import version_info
from dis import dis
if version_info.major == 3:
    if version_info.minor < 6:from byteplay import *
    else:from wbyteplay import *
else:from byteplay2 import *
from pprint import pprint

def f(a, b):
    res = a + b
    return res

def g(a, b):
    res = a + b if a < b else b + a
    r = 0
    for a in range(res):
        r += 1
    return r or 2

for x in (f, g):
    #get byte code for f
    c = Code.from_code(x.__code__)
    pprint(c.code)

    #generate byte code
    cnew = c.to_code()

    x.__code__ = cnew
    dis(x)

    print(x(3,5))
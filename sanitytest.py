#!/bin/python
#author: tobias mueller 13.6.13
#byteplay test

from sys import version_info
if version_info.major == 3:from byteplay import *
else:from byteplay2 import *
from pprint import pprint

def f(a, b):
  res = a + b
  return res

#get byte code for f
c = Code.from_code(f.__code__)
pprint(c.code)

#generate byte code
cnew = c.to_code()

f.__code__ = cnew

print(f(3,5))
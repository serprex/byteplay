#!/usr/bin/python

from setuptools import setup, find_packages
from byteplay import __version__ as lib_version

setup(
       name = 'byteplay',
       author='serpex',
       url='https://github.com/serprex/byteplay/',
       version = lib_version,
       py_modules = ['byteplay'],
       zip_safe = True,
       license='LGPL',
       description='bytecode manipulation library')


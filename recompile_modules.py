# recompile_modules: recompile modules with byteplay, utility for test purposes
# Copyright (C) 2006-2010 Noam Yorav-Raphael
# Homepage: http://code.google.com/p/byteplay
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

import sys
import os

from byteplay import *


def printcodelist(codelist, to=sys.stdout):
    """Get a code list. Print it nicely."""

    labeldict = {}
    pendinglabels = []
    for i, (op, arg) in enumerate(codelist):
        if isinstance(op, Label):
            pendinglabels.append(op)
        elif op is SetLineno:
            pass
        else:
            while pendinglabels:
                labeldict[pendinglabels.pop()] = i

    lineno = None
    islabel = False
    for i, (op, arg) in enumerate(codelist):
        if op is SetLineno:
            lineno = arg
            print(file=to)
            continue

        if isinstance(op, Label):
            islabel = True
            continue

        if lineno is None:
            linenostr = ''
        else:
            linenostr = str(lineno)
            lineno = None

        if islabel:
            islabelstr = '>>'
            islabel = False
        else:
            islabelstr = ''

        if op in hasconst:
            argstr = repr(arg)
        elif op in hasjump:
            try:
                argstr = 'to ' + str(labeldict[arg])
            except KeyError:
                argstr = repr(arg)
        elif op in hasarg:
            argstr = str(arg)
        else:
            argstr = ''

        print('%3s     %2s %4d %-20s %s' % (
            linenostr,
            islabelstr,
            i,
            op,
            argstr), file=to)


def recompile(filename, insert_reassembly_stamp=True):
    """Create a .pyc by disassembling the file and assembling it again, printing
    a message that the reassembled file was loaded."""
    # Most of the code here based on the compile.py module.
    import io
    import marshal
    import struct
    import importlib.util

    f = open(filename, 'U', encoding='utf-8')
    try:
        timestamp = int(os.fstat(f.fileno()).st_mtime)
    except AttributeError:
        timestamp = int(os.stat(filename).st_mtime)
    try:
        codestring = f.read()
    except UnicodeDecodeError as exc:
        print("Skipping %s - unsupported encoding." % filename, file=sys.stderr)
        return
    f.close()

    if codestring and codestring[-1] != '\n':
        codestring = codestring + '\n'
    try:
        codeobject = compile(codestring, filename, 'exec')
    except SyntaxError as exc:
        print("Skipping %s - syntax error ((%u:%u) %s)." %
              (filename, exc.lineno, exc.offset if exc.offset is not None else -1, exc.msg), file=sys.stderr)
        return

    cod = Code.from_code(codeobject)
    if cod is None:
        print("Can't recompile", filename)
        return

    if insert_reassembly_stamp:
        message = "reassembled %r imported.\n" % filename
        cod.code[:0] = [  # __import__('sys').stderr.write(message)
            (LOAD_GLOBAL, '__import__'),
            (LOAD_CONST, 'sys'),
            (CALL_FUNCTION, 1),
            (LOAD_ATTR, 'stderr'),
            (LOAD_ATTR, 'write'),
            (LOAD_CONST, message),
            (CALL_FUNCTION, 1),
            (POP_TOP, None),
        ]

    codeobject2 = cod.to_code()
    optimize = -1
    if optimize >= 0:
        cfile = importlib.util.cache_from_source(filename,
                                                 debug_override=not optimize)
    else:
        cfile = importlib.util.cache_from_source(filename)

    mode = importlib._bootstrap._calc_mode(filename)
    cdir = os.path.dirname(cfile)
    os.makedirs(cdir, exist_ok=True)
    fd = os.open(cfile, os.O_CREAT | os.O_WRONLY, mode & 0o666)

    with io.FileIO(fd, 'wb') as fc:
        fc.write(b'\0\0\0\0')
        fc.write(struct.pack('<l', timestamp))
        fc.write(b'\0\0\0\0')
        marshal.dump(codeobject2, fc)
        fc.flush()
        fsize = os.path.getsize(filename)
        fc.seek(0, 0)
        fc.write(importlib.util.MAGIC_NUMBER)
        fc.seek(8, 0)
        fc.write(struct.pack('<l', fsize))


def recompile_all(path, insert_reassembly_stamp=True):
    """recursively recompile all .py files in the directory"""
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for name in files:
                if name.endswith('.py'):
                    filename = os.path.abspath(os.path.join(root, name))
                    print(filename, file=sys.stderr)
                    recompile(filename, insert_reassembly_stamp=insert_reassembly_stamp)
    else:
        filename = os.path.abspath(path)
        recompile(filename, insert_reassembly_stamp=insert_reassembly_stamp)


def main():
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print("""\
Usage: %s dir

Search recursively for *.py in the given directory, disassemble and assemble
them, adding a note when each file is imported.

Use it to test byteplay like this:
> byteplay.py Lib
> make test

Some FutureWarnings may be raised, but that's expected.

Tip: before doing this, check to see which tests fail even without reassembling
them...
""" % sys.argv[0])
        sys.exit(1)
    recompile_all(sys.argv[1])


if __name__ == '__main__':
    main()

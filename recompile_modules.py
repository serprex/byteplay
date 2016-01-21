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
            print >> to
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

        print >> to, '%3s     %2s %4d %-20s %s' % (
            linenostr,
            islabelstr,
            i,
            op,
            argstr)


def recompile(filename):
    """Create a .pyc by disassembling the file and assembling it again, printing
    a message that the reassembled file was loaded."""
    # Most of the code here based on the compile.py module.
    import os
    import imp
    import marshal
    import struct

    f = open(filename, 'U')
    try:
        timestamp = long(os.fstat(f.fileno()).st_mtime)
    except AttributeError:
        timestamp = long(os.stat(filename).st_mtime)
    codestring = f.read()
    f.close()
    if codestring and codestring[-1] != '\n':
        codestring = codestring + '\n'
    try:
        codeobject = compile(codestring, filename, 'exec')
    except SyntaxError:
        print >> sys.stderr, "Skipping %s - syntax error." % filename
        return
    cod = Code.from_code(codeobject)
    message = "reassembled %r imported.\n" % filename
    cod.code[:0] = [ # __import__('sys').stderr.write(message)
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
    fc = open(filename+'c', 'wb')
    fc.write('\0\0\0\0')
    fc.write(struct.pack('<l', timestamp))
    marshal.dump(codeobject2, fc)
    fc.flush()
    fc.seek(0, 0)
    fc.write(imp.get_magic())
    fc.close()

def recompile_all(path):
    """recursively recompile all .py files in the directory"""
    import os
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for name in files:
                if name.endswith('.py'):
                    filename = os.path.abspath(os.path.join(root, name))
                    print >> sys.stderr, filename
                    recompile(filename)
    else:
        filename = os.path.abspath(path)
        recompile(filename)

def main():
    import os
    if len(sys.argv) != 2 or not os.path.exists(sys.argv[1]):
        print """\
Usage: %s dir

Search recursively for *.py in the given directory, disassemble and assemble
them, adding a note when each file is imported.

Use it to test byteplay like this:
> byteplay.py Lib
> make test

Some FutureWarnings may be raised, but that's expected.

Tip: before doing this, check to see which tests fail even without reassembling
them...
""" % sys.argv[0]
        sys.exit(1)
    recompile_all(sys.argv[1])

if __name__ == '__main__':
    main()

#!/usr/bin/env python
import unittest

class Test(unittest.TestCase):
    def test_sane(self):
        code = compile(open("sanitytest.py").read(), "sanitytest.py", "exec")
        exec(code, {"print": lambda x:self.assertEqual(x, 8)}, {})

if __name__ == '__main__':
    unittest.main()
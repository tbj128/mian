from mian.core.project import Project


import unittest


def inc(x):
    return x + 1


class TestStringMethods(unittest.TestCase):

    def test_upper(self):
        self.assertEqual('foo'.upper(), 'FOO')

    def test_isupper(self):
        self.assertTrue('FOO'.isupper())
        self.assertFalse('Foo'.isupper())

    def test_split(self):
        s = 'hello world'
        self.assertEqual(s.split(), ['hello', 'world'])
        # check that s.split fails when the separator is not a string
        with self.assertRaises(TypeError):
            s.split(2)

    # content of test_sample.py

    def test_answer(self):
        self.assertEqual(inc(3), 4)
        self.assertEqual(Project.add_file_name_attr("abc", "cde", "efg"), "abc")


if __name__ == '__main__':
    unittest.main()
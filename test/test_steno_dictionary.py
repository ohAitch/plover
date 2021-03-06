# Copyright (c) 2013 Hesky Fisher
# See LICENSE.txt for details.

"""Unit tests for steno_dictionary.py."""

import os
import stat
import tempfile
import unittest

from plover.steno_dictionary import StenoDictionary, StenoDictionaryCollection


class StenoDictionaryTestCase(unittest.TestCase):

    def test_dictionary(self):
        notifications = []
        def listener(longest_key):
            notifications.append(longest_key)

        d = StenoDictionary()
        self.assertEqual(d.longest_key, 0)

        d.add_longest_key_listener(listener)
        d[('S',)] = 'a'
        self.assertEqual(d.longest_key, 1)
        self.assertEqual(notifications, [1])
        d[('S', 'S', 'S', 'S')] = 'b'
        self.assertEqual(d.longest_key, 4)
        self.assertEqual(notifications, [1, 4])
        d[('S', 'S')] = 'c'
        self.assertEqual(d.longest_key, 4)
        self.assertEqual(d[('S', 'S')], 'c')
        self.assertEqual(notifications, [1, 4])
        del d[('S', 'S', 'S', 'S')]
        self.assertEqual(d.longest_key, 2)
        self.assertEqual(notifications, [1, 4, 2])
        del d[('S',)]
        self.assertEqual(d.longest_key, 2)
        self.assertEqual(notifications, [1, 4, 2])
        self.assertEqual(d.reverse_lookup('c'), [('S', 'S')])
        self.assertEqual(d.casereverse_lookup('c'), ['c'])
        d.clear()
        self.assertEqual(d.longest_key, 0)
        self.assertEqual(notifications, [1, 4, 2, 0])
        self.assertEqual(d.reverse_lookup('c'), [])
        self.assertEqual(d.casereverse_lookup('c'), [])

        d.remove_longest_key_listener(listener)
        d[('S', 'S')] = 'c'
        self.assertEqual(d.longest_key, 2)
        self.assertEqual(notifications, [1, 4, 2, 0])

    def test_dictionary_collection(self):
        d1 = StenoDictionary()
        d1[('S',)] = 'a'
        d1[('T',)] = 'b'
        d1.path = 'd1'
        d2 = StenoDictionary()
        d2[('S',)] = 'c'
        d2[('W',)] = 'd'
        d2.path = 'd2'
        dc = StenoDictionaryCollection([d2, d1])
        self.assertEqual(dc.lookup(('S',)), 'c')
        self.assertEqual(dc.lookup(('W',)), 'd')
        self.assertEqual(dc.lookup(('T',)), 'b')
        f = lambda k, v: v == 'c'
        dc.add_filter(f)
        self.assertIsNone(dc.lookup(('S',)))
        self.assertEqual(dc.raw_lookup(('S',)), 'c')
        self.assertEqual(dc.lookup(('W',)), 'd')
        self.assertEqual(dc.lookup(('T',)), 'b')
        self.assertEqual(dc.reverse_lookup('c'), [('S',)])

        dc.remove_filter(f)
        self.assertEqual(dc.lookup(('S',)), 'c')
        self.assertEqual(dc.lookup(('W',)), 'd')
        self.assertEqual(dc.lookup(('T',)), 'b')

        self.assertEqual(dc.reverse_lookup('c'), [('S',)])

        dc.set(('S',), 'e')
        self.assertEqual(dc.lookup(('S',)), 'e')
        self.assertEqual(d2[('S',)], 'e')

        dc.set(('S',), 'f', path='d1')
        self.assertEqual(dc.lookup(('S',)), 'e')
        self.assertEqual(d1[('S',)], 'f')
        self.assertEqual(d2[('S',)], 'e')

        # Iterating on a StenoDictionaryCollection is
        # the same as iterating on its dictionaries' paths.
        self.assertEqual(list(dc), ['d2', 'd1'])

        # Test get and [].
        self.assertEqual(dc.get('d1'), d1)
        self.assertEqual(dc['d1'], d1)
        self.assertEqual(dc.get('invalid'), None)
        with self.assertRaises(KeyError):
            dc['invalid']

    def test_dictionary_collection_writeable(self):
        d1 = StenoDictionary()
        d1[('S',)] = 'a'
        d1[('T',)] = 'b'
        d2 = StenoDictionary()
        d2[('S',)] = 'c'
        d2[('W',)] = 'd'
        d2.readonly = True
        dc = StenoDictionaryCollection([d2, d1])
        self.assertEqual(dc.first_writable(), d1)
        dc.set(('S',), 'A')
        self.assertEqual(d1[('S',)], 'A')
        self.assertEqual(d2[('S',)], 'c')

    def test_dictionary_collection_longest_key(self):

        k1 = ('S',)
        k2 = ('S', 'T')
        k3 = ('S', 'T', 'R')

        dc = StenoDictionaryCollection()
        self.assertEqual(dc.longest_key, 0)

        d1 = StenoDictionary()
        d1._path = 'd1'
        d1[k1] = 'a'

        dc.set_dicts([d1])
        self.assertEqual(dc.longest_key, 1)

        d1[k2] = 'a'
        self.assertEqual(dc.longest_key, 2)

        d2 = StenoDictionary()
        d2._path = 'd2'
        d2[k3] = 'c'

        dc.set_dicts([d2, d1])
        self.assertEqual(dc.longest_key, 3)

        del d1[k2]
        self.assertEqual(dc.longest_key, 3)

        dc.set_dicts([d1])
        self.assertEqual(dc.longest_key, 1)

        dc.set_dicts([])
        self.assertEqual(dc.longest_key, 0)

    def test_casereverse_del(self):
        d = StenoDictionary()
        d[('S-G',)] = 'something'
        d[('SPH-G',)] = 'something'
        self.assertEqual(d.casereverse_lookup('something'), ['something'])
        del d[('S-G',)]
        self.assertEqual(d.casereverse_lookup('something'), ['something'])
        del d[('SPH-G',)]
        self.assertEqual(d.casereverse_lookup('something'), [])

    def test_reverse_lookup(self):
        dc = StenoDictionaryCollection()

        d1 = StenoDictionary()
        d1[('PWAOUFL',)] = 'beautiful'
        d1[('WAOUFL',)] = 'beautiful'

        d2 = StenoDictionary()
        d2[('PW-FL',)] = 'beautiful'

        d3 = StenoDictionary()
        d3[('WAOUFL',)] = 'not beautiful'

        # Simple test.
        dc.set_dicts([d1])
        self.assertCountEqual(dc.reverse_lookup('beautiful'),
                              [('PWAOUFL',), ('WAOUFL',)])

        # No duplicates.
        d2_copy = StenoDictionary()
        d2_copy.update(d2)
        dc.set_dicts([d2_copy, d2])
        self.assertCountEqual(dc.reverse_lookup('beautiful'),
                              [('PW-FL',)])

        # Don't stop at the first dictionary with matches.
        dc.set_dicts([d2, d1])
        self.assertCountEqual(dc.reverse_lookup('beautiful'),
                              [('PWAOUFL',), ('WAOUFL',), ('PW-FL',)])

        # Ignore keys overriden by a higher precedence dictionary.
        dc.set_dicts([d3, d2, d1])
        self.assertCountEqual(dc.reverse_lookup('beautiful'),
                              [('PWAOUFL',), ('PW-FL',)])

    def test_dictionary_enabled(self):
        dc = StenoDictionaryCollection()
        d1 = StenoDictionary()
        d1.path = 'd1'
        d1[('TEFT',)] = 'test1'
        d1[('TEFGT',)] = 'Testing'
        d2 = StenoDictionary()
        d2[('TEFT',)] = 'test2'
        d2[('TEFT','-G')] = 'Testing'
        d2.path = 'd2'
        dc.set_dicts([d2, d1])
        self.assertEqual(dc.lookup(('TEFT',)), 'test2')
        self.assertEqual(dc.raw_lookup(('TEFT',)), 'test2')
        self.assertEqual(dc.casereverse_lookup('testing'), ['Testing'])
        self.assertCountEqual(dc.reverse_lookup('Testing'), [('TEFGT',), ('TEFT', '-G')])
        d2.enabled = False
        self.assertEqual(dc.lookup(('TEFT',)), 'test1')
        self.assertEqual(dc.raw_lookup(('TEFT',)), 'test1')
        self.assertEqual(dc.casereverse_lookup('testing'), ['Testing'])
        self.assertCountEqual(dc.reverse_lookup('Testing'), [('TEFGT',)])
        d1.enabled = False
        self.assertEqual(dc.lookup(('TEST',)), None)
        self.assertEqual(dc.raw_lookup(('TEFT',)), None)
        self.assertEqual(dc.casereverse_lookup('testing'), None)
        self.assertCountEqual(dc.reverse_lookup('Testing'), [])

    def test_dictionary_readonly(self):
        class FakeDictionary(StenoDictionary):
            def _load(self, filename):
                pass
        tf = tempfile.NamedTemporaryFile(delete=False)
        try:
            tf.close()
            d = FakeDictionary.load(tf.name)
            # Writable file: not readonly.
            self.assertFalse(d.readonly)
            # Readonly file: readonly dictionary.
            os.chmod(tf.name, stat.S_IREAD)
            d = FakeDictionary.load(tf.name)
            self.assertTrue(d.readonly)
        finally:
            # Deleting the file will fail on Windows
            # if we don't restore write permission.
            os.chmod(tf.name, stat.S_IWRITE)
            os.unlink(tf.name)
        # Assets are always readonly.
        d = FakeDictionary.load('asset:plover:assets/main.json')
        self.assertTrue(d.readonly)

import os
import sys
import unittest

filename = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join (filename, '..'))

from process import SubsLoader, DecodeError, LoadError, \
    ParseError, ParserNotFoundError

from parsers import SrtParser

PARSERS = [SrtParser]

ENCODINGS = ['utf-8',
             'utf-16'
             'windows-1252',
             'windows-1256',
             'windows-1250',
             'iso-8859-2',
             'maclatin2',
             'IBM852',
             'iso-8859-15',
             'macroman',
             'ibm1140',
             'IBM850',
             'windows-1251',
             'cyrillic',
             'maccyrillic',
             'koi8_r',
             'IBM866']

SUBS_PATH = os.path.join(os.path.dirname(__file__), 'subfiles')
TESTFILES = [os.path.join(SUBS_PATH, 'test_arabic.srt'),
             os.path.join(SUBS_PATH,'test_random.srt'),
             os.path.join(SUBS_PATH,'test_tags.srt'),
             os.path.join(SUBS_PATH,'test_null_chars.srt'),
             os.path.join(SUBS_PATH,'test_utf16.srt')]

class LoaderTestCase(unittest.TestCase):
    def setUp(self):
        self.subsloader = SubsLoader(PARSERS, ENCODINGS)

    def test_loader(self):
        for subpath in TESTFILES:
            sublist, encoding = self.subsloader.load(subpath)
            self.assertTrue(len(sublist) > 1, 'parsed subtitle list has to have at least 2 entries')
            self.assertTrue(encoding != '', 'cannot detect encoding')

    def test_utf16(self):
        self.subsloader.change_encodings(['utf-8','utf-16'])
        sublist, encoding = self.subsloader.load(os.path.join(SUBS_PATH,'test_utf16.srt'))
        self.assertTrue(len(sublist) > 1, 'parsed subtitle list has to have at least 2 entries')
        self.assertTrue(encoding != '', 'cannot detect encoding')
        self.assertTrue(encoding == 'utf-16', 'utf-16 file has to be decoded with utf-16 encoding')

    def test_invalid_path_local(self):
        self.assertRaises(LoadError, self.subsloader.load, 'dsadsa')

    def test_invalid_path_remote(self):
        self.assertRaises(LoadError, self.subsloader.load, 'http://dsakldmskla.srt')

    def test_invalid_encoding(self):
        self.subsloader.change_encodings(['utf-8'])
        self.assertRaises(DecodeError, self.subsloader.load, os.path.join(SUBS_PATH,'test_arabic.srt'))

    def test_invalid_file(self):
        self.assertRaises(ParseError, self.subsloader.load, os.path.join(SUBS_PATH,'test_invalid_file.srt'))

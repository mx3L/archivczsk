import os
import traceback
from urllib2 import URLError, HTTPError

from utils import load, decode
from parsers.baseparser import ParseError, NoSubtitlesParseError

class ParserNotFoundError(Exception):
    pass

class DecodeError(Exception):
    pass

class LoadError(Exception):
    pass

class SubsLoader(object):
    def __init__(self, parsers_cls, encodings=None):
        self._parsers = [parser_cls() for parser_cls in parsers_cls]
        self._encodings = ['utf-8']
        if encodings:
            self._encodings = encodings
        self._row_parsing = False

    def toggle_row_parsing(self):
        if self._row_parsing:
            self.set_row_parsing(False)
        else:
            self.set_row_parsing(True)

    def set_row_parsing(self, val):
        for parser in self._parsers:
            parser.rowParse = val
        if val:
            print '[SubsLoader] setting row parsing for Parsers'
            self._row_parsing = True
        else:
            print '[SubsLoader] setting block parsing for Parsers'
            self._row_parsing = False

    def change_encodings(self, encodings):
        print '[SubsLoader] changing encoding group: ', encodings
        self._encodings = encodings

    def change_encoding(self, text, current_encoding):
        try:
            decoded_text, encoding = decode(text, self._encodings, current_encoding)
        except Exception:
            traceback.print_exc()
            print '[SubsLoader] cannot decode subtitles'
            raise DecodeError()
        return decoded_text, encoding

    def load(self, subfile, current_encoding=None):
        print '[SubsLoader] loading "{0}"'.format(subfile)
        while 1:
            decoded_text, encoding = self._process_path(subfile, current_encoding)
            try:
                sublist = self._parse(decoded_text, os.path.splitext(subfile)[1])
            except NoSubtitlesParseError:
                # this could mean that subtitles file was decoded but
                # with not right encoding, we try to use other encodings
                if current_encoding == self._encodings[-1]:
                    raise
                print '[SubsLoader] no subtitles parsed, will try different encoding'
                current_encoding = encoding
                continue
            print '[SubsLoader] "{0}" - succesfully loaded'.format(subfile),
            return sublist, encoding

    def _process_path(self, subfile, current_encoding=None) :
        try:
            text = load(subfile)
        except (URLError, HTTPError, IOError) as e:
            print '[SubsLoader] "{0}" ,cannot load: {1}'.format(subfile, e)
            raise LoadError(subfile)
        try:
            decoded_list, encoding = decode(text, self._encodings, current_encoding)
        except Exception as e:
            print '[SubsLoader] "{0}" cannot decode: {1}'.format(subfile, e)
            raise DecodeError(subfile)
        return decoded_list, encoding

    def _parse(self, text, ext=None):
        print '[SubsLoader] looking for "{0}" parser'.format(ext)
        for parser in self._parsers:
            if not ext:
                print '[SubsLoader] extension not set, parsing without extension..'
                break
            if parser.canParse(ext):
                print '[SubsLoader] found [{0}]'.format(parser)
                print '[SubsLoader][{0}] parsing...'.format(parser)
                try:
                    return parser.parse(text)
                except ParseError as e:
                    print '[SubsLoader][{0}]: {1}'.format(parser,e)
                    raise
        for parser in self._parsers:
            print '[SubsLoader] trying parsing with [{0}]'.format(parser)
            try:
                return parser.parse(text)
            except NoSubtitlesParseError as e:
                if parser == self._parsers[-1]:
                    raise
                continue
            except ParseError as e:
                print '[SubsLoader][{0}]: {1}'.format(parser,e)
                continue
        raise ParserNotFoundError(str(ext))

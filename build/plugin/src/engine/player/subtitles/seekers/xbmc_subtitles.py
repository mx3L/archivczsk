'''
Created on Feb 10, 2014

@author: marko
'''
import os

from seeker import BaseSeeker
from utilities import LANGUAGES

def _(text):
    return text

class XBMCSubtitlesAdapter(BaseSeeker):
    module = None

    def __init__(self, tmp_path, download_path, settings=None, settings_provider=None, captcha_cb=None, delay_cb=None, message_cb=None):
        assert self.module is not None,'you have to provide xbmc-subtitles module'
        logo = os.path.join(os.path.dirname(self.module.__file__), 'logo.png')
        BaseSeeker.__init__(self, tmp_path, download_path, settings, settings_provider, logo)
        self.module.captcha_cb = captcha_cb
        self.module.delay_cb = delay_cb
        self.module.message_cb = message_cb
        self.lang1 = self.lang2 = self.lang3 = ""
        try:
            self.lang1 = self.get_full_lang_name(self.supported_langs[0])
            self.lang2 = self.get_full_lang_name(self.supported_langs[1])
            self.lang3 = self.get_full_lang_name(self.supported_langs[2])
        except IndexError:
            pass

    def get_full_lang_name(self, lang):
        for x in LANGUAGES:
            if lang == x[2]:
                return x[0]

    def _search(self, title, filepath, lang, season, episode, tvshow, year):
        print title, filepath, season, episode, tvshow, year
        if filepath is None:
            file_original_path = title
        else:
            file_original_path = filepath
        title = title if title else ""
        season = season if season else ""
        episode = episode if episode else ""
        tvshow = tvshow if tvshow else ""
        year = year if year else ""
        lang1 = lang2 = lang3 = ""
        if lang is not None:
            try:
                lang1 = self.get_full_lang_name(lang[0])
                lang2 = self.get_full_lang_name(lang[1])
                lang3 = self.get_full_lang_name(lang[2])
            except IndexError:
                pass
        else:
            lang1 = self.lang1
            lang2 = self.lang2
            lang3 = self.lang3
        print str(self), 'using langs',lang1, lang2, lang3
        self.module.settings_provider = self.settings_provider
        # Standard output -
        # subtitles list
        # session id (e.g a cookie string, passed on to download_subtitles),
        # message to print back to the user
        # return subtitlesList, "", msg
        subtitles_list, session_id, msg = self.module.search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp=False, rar=False, lang1=lang1, lang2=lang2, lang3=lang3, stack=None)
        return {'list':subtitles_list,'session_id':session_id,'msg':msg}

    def _download(self, subtitles, selected_subtitle, path=None):
        subtitles_list = subtitles['list']
        session_id = subtitles['session_id']
        pos = subtitles_list.index(selected_subtitle)
        zip_subs = os.path.join(self.tmp_path, selected_subtitle['filename'])
        tmp_sub_dir = self.tmp_path
        if path is not None:
            sub_folder = path
        else:
            sub_folder = self.download_path
        # Standard output -
        # True if the file is packed as zip: addon will automatically unpack it.
        # language of subtitles,
        # Name of subtitles file if not packed (or if we unpacked it ourselves)
        # return False, language, subs_file
        compressed, language, file = self.module.download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id)
        if compressed !=False:
            if compressed =="":
                compressed = "zip"
            else:
                compressed = file
            file = zip_subs
        else:
            file = os.path.join(sub_folder, file)
        return  compressed, file

    def close(self):
        try:
            del self.module.captcha_cb
            del self.module.message_cb
            del self.module.delay_cb
            del self.module.settings_provider
        except Exception:
            pass

try:
    from Titulky import titulkycom
except ImportError as e:
    print e
    titulkycom = None

class TitulkyComSeeker(XBMCSubtitlesAdapter):
    module = titulkycom
    provider_name = 'Titulky.com'
    supported_langs = ['sk', 'cs']
    default_settings = {'Titulkyuser':{'label':_("Username"), 'type':'text', 'default':"",'pos':0},
                                       'Titulkypass':{'label':_("Password"), 'type':'text', 'default':"",'pos':1}, }

try:
    from Edna import edna
except ImportError as e:
    print e
    edna = None

class EdnaSeeker(XBMCSubtitlesAdapter):
    module = edna
    provider_name = 'Edna.cz'
    supported_langs = ['sk', 'cs']
    default_settings={}

try:
    from OpenSubtitles import opensubtitles
except ImportError as e:
    print e
    opensubtitles = None

class OpenSubtitlesSeeker(XBMCSubtitlesAdapter):
    module = opensubtitles
    provider_name = 'OpenSubtitles'
    supported_langs =supported_langs = ["en",
                                            "fr",
                                            "hu",
                                            "cs",
                                            "pl" ,
                                            "sk" ,
                                            "pt",
                                            "pt-br",
                                            "es",
                                            "el",
                                            "ar",
                                            'sq',
                                            "hy",
                                            "ay",
                                            "bs",
                                            "bg",
                                            "ca",
                                            "zh",
                                            "hr",
                                            "da",
                                            "nl",
                                            "eo",
                                            "et",
                                            "fi",
                                            "gl",
                                            "ka",
                                            "de",
                                            "he",
                                            "hi",
                                            "is",
                                            "id",
                                            "it",
                                            "ja",
                                            "kk",
                                            "ko",
                                            "lv",
                                            "lt",
                                            "lb",
                                            "mk",
                                            "ms",
                                            "no",
                                            "oc",
                                            "fa",
                                            "ro",
                                            "ru",
                                            "sr",
                                            "sl",
                                            "sv",
                                            "th",
                                            "tr",
                                            "uk",
                                            "vi"]
    default_settings={}




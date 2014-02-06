import os, sys
import time
import unittest
filename = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join (filename, '..'))

from seek import SubsSeeker

class TestSeeker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.settings = {}
        cls.tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'subcache')
        cls.download_path = cls.tmp_path
        cls.provider_class = None

    def captcha_cb(self, url):
        return raw_input('visit url:%s\ntype captcha:'%url)

    def message_cb(self, text):
        print text

    def delay_cb(self, seconds):
        for i in xrange(seconds):
            print i,'second'
            time.sleep(1)

    def setUp(self):
        download_path = tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'subcache')
        settings= {'Titulky.com':{'Titulkypass':'','Titulkyuser':''}}
        self.seeker = SubsSeeker(download_path, tmp_path, self.captcha_cb, self.delay_cb, self.message_cb, settings=settings)

    def testSearchSimple(self):
        subtitles = self.seeker.getSubtitles(title='True Detective', langs=['cs','sk'])
        self.assertTrue(len(subtitles)>0, 'there should be at least one subtitle found')

    def testDownloadSimple(self):
        subtitles = self.seeker.getSubtitles(title='True Detective', langs=['cs','sk','en'])
        subtitle = self.seeker.getSubtitlesList(subtitles)[-1]
        self.seeker.downloadSubtitle(subtitle, subtitles)



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
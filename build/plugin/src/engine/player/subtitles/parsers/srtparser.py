import time
import os
import re
import traceback
from baseparser import BaseParser



class SrtParser(BaseParser):
    parsing = ('.srt')

    def parse(self, text):
        try:
            subdict = self.srt_to_dict(text)
        except Exception:
            print traceback.print_exc()
            print '[srtParser] cannot parse srt subtitles'
            return
        return subdict
    
    def srt_time_to_pts(self, time):
        split_time = time.split(',')
        major, minor = (split_time[0].split(':'), split_time[1])
        return long((int(major[0]) * 3600 + int(major[1]) * 60 + int(major[2])) * 1000 + int(minor))

    def srt_to_dict(self, srtText):
        subs = []
        for s in re.sub('\s*\n\n\n*', '\n\n', re.sub('\r\n', '\n', srtText)).split('\n\n'):
            st = s.split('\n')
            if len(st) >= 3:
                split = st[1].split(' --> ')
                startTime = self.srt_time_to_pts(split[0].strip())
                endTime = self.srt_time_to_pts(split[1].strip())
                text = '\n'.join(j for j in st[2:len(st)])
                #print text
                subs.append(self.createSub(text, startTime, endTime))
        return subs
    
parserClass = SrtParser

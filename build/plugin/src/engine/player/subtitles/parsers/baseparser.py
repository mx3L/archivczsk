import os

class BaseParser():
    parsing = ()
    @classmethod
    def canParse(cls, filename):
        return os.path.splitext(filename)[1] in cls.parsing
    
    def createSub(self, text, start, end):
        """
        @param text: text of subtitle 
        @param start: start time of subtitle in ms
        @param end: end time of subtitle in ms
        
        """
        duration = long(end - start)
        start = long(start * 90)
        end = long(end * 90)
        return {'text':text, 'start':start, 'end':end, 'duration':duration}
       
    def parse(self, text):
        """
        parses subtitles from text into list of sub dicts
        and returns this list
        
        """
        return []

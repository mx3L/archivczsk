import os
import re

class ParseError(Exception):
    pass

class SubStyler(object):

    HEX_COLORS = {
            "red":"#FF0000",
            "white":"#FFFFFF",
            "cyan":"#00FFFF",
            "silver":"#C0C0C0",
            "blue": "#0000FF",
            "gray":"#808080",
            "grey": "#808080",
            "darkblue": "#0000A0",
            "black": "#000000",
            "lightblue":"#ADD8E6",
            "orange":"#FFA500",
            "purple":"#800080",
            "brown":"#A52A2A",
            "yellow":"#FFFF00",
            "maroon":"#800000",
            "lime":"#00FF00",
            "green":"#008000",
            "magenta":"#FF00FF",
            "olive":"#808000"}

    def italicStart(self, text):
        return text.lower().find('<i>') != -1

    def italicEnd(self, text):
        return text.lower().find('</i>') != -1

    def boldStart(self, text):
        return text.lower().find('<b>') != -1

    def boldEnd(self, text):
        return text.lower().find('</b>') != -1

    def underlineStart(self, text):
        return text.lower().find('<u>') != -1

    def underlineEnd(self, text):
        return text.lower().find('</u>') != -1

    def removeTags(self, text):
        return re.sub('<[^>]*>', '', text)

    def getStyle(self, text):
        if self.italicStart(text):
            return 'italic'
        elif self.boldStart(text):
            return 'bold'
        return 'regular'


    def getColor(self, text):
        color = 'default'
        colorMatch = re.search('<[Ff]ont [Cc]olor=(.+?)>', text, re.DOTALL)
        colorText = colorMatch and colorMatch.group(1) or color
        colorText = colorText.replace("'", "").replace('"', '')
        hexColor = re.search("(\#[0-9,a-f,A-F]{6})", colorText)
        if hexColor:
            color = hexColor.group(1)[1:]
        else:
            try:
                color = self.HEX_COLORS[colorText.lower()][1:]
            except KeyError:
                pass
        return color


class SubLineStyler(SubStyler):
    def getStyle(self, text, style):
        newStyle = style
        endTag = False
        # looking for end tag
        if style == 'italic':
            endTag = self.italicEnd(text)
        elif style == 'bold':
            endTag = self.boldEnd(text)
        elif style == 'underline':
            endTag = True
        # looking for start/end tag on the same line
        else:
            if self.italicStart(text):
                style = 'italic'
                newStyle = style
                endTag = self.italicEnd(text)
            elif self.boldStart(text):
                style = 'bold'
                newStyle = style
                endTag = self.boldEnd(text)
            elif self.underlineStart(text):
                style = 'regular'
                newStyle = style

        if endTag:
            newStyle = 'regular'
        return style, newStyle

    def getColor(self, text, color):
        newColor = color
        if color != 'default':
            if text.find('</font>') != -1 or text.find('</Font>') != -1:
                newColor = 'default'
        else:
            colorMatch = re.search('<[Ff]ont [Cc]olor=(.+?)>', text, re.DOTALL)
            colorText = colorMatch and colorMatch.group(1) or color
            colorText = colorText.replace("'", "").replace('"', '')
            hexColor = re.search("(\#[0-9,a-f,A-F]{6})", colorText)
            if hexColor:
                color = hexColor.group(1)[1:]
            else:
                try:
                    color = self.HEX_COLORS[colorText.lower()][1:]
                except KeyError:
                    pass
            if text.find('</font>') != -1 or text.find('</Font>') != -1:
                newColor = 'default'
            else:
                newColor = color
        return color, newColor


subStyler = SubStyler()
subLineStyler = SubLineStyler()

class BaseParser(object):
    parsing = ()

    @classmethod
    def canParse(cls, filename):
        return os.path.splitext(filename)[1] in cls.parsing

    def __init__(self, rowParse=False):
        self.rowParse = rowParse

    def __str__(self):
        return self.__class__.__name__

    def createSub(self, text, start, end):
        """
        @param text: text of subtitle
        @param start: start time of subtitle in ms
        @param end: end time of subtitle in ms

        """
        duration = long(end - start)
        start = long(start * 90)
        end = long(end * 90)
        if self.rowParse:
            rows = []
            style = newStyle = 'regular'
            color = newColor = 'default'
            for rowText in text.split('\n'):
                rowStyle, newStyle = subLineStyler.getStyle(rowText, newStyle)
                rowColor, newColor = subLineStyler.getColor(rowText, newColor)
                rowText = subLineStyler.removeTags(rowText)
                rows.append({"text":rowText, "style":rowStyle, 'color':rowColor})
            return {'rows':rows, 'start':start, 'end':end, 'duration':duration}
        else:
            style = subStyler.getStyle(text)
            color = subStyler.getColor(text)
            text = subStyler.removeTags(text)
            return {'text':text, 'style':style, 'color':color, 'start':start, 'end':end, 'duration':duration}

    def parse(self, text):
        """
        parses subtitles from text into list of sub dicts
        and returns this list

        """
        text =text.strip()
        text = text.replace('\x00','')
        return self._parse(text)

    def _parse(self, text):
        return []
import re
from Components.Converter.Converter import Converter
from Components.Element import cached

def getEscapeColorFromHexString(color):
        if color.startswith('#'):
            color = color[1:]
        if len(color) == 6:
            color = "00"+ color
        if len(color) != 8:
            print 'invalid color %s'
            return getEscapeColorFromHexString("00ffffff")
        colorsarray = []
        for x in color:
            if x == "0":
                # cannot pass non-printable null to string :(
                c = "1"
            else:
                c = x
            colorsarray.append(chr(int(c, 16)))
        return ''.join(colorsarray)



class ACZSKKodiToE2List(Converter):
    COLORS = {
       "red":"FF0000",
       "white":"FFFFFF",
       "cyan":"00FFFF",
       "silver":"C0C0C0",
       "blue": "0000ff",
       "gray":"808080",
       "grey": "808080",
       "darkblue": "0000A0",
       "black": "000000",
       "lightblue":"ADD8E6",
       "orange":"FFA500",
       "purple":"800080",
       "brown":"A52A2A",
       "yellow":"FFFF00",
       "maroon":"800000",
       "lime":"00FF00",
       "green":"008000",
       "magenta":"FF00FF",
       "olive":"808000"
    }
    
    TYPE_TEXT = 0
    TYPE_COLOR_CODES = 1
    
    def __init__(self, arguments):
        Converter.__init__(self, arguments)
        self.italicColor =  getEscapeColorFromHexString("FFFFFF")
        self.boldColor = getEscapeColorFromHexString("FFFFFF")
        self.defaultColor = getEscapeColorFromHexString("FFFFFF")
        self.indexes = []
        arguments = arguments.split(',')
        for arg in arguments:
            if arg.startswith("Index"):
                self.indexes = [int(i) for i in arg.split(':')[1].split('.')]
                print "[KodiToE2List] self.indexes = %s"%str(self.indexes)
        if "ColorCodes" in arguments:
            self.type = self.TYPE_COLOR_CODES
            print "[KodiToE2List] self.type = self.TYPE_COLOR_CODES"
        else:
            self.type = self.TYPE_TEXT
            print "[KodiToE2List] self.type = self.TYPE_TEXT"
        if self.type == self.TYPE_COLOR_CODES:
            for arg in arguments:
                if arg.split(':')[0] == "Bold":
                    self.boldColor  = getEscapeColorFromHexString(arg.split(':')[1])
                elif arg.split(':')[0] == "Italic":
                    self.italicColor = getEscapeColorFromHexString(arg.split(':')[1])
                elif arg.split(':')[0] == "Default":
                    self.defaultColor = getEscapeColorFromHexString(arg.split(':')[1])
                    

    def changed(self, what):
        if what[0] == self.CHANGED_SPECIFIC and what[1] == "style":
            pass
        self.downstream_elements.changed(what)
        
    def getList(self):
        slist = self.source.list
        clist = []
        for e in slist:
            ecpy = list(e)
            for i in self.indexes:
                ecpy[i] = self.getText(e[i])
            clist.append(tuple(ecpy))
        return clist
    list = property(getList)
        
    def selectionChanged(self, index):
        self.source.selectionChanged(index)

    @cached
    def getCurrent(self):
        if self.source is None or self.index is None or self.index >= len(self.source.list):
            return None
        return self.source.list[self.index]

    current = property(getCurrent)

    # pass through: getIndex / setIndex to master
    @cached
    def getIndex(self):
        if self.master is None:
            return None
        return self.master.index

    def setIndex(self, index):
        if self.master is not None:
            self.master.index = index

    index = property(getIndex, setIndex)
    
    @cached
    def getStyle(self):
        return self.source.style

    def setStyle(self, style):
        self.source.style = style
            
    style = property(getStyle)

    def entry_changed(self, index):
        self.downstream_elements.entry_changed(index)
        
    def getText(self, text):
        def uppercase(match):
            return match.group('text').upper()

        def lowercase(match):
            return match.group('text').lower()

        def customColor(match):
            if self.type == self.TYPE_TEXT:
                return match.group('text')
            color = match.group('color').lower()
            if color in self.COLORS:
                ftext = '\\c%s%s\\c%s' % (getEscapeColorFromHexString(self.COLORS[color]), match.group('text'), self.defaultColor)
            else:
                ftext = '\\c%s%s' % (self.defaultColor, match.group('text'))
            return ftext

        def boldColor(match):
            if self.type == self.TYPE_TEXT:
                return match.group('text')
            return '\\c%s%s\\c%s' % (self.boldColor, match.group('text'), self.defaultColor)

        def italicColor(match):
            if self.type == self.TYPE_TEXT:
                return match.group('text')
            return '\\c%s%s\\c%s' % (self.italicColor, match.group('text'), self.defaultColor)
        
        text = re.sub(r'\[UPPERCASE\](?P<text>.+?)\[/UPPERCASE\]', uppercase, text)
        text = re.sub(r'\[LOWERCASE\](?P<text>.+?)\[/LOWERCASE\]', lowercase, text)
        text = re.sub(r'\[COLOR\ (?P<color>[^\]]+)\](?P<text>.+?)\[/COLOR\]', customColor, text)
        text = re.sub(r'\[B\](?P<text>.+?)\[\/B\]', boldColor, text)
        text = re.sub(r'\[I\](?P<text>.+?)\[\/I\]', italicColor, text)
        text = text.replace('[CR]','\n')
        return text

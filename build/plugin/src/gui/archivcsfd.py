##################################
# big thanks to @mik9
##################################

import os
import traceback
import re
import urllib, urllib2


from enigma import ePicLoad
from random import *
from Components.config import config
from Screens.Screen import Screen
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ScrollLabel import ScrollLabel
from Components.Button import Button
from Components.AVSwitch import AVSwitch
from Components.MenuList import MenuList
from Components.ProgressBar import ProgressBar
from Components.Pixmap import Pixmap
from twisted.web.client import downloadPage
from Plugins.Extensions.archivCZSK import _, log, settings
from Plugins.Extensions.archivCZSK.compat import eConnectCallback
from Plugins.Extensions.archivCZSK.engine.tools.util import toString


class ArchivCSFD(Screen):
    def __init__(self, session, eventName, year, args = None):
        try:
            Screen.__init__(self, session)
            self.eventName = eventName
            self["poster"] = Pixmap()
            self.picload = ePicLoad()
            #self.picload.PictureData.get().append(self.paintPosterPixmapCB)
            # OE2.0 - OE2.5 compatibility
            self.picload_conn = eConnectCallback(self.picload.PictureData, self.paintPosterPixmapCB)
            self["stars"] = ProgressBar()
            self["starsbg"] = Pixmap()
            self["stars"].hide()
            self["starsbg"].hide()
            self["poster"].hide()
            
            self.ratingstars = -1
            #self["titlelabel"] = Label("CSFD Lite")
            self["detailslabel"] = ScrollLabel("")
            self["extralabel"] = ScrollLabel("")
            self["statusbar"] = Label("")
            self["ratinglabel"] = Label("")
            self["baseFilmInfo"] = Label("")
            self.resultlist = []
            self["menu"] = MenuList(self.resultlist)
            self["menu"].hide()

            self["detailslabel"].hide()
            self["baseFilmInfo"].hide()
            self["key_red"] = Button("Exit")
            self["key_green"] = Button("")
            self["key_yellow"] = Button("")
            self["key_blue"] = Button("")
        
            # 0 = multiple query selection menu page
            # 1 = movie info page
            # 2 = extra infos page
            self.Page = 0

            self["actions"] = ActionMap(["OkCancelActions", "ColorActions", "MovieSelectionActions", "DirectionActions"],
            {
                "ok": self.showDetails,
                #"cancel": self.close,
                "cancel": self.__onClose,
                "down": self.pageDown,
                "up": self.pageUp,
                #"right": self.pageDown,
                #"left": self.pageUp,
                #"red": self.close,
                "red": self.__onClose,
                "green": self.showMenu,
                "yellow": self.showDetails,
                "blue": self.showExtras,
                #"contextMenu": self.openChannelSelection,
                "showEventInfo": self.showDetails
            }, -1)

            self.rokEPG = year
        
            self.getCSFD()
        except:
            log.logError("Init ArchivCSFD failed.\n%s"%traceback.format_exc())
            #raise

    def __onClose(self):
        # OE2.0 - OE2.5 compatibility
        # picload_conn this must be, if not than crash system
        del self.picload_conn
        del self.picload
        self.close()

    def toInt(self, s):
        try:
            return int(s)
        except:
            return 0

    def removeDiacritics(self, text):
        searchExp = text
        try:
            import unicodedata
            tmp = unicode(searchExp, "utf-8")
            
            tmp = ''.join((c for c in unicodedata.normalize('NFD', tmp) 
                                        if unicodedata.category(c) != 'Mn')).encode('utf-8')
            return tmp
        except:
            log.logError("ArchivCSFD remove diacritics failed.\n%s"%traceback.format_exc())
            return searchExp
    def odstraneniTagu(self, upravovanytext):
        self.htmltags = re.compile('<.*?>')
        upravovanytext = self.htmltags.sub('', upravovanytext)
        upravovanytext = upravovanytext.replace('&amp;', '&').replace('&nbsp;', ' ')
        return upravovanytext
    def hledejVse(self, retezec, celytext):
        maska = re.compile(retezec, re.DOTALL)
        vysledky = maska.findall(celytext)
        return vysledky
    def najdi(self, retezec, celytext):
        maska = re.compile(retezec, re.DOTALL)
        vysledek = maska.findall(celytext)
        vysledek = vysledek[0] if vysledek else ""
        return vysledek
    def odstraneniInterpunkce(self, upravovanytext):
        interpunkce = ',<.>/?;:"[{]}`~!@#$%^&*()-_=+|'
        for znak in interpunkce:
            upravovanytext = upravovanytext.replace(znak, ' ')
        upravovanytext = upravovanytext.replace('   ', ' ').replace('  ', ' ')
        return upravovanytext
    def malaPismena(self, upravovanytext):
        velka = ['\\xc3\\x81','\\xc4\\x8c','\\xc4\\x8e','\\xc3\\x89','\\xc4\\x9a','\\xc3\\x8d','\\xc5\\x87','\\xc3\\x93','\\xc5\\x98','\\xc5\\xa0','\\xc5\\xa4','\\xc3\\x9a','\\xc5\\xae','\\xc3\\x9d','\\xc5\\xbd']
        mala =  ['\\xc3\\xa1','\\xc4\\x8d','\\xc4\\x8f','\\xc3\\xa9','\\xc4\\x9b','\\xc3\\xad','\\xc5\\x88','\\xc3\\xb3','\\xc5\\x99','\\xc5\\xa1','\\xc5\\xa5','\\xc3\\xba','\\xc5\\xaf','\\xc3\\xbd','\\xc5\\xbe']
        for velky, maly in zip(velka, mala):
            upravovanytext = upravovanytext.replace(velky, maly)
        upravovanytext = upravovanytext.lower()
        return upravovanytext

    def resetLabels(self):
        self["detailslabel"].setText("")
        self["ratinglabel"].setText("")
        self["baseFilmInfo"].setText("")
        #self["titlelabel"].setText("")
        #self["titlelabel"].setText("")
        self["extralabel"].setText("")
        self.ratingstars = -1

    def pageUp(self):
        if self.Page == 0:
            self["menu"].instance.moveSelection(self["menu"].instance.moveUp)
        if self.Page == 1:
            self["detailslabel"].pageUp()
        if self.Page == 2:
            self["extralabel"].pageUp()
    
    def pageDown(self):
        if self.Page == 0:
            self["menu"].instance.moveSelection(self["menu"].instance.moveDown)
        if self.Page == 1:
            self["detailslabel"].pageDown()
        if self.Page == 2:
            self["extralabel"].pageDown()

    def showMenu(self):
        try:
            self["statusbar"].show()
            #if ( self.Page is 1 or self.Page is 2 ) and self.resultlist:
            self.setTitle(_("Search results for")+ (" '%s'"%self.nazeveventuproskin))
            self["menu"].show()
            self["stars"].hide()
            self["starsbg"].hide()
            self["ratinglabel"].hide()
            self["poster"].hide()
            self["extralabel"].hide()
            #self["titlelabel"].hide()
            self["detailslabel"].hide()
            self["baseFilmInfo"].hide()
            self["key_blue"].setText("")
            self["key_green"].setText(_("List"))
            self["key_yellow"].setText(_("Film info"))
            self.Page = 0
        except:
            self["statusbar"].show()
            self["statusbar"].setText("Fatal ERROR")
            log.logError("Action showMenu failed.\n%s"%traceback.format_exc())

    def showDetails(self):
        try:
            self["ratinglabel"].show()
            self["detailslabel"].show()
            self["baseFilmInfo"].show()
            self["poster"].show()
            self["statusbar"].hide()
            self["menu"].hide()

            if self.resultlist and self.Page == 0:
                if not self.unikatni:
                    self.link = self["menu"].getCurrent()[1]
                    self.nazevkomplet = self["menu"].getCurrent()[0]
                self.unikatni = False
                self["statusbar"].setText("Downloading movie information: '%s'" % (self.link))
                localfile = os.path.join(config.plugins.archivCZSK.tmpPath.value, "archivCSFDquery2.html")
                fetchurl = "https://www.csfd.cz/film/" + self.link + "/komentare/?all=1" + str(randint(1000, 9999))
                downloadPage(fetchurl,localfile).addCallback(self.CSFDquery2).addErrback(self.fetchFailed)
                self["menu"].hide()
                self.resetLabels()
                self.setTitle(self.nazevkomplet)
                #self["titlelabel"].show()
                self.Page = 1

            if self.Page == 2:
                #self["titlelabel"].show()
                self["extralabel"].hide()
                self["poster"].show()
                if self.ratingstars > 0:
                    self["starsbg"].show()
                    self["stars"].show()
                    self["stars"].setValue(self.ratingstars)

                self.Page = 1
        except:
            self["statusbar"].show()
            self["statusbar"].setText("Fatal ERROR")
            log.logError("Action showDetails failed.\n%s"%traceback.format_exc())

    def showExtras(self):
        try:
            if self.Page == 1:
                self["extralabel"].show()
                self["detailslabel"].hide()
                self["baseFilmInfo"].hide()
                self["poster"].hide()
                self["stars"].hide()
                self["starsbg"].hide()
                self["ratinglabel"].hide()
                self.Page = 2
        except:
            self["statusbar"].show()
            self["statusbar"].setText("Fatal ERROR")
            log.logError("Action showExtras failed.\n%s"%traceback.format_exc())

    def openChannelSelection(self):
        self.session.openWithCallback(
            self.channelSelectionClosed,
            ArchivCSFDChannelSelection
        )

    def channelSelectionClosed(self, ret = None):
        if ret:
            self.eventName = ret
            self.Page = 0
            self.resultlist = []
            self["menu"].hide()
            self["ratinglabel"].show()
            self["detailslabel"].show()
            self["baseFilmInfo"].show()
            self["poster"].hide()
            self["stars"].hide()
            self["starsbg"].hide()
            self.getCSFD()

    def getCSFD(self):
        self.resetLabels()

        if self.eventName is not "":
            if self.eventName[-3:] == "...":
                self.eventName = self.eventName[:-3]
            self.nazeveventuproskin = self.eventName
            self.eventName = self.eventName.strip()

            try:
                self.eventName = urllib.quote(self.eventName)
            except:
                self.eventName = urllib.quote(self.eventName.decode('utf8').encode('ascii','ignore'))
            
            self.nazeveventu = self.eventName
            jineznaky = list(set(self.hledejVse('(%[0-9A-F][0-9A-F])', self.nazeveventu)))
            for jinyznak in jineznaky:
                desitkove = int(jinyznak[1:3], 16)
                if desitkove > 31 and desitkove < 128:
                    self.nazeveventu = self.nazeveventu.replace(jinyznak, chr(desitkove)) 
                elif desitkove > 127:
                    self.nazeveventu = self.nazeveventu.replace(jinyznak, jinyznak.lower())
            self.nazeveventu = self.nazeveventu.replace('%', '\\x')

            self["statusbar"].setText(_("Searching for")+(" '%s'" % self.nazeveventuproskin))
            localfile =  os.path.join(config.plugins.archivCZSK.tmpPath.value, "archivCSFDquery.html")
            fetchurl = "https://www.csfd.cz/hledat/?q=" + self.eventName
            self.puvodniurl = fetchurl
            downloadPage(fetchurl,localfile).addCallback(self.CSFDquery).addErrback(self.fetchFailed)
        else:
            self["statusbar"].setText("Movie name is empty.")

    def fetchFailed(self,string):
        log.logError("Download csfd info failed.\n%s"%string)
        self["statusbar"].setText("Download csfd info failed.")

    def adresaPredPresmerovanim(self, adresa):
        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
        request = opener.open(adresa)
        return request.url

    def CSFDquery(self, string):
        self["statusbar"].setText(_("Download complete for")+(" '%s'" % self.nazeveventuproskin))
        qfl = os.path.join(config.plugins.archivCZSK.tmpPath.value, "archivCSFDquery.html")
        self.inhtml = (open(qfl, "r").read())
         
        self.resultlist = []
        self.unikatni = False
        if '<h1 itemprop="name">' in self.inhtml:
            odkaz = self.najdi('<link rel="canonical" href="https://www.csfd.cz/film/(.*?)/', self.inhtml)
            nazevfilmu = self.najdi('<h1 itemprop="name">\s+(.*?)\s+<', self.inhtml)
            self.resultlist = [(nazevfilmu, odkaz)]
        elif not "<!DOCTYPE html" in self.inhtml:
            odkaz = self.adresaPredPresmerovanim(self.puvodniurl)
            odkaz = self.najdi('https://www.csfd.cz/film/(.*?)/', odkaz)
            self.resultlist = [(self.nazeveventuproskin, odkaz)]
        elif "SFD.cz</title>" in self.inhtml:
            filmy = self.najdi('<h2 class="header">Filmy</h2>(.*?)</ul>', self.inhtml)
            self.resultlist = []
            for odkaz, filmnazev, filminfo in self.hledejVse('<h3 class="subject"><a href="/film/(.*?)"(.*?)</h3>.*?<p>(.*?)</p>', filmy):
                hlavninazev = self.najdi('class="film c[0-9]">(.*?)</a>', filmnazev)
                celynazev = hlavninazev
                if 'class="film-type"' in filmnazev:
                    typnazev = self.najdi('<span class="film-type">(.*?)</span>', filmnazev)
                    celynazev += ' ' + typnazev
                celynazev += ' (' + filminfo + ')'
                rok = self.najdi('([0-9]{4})', filminfo)
                self.resultlist += [(celynazev, odkaz, hlavninazev, rok)]
            
            filmy = self.najdi('<ul class="films others">(.*?)</ul>', self.inhtml)
            for odkaz, filmnazev, filminfo in self.hledejVse('<a href="/film/(.*?)"(.*?)dir="ltr">(.*?)</span>', filmy):
                hlavninazev = self.najdi('class="film c[0-9]">(.*?)</a>', filmnazev)
                celynazev = hlavninazev
                if 'class="film-type"' in filmnazev:
                    typnazev = self.najdi('<span class="film-type">(.*?)</span>', filmnazev)
                    celynazev += ' ' + typnazev
                celynazev += ' ' + filminfo
                rok = self.najdi('([0-9]{4})', filminfo)
                self.resultlist += [(celynazev, odkaz, hlavninazev, rok)]
            
            shoda = []
            for nazevinfo, odkaz, nazevfilmu, rok in self.resultlist:
                log.logDebug("ArchivCSFD nazevinfo=%s, odkaz=%s, nazevfilmu=%s, rok=%s || compare=%s"%(nazevinfo, odkaz, nazevfilmu, rok, self.nazeveventu))
                #konvertovanynazev = ""
                nazevfilmu = self.odstraneniTagu(nazevfilmu)
                #konvertovanynazev = nazevfilmu
                #for znak in nazevfilmu:
                #    if ord(znak) > 127:
                #        znak = "\\x" + znak.encode("hex")
                #    konvertovanynazev += znak
                a = self.removeDiacritics(nazevfilmu).lower()
                b = self.removeDiacritics(self.nazeveventu).lower()
                #if self.malaPismena(self.odstraneniInterpunkce(konvertovanynazev)) == self.malaPismena(self.odstraneniInterpunkce(self.nazeveventu)):
                if a == b:
                    shoda += [(self.odstraneniTagu(nazevinfo), odkaz, rok)]

            log.logDebug("ArchivCSFD found %s matching movies"%len(shoda))
            if len(shoda) == 1:
                self.nazevkomplet, self.link, v3 = shoda[0]
                self.unikatni = True
            elif len(shoda) > 1:
                for nazevinfo, odkaz, rok in shoda:
                    rokInt = self.toInt(rok)
                    if (self.rokEPG == rokInt or self.rokEPG-1 == rokInt) and not self.unikatni:
                        self.nazevkomplet, self.link, v3 = self.odstraneniTagu(nazevinfo), odkaz, rok
                        self.unikatni = True
                        break
            self.resultlist = [(v1, v2) for v1, v2, v3, v4 in self.resultlist]
        else:
            self["detailslabel"].setText("Csfd request failed.")

        if self.resultlist:
            self.resultlist = [(self.odstraneniTagu(nazevinfo), odkaz) for nazevinfo, odkaz in self.resultlist]
            self["menu"].l.setList(self.resultlist)
            self['menu'].moveToIndex(0)
            if len(self.resultlist) == 1 or self.unikatni:
                self.Page = 0
                self["extralabel"].hide()
                self.showDetails()
            elif len(self.resultlist) > 1:
                self.Page = 1
                self.showMenu()
        else:
            #self["detailslabel"].setText("Not found for '%s'" % (self.nazeveventuproskin))
            self["statusbar"].setText("Not found for '%s'" % (self.nazeveventuproskin))

    

    def CSFDquery2(self,string):
        self["statusbar"].setText("Download movie info complete for '%s'" % (self.nazevkomplet))
        qfl = os.path.join(config.plugins.archivCZSK.tmpPath.value, "archivCSFDquery2.html")
        self.inhtml = (open(qfl, "r").read())
         
        if 'DOCTYPE html PUBLIC' in self.inhtml:
            self.CSFDparse()
        else:
            self["statusbar"].setText("Csfd loading error for '%s'" % (self.link))

    def CSFDparse(self):
        self.Page = 1
        Detailstext = "Movie info not found"
        if '<h1 itemprop="name">' in self.inhtml:
            self["key_yellow"].setText(_("Film info"))
            self["statusbar"].setText("CSFD info for '%s'" % (self.nazevkomplet))

            filmnazev = self.najdi('h1 itemprop="name"(.*?)/h1>', self.inhtml)
            nazevfilmu = self.najdi('>\s+(.*?)\s+<', filmnazev)
            if 'class="film-type"' in filmnazev:
                typnazev = self.najdi('<span class="film-type">(.*?)</span>', filmnazev)
                nazevfilmu += ' ' + typnazev
            nazevfilmu = self.odstraneniTagu(nazevfilmu)
            if len(nazevfilmu) > 70:
                nazevfilmu = nazevfilmu[0:70] + "..."
            #self["titlelabel"].setText(nazevfilmu)

            hodnoceni = self.najdi('<h2 class="average">(.*?)<', self.inhtml)
            Ratingtext = "--"
            if hodnoceni != "":
                Ratingtext = hodnoceni
                if "%" in hodnoceni:
                    self.ratingstars = int(hodnoceni.replace("%",""))
                    self["stars"].show()
                    self["stars"].setValue(self.ratingstars)
                    self["starsbg"].show()
            self["ratinglabel"].setText(Ratingtext)

            posterurl = ""
            posterurl = self.najdi('<div id="poster".*?src="(.*?)"', self.inhtml)
            if posterurl != "":
                if not "https:" in posterurl:
                    posterurl = "https:" + posterurl
                self["statusbar"].setText("Downloading movie poster for '%s'" % (posterurl))
                localfile = os.path.join(config.plugins.archivCZSK.tmpPath.value, "csfd_archivczsk_poster.jpg")
                downloadPage(posterurl,localfile).addCallback(self.CSFDPoster).addErrback(self.fetchFailed)
            else:
                self.CSFDPoster(noPoster = True)

            baseInfo = ""
            Detailstext = ""
            nazevserialu = serie = ''
            serial = self.najdi('<div class="ct-general th-0 series-navigation">(.*?)</div>', self.inhtml)
            #if serial:
            #    nazevserialu = self.najdi('<div class="content">\s+<a href="/film/.*?/">(.*?)</a>', serial)
            #    serie = self.najdi('</span><a href="/film/.*?/">(.*?)</a>', serial)
            #    nazevserialu = self.odstraneniTagu(nazevserialu)
            #    serie = self.odstraneniTagu(serie)
            #if nazevserialu != '':
            #    baseInfo += 'Seri\xc3\xa1l: ' + nazevserialu
            #    if serie != '':
            #        baseInfo += ' (' + serie + ')'
            #    baseInfo += '\n\n'

            #nazvy = self.najdi('<ul class="names">(.*?)</ul>', self.inhtml)
            #if nazvy:
            #    searchresultmask = re.compile('alt="(.*?)".*?<h3>(.*?)</h3>', re.DOTALL)
            #    searchresults = searchresultmask.findall(nazvy)
            #    vysledky = [(v2 + ' (' + v1 + ')') for v1, v2 in searchresults]
            #    for nazev in vysledky:
            #        baseInfo += nazev + '\n'
            #    baseInfo += '\n'

            #zanr = self.najdi('<p class="genre">(.*?)<', self.inhtml)
            #baseInfo += zanr + '\n'

            zemerokdelka = self.najdi('<p class="origin">(.*?)</p>', self.inhtml)
            zemerokdelka = zemerokdelka.replace('<span itemprop="dateCreated">', '').replace('</span>', '')
            try:
                baseInfo = zemerokdelka.split(",")[2].strip()+"\n"
            except:
                pass

            #baseInfo += zemerokdelka + '\n\n'

            #vysilani = self.najdi('<ul class="relations">(.*?)</ul>', self.inhtml)
            #if vysilani:
            #    baseInfo += 'Nejbli\xc5\xbe\xc5\xa1\xc3\xad vys\xc3\xadl\xc3\xa1n\xc3\xad v TV:\n'
            #    searchresultmask = re.compile('<li class="content g1">.*?>(.*?)</a>', re.DOTALL)
            #    searchresults = searchresultmask.findall(vysilani)
            #    vysledky = [(v1) for v1 in searchresults]
            #    for termin in vysledky:
            #        baseInfo += termin + '      '
            #    #baseInfo += '\n\n'

            obory = ['Re\xc5\xbeie', 'P\xc5\x99edloha', 'Sc\xc3\xa9n\xc3\xa1\xc5\x99', 'Kamera','Hudba', 'Hraj\xc3\xad']
            for obor in obory:
                nazvy = self.najdi('<h4>' + obor + ':</h4>(.*?)</span>', self.inhtml)
                searchresultmask = re.compile('<a href=".*?">(.*?)</a>', re.DOTALL)
                searchresults = searchresultmask.findall(nazvy)
                vysledky = [(tvurce) for tvurce in searchresults]
                autori = ""
                for tvurce in vysledky:
                    autori += tvurce + ", "
                autori = autori[0:len(autori)-2]
                if autori != "":
                    if obor == 'Hraj\xc3\xad':
                        baseInfo += '\n'	
                    baseInfo += obor + ': ' + autori + '\n'
            if baseInfo != "":
                baseInfo += '\n'

            obsahy = self.najdi('<h3>Obsah(.*?)</ul>', self.inhtml)
            searchresultmask = re.compile('<span class="dot icon.*?></span>\s+(.*?)<span class.*?>(.*?)</span>', re.DOTALL)
            searchresults = searchresultmask.findall(obsahy)
            vysledky = [(v1, v2) for v1, v2 in searchresults]
            for obsah, autorobsahu in vysledky:
                if "<a href" in autorobsahu:
                    autorobsahu = "(" + self.najdi('<a href.*?>(.*?)<', autorobsahu) + ")"
                Detailstext += obsah + '   ' + autorobsahu + '\n\n'
            Detailstext = self.odstraneniTagu(Detailstext)

            Extratext = ""
            #pocetkomentaru = self.najdi('<h2>Koment.*?"count">(.*?)<', self.inhtml)
            #if pocetkomentaru != "" and pocetkomentaru != "(0)":
            #    Extratext += "Koment\xc3\xa1\xc5\x99e u\xc5\xbeivatel\xc5\xaf k filmu " + pocetkomentaru + '\n\n'
            komentare = self.najdi('<h2>Koment(.*?)<div class="footer">', self.inhtml)
            searchresultmask = re.compile('<h5 class="author">(.*?)</h5>.*?class="rating"(.*?)<p class="post">(.*?)<span class="date desc">(.*?)</span>', re.DOTALL)
            searchresults = searchresultmask.findall(komentare)
            vysledky = [(v1, v2, v3, v4) for v1, v2, v3, v4 in searchresults]
            for autorkomentare, hodnocenikomentare, komentar, datumkomentare in vysledky:
                if "a href" in autorkomentare:
                    autorkomentare = self.najdi('>(.*?)<', autorkomentare)
                if "alt=" in hodnocenikomentare:
                    hodnocenikomentare = self.najdi('alt="(.*?)"', hodnocenikomentare)
                elif "odpad" in hodnocenikomentare:
                    hodnocenikomentare = "odpad!"
                else:
                    hodnocenikomentare = ""
                Extratext += autorkomentare + '    ' + hodnocenikomentare + '\n' + komentar + '\n' + datumkomentare + '\n\n'
            if Extratext != "":
                Extratext = self.odstraneniTagu(Extratext)
                if len(Extratext) > 19000:
                    Extratext = Extratext[0:19000] + "...\n\n(seznam koment\xc3\xa1\xc5\x99\xc5\xaf zkr\xc3\xa1cen)"
                self["extralabel"].setText(Extratext)
                self["extralabel"].hide()
                self["key_blue"].setText(_("Comments"))

        self["baseFilmInfo"].setText(baseInfo)
        self["detailslabel"].setText(Detailstext)
    
    def CSFDPoster(self, noPoster = False):
        self["statusbar"].setText(_("Csfd info for") + (" '%s'" % self.nazevkomplet))
        if not noPoster:
            filename = os.path.join(config.plugins.archivCZSK.tmpPath.value, "csfd_archivczsk_poster.jpg")
        else:
            filename = os.path.join(settings.PLUGIN_PATH, 'gui','icon', 'csfd_no_poster.png')
        sc = AVSwitch().getFramebufferScale()
        self.picload.setPara((self["poster"].instance.size().width(), self["poster"].instance.size().height(), sc[0], sc[1], False, 1, "#00000000"))
        self.picload.startDecode(filename)

    def paintPosterPixmapCB(self, picInfo=None):
        ptr = self.picload.getData()
        if ptr is not None:
            self["poster"].instance.setPixmap(ptr.__deref__())
            self["poster"].show()

    def createSummary(self):
        return ArchivCSFDLCDScreen    


class ArchivCSFDLCDScreen(Screen):
    def __init__(self, session, parent):
        Screen.__init__(self, session)
        self["headline"] = Label("Archiv CSFD")
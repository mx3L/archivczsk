## Zoznam zmien: 

  * automaticka aktualizacia pluginu so zachovanim udajov
  * volba CSFD pluginu (+interny)
  * rozsirene informacie o filme (pokial ich doplnok poskytuje)
  * definovanie vlastneho radenia doplnok (prinosne pri vlastnej kategorii)
  * predny panel setoboxu zobrazuje co sa prave prehrava
  * logovanie (default: /tmp/archivCZSK.log)
  * vylepsena funkcionalita aktualizacie doplnkov
  * kontrola aktualizacii pri spusteni pluginu resp. po uplynuti 2h od poslednej kontroly
  * uprava designu skinov
  * rychlostne vylepsenie pluginu
  * fix FullHD skinu ktory sposoboval pad systemu
  * fix virtualnej klavesnice (XcursorX)
  * fix pridavania do oblubenych poloziek (niekedy to nic nepridalo)
  * fix pretacania v doplnku Sosac (pri zaplatenom VIP ucte)
  * fix kompatibility OE2.0 - OE2.5
  * fix chybajuceho kodovania napr. v OpenAtv6.1 (pad systemu pri stahovani videa)
  * fix dalsich chyb ktore sposobovali pad systemu


## Install
Pouzivatelom windows doporucujem stiahnut program[ __putty__](https://the.earth.li/~sgtatham/putty/latest/w32/putty.exe) cez ktory sa pripojite na setobox samozrejme musite poznat IP adresu setoboxu a prihlasovacie meno zvycajne *__root__*

* __SSH telnet__

      opkg install curl
      opkg install http://github.com/mx3L/archivczsk/releases/download/v1.0/subssupport_1.5.5-20170116_all.ipk
      opkg install http://github.com/.............ipk
      init 4
      init 3
      (alebo: reboot)
      
      -----------------------Debian-----------------------

      dpkg -i curl
      dpkg -i http://github.com/mx3L/archivczsk/releases/download/v1.0/subssupport_1.5.5-20170116_all.deb
      dpkg -i http://github.com/.............deb
      init 4
      init 3
      (alebo: reboot)
      
* __Manual__ (nedoporucujem, mozne problemy)
   * stiahnut balicek (*.ipk|*.deb)  a nahrat do setoboxu do adresara __/tmp__
   * cez software setoboxu najst manualne instalovanie balickov a mal by sa objavit dany nazov balicku
   * naistalovat a restart setoboxu
   * *nebude fungovat auto update pokial nie je naistalovany __curl__*

## Re-Install
Ak uz mate jednu z predoslych verzii naistalovanu obnovia sa kategorie aj data pluginov ktore ste mali pred tym.

* __SSH telnet__

      mkdir -p /tmp/archivczsk
      cp -R /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/resources/data /tmp/archivczsk
      opkg remove -force-depends enigma2-plugin-extensions-archivczsk
      opkg install http://github.com/.............ipk
      init 4
      init 3
            
      -----------------------Debian-----------------------

      mkdir -p /tmp/archivczsk
      cp -R /usr/lib/enigma2/python/Plugins/Extensions/archivCZSK/resources/data /tmp/archivczsk
      dpkg --purge enigma2-plugin-extensions-archivczsk
      dpkg -i http://github.com/.............deb
      init 4
      init 3
      (alebo: reboot)

## Problem spustenia pluginu (napr. pre Black Hole image)
- Pokial sa Vam nezobrazi archivCZSK v ponuke resp. pri vstupe do zoznamu modulov Vam vypise "cannot import name BrowserLikeRedirectAgent" tak treba spustit cez telnet tento prikaz a restartnut prijmac (fix zaberie cca +4MB v pamati FLASH ale kto chce moze vymazat zolzku '/twisted_origin_backup' a subory *.py v zlozke '/twisted' __az po restarte prijmaca!!!__). 

  ```
  opkg install http://github.com/mx3L/archivczsk/releases/download/v1.0/twisted-16-2-0-fix.ipk
  ```

## Reporting
Pripadne chyby poprosim hlasit sem na github (__doporucujem pripojit log file__ inac je dost mozne ze nedostanete odpoved)





*********************************************************************************************************
*********************************************************************************************************




## Verzia 0.73
**Vseobecne**

* pridana full-hd verzia skinu
* pridana podpora pre skinovanie nastaveni doplnkov/archivu
  * uprava skinu nastaveni z vyuzitim noveho Tabs komponentu
* opravy a vylepsenia pri zobrazovani cesty pri prehliadani doplnkov
  * vzdy sa zobrazuje spravna cesta
  * skracovanie cesty ak za sebou nasleduju rovnake nazvy 
* pridane vyhladavanie v EPG pre sosac plugin
* pridana podpora pre editovanie ulozenych vyhladavanych nazvov
* oprava hlasenej chyby SSL: CERTIFICATE_VERIFY_FAILED, v niektorych 
doplnkoch(ivysilani, prima, koukni) pri pouziti python-2.7.9+
* oprava stahovania aktualizacii po prvom spusteni
* odstranene nepotrebne sucasti archivov (servicemp4, rtmpgw)
* odstranene instalovanie rtmpdump z dovodu moznej nekompatibility
a uprednostnene instalovanie rtmpdump z feedu

## Verzia 0.72 beta 8
**Vseobecne**

* oprava GS pri vyhladavani cez EPG 
* pridana podpora pre novy prima plugin
* odstraneny nefunkcny prima plugin,
* oprava tv.sme.sk a videacesky.cz 

## Verzia 0.72 beta 7
**Vseobecne**

* aktualizovane archivy
* mensie upravy skinu, priprava pre podporu inych skinov
* oprava GS pred zacatim prehravania na OpenATV image
* odstraneny prehravac streamov ( odporucam pouzit IPTV bouquets )
* pridana moznost neotvarat "Vyberte Zdroj" obrazovku pred nacitavanim videa, ale nacitat video linky a vybrat si z nich, s moznostou sa k nim vratit.

## Verzia 0.72 beta 6
**Vseobecne**

* aktualizovana prima-play(prehravanie funkcne)
* pridane zobrazenie gstreamer verzie
* zlepsene prehravanie rtmp streamov pri image s gstreamer-1.0 verziou
  * korektne zobrazenie pozicie po pretacani (prima-play, novaplus), v pripade ze je zapnuta oprava rtmp pretacania
* zlepsenie moznosti stahovania pri image s gstreamer
  * pridana moznost stahovat HLS streamy(ivysilani, ta3.com, rtvs.sk, markiza.sk)
  * stabilnejsie stahovanie rtmp streamov(prima-play, joj.sk, novaplus..)

## Verzia 0.72 beta 5
**Vseobecne**

* aktualizovane doplnky (ta3.com, joj.sk, rtvs.sk, prima-play, ulozto, stream-resolver)
* odstranene nefunkcne doplnky
* nova adresa pre aktualizacie (pre starsie verzie nebudu aktualizacie fungovat)
* opravena detekcia gstreamer-1.0 verzie
* pridana zavislost na novu subssupport verziu pre lepsiu podporu tituliek
* pridana zavislost na youtube-dl pre prehravanie zabezpecenych videii z youtube
* pridana zavislost na python-email pre funcknost dvtv
* pridana zavislost na curl pre funkcnost automatickych aktualizacii

## Verzia 0.72 beta 4
**Vseobecne**

* vypnutie hlasky pri ukonceni pluginu/prehravaca (http://code.google.com/p/archivy-czsk/issues/detail?id=50)

## Verzia 0.72 beta 3
**Vseobecne**

* korektne formatovane pismo v zoznamoch
* pouzity LocationBox pre vyber cesty
* oprava stahovania niektorych rtmp streamov
* opravena captcha obrazovka
* + ine mensie opravy popisane v commit log

## Verzia 0.72 beta 2
**Vseobecne**

* oprava GS na DMM image(Newnigma)

## Verzia 0.72 beta 1
**Vseobecne**

* pridany manazer doplnkov
  * vypnutie, zapnutie doplnkov
* pridana podpora kategorii
  * vytvaranie, mazanie, editacia kategorii
  * pridavanie, mazanie doplnkov do/v kategorii
  * nastavenie predvolenej kategorie
* oprava konfliktu s inymi pluginmy(TSMedia,)
* opraveny cesky preklad - opravil vlastvs499

**Stahovanie**
* moznost premenovat/prepisat subor ak uz taky subor existuje
* oprava zistenia nazvu suboru(ulozto)

## Verzia 0.70 beta 7
**Vseobecne**

* rychlejsia kontrola aktualizacii
* oprava stahovania aktualizacii na niektorych prijmacoch
* opravy prekladu

**Prehravac**
* pridane vsetky moznosti zmeny pomeru stran a uprav obrazu
* aktualizovana librtmp kniznica pre mipsel
* aktualizovana servicemp4 aplikacia pre mipsel

## Verzia 0.70 beta 6
**Vseobecne**

* zjednodusene prehravanie/stahovanie videii
  * pridana podpora pre dynamicky ziskavane video polozky
  * automaticke zacatie prehravania/stahovania v pripade ziskania len jedneho videa
* pridana podpora pre globalne kontextove ponuky
  * Zobrazit stahovane subory 

**Prehravac**
* oprava pauzovania/odpauzovania v rtmp streamoch (tv archivy)
* oprava prehravania tituliek pri skoku na dalsie video v playliste

## Verzia 0.70 beta 5
**Vseobecne**

* zlepsena podpora pre DMM image (nahodne GS, aktualizacie)
* opravy kontextovych ponuk (zalozky, playlist)
* oprava stahovania (befun)
* znizeny rtmp buffer pre plynule prehravanie na niektorych STB

## Verzia 0.70 beta 4
**Vseobecne**

* aktualizovane doplnky -> https://github.com/mx3L/archivczsk-doplnky
* koukni.cz pridane do EPG vyhladavania
* oprava GS po ukonceni pluginu
* oprava GS na niektorych DM image pri spusteni videa

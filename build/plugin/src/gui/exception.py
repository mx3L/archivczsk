'''
Created on 10.3.2013

@author: marko

GUI Exception handling
'''
import traceback
import urllib2,requests
from common import showInfoMessage, showWarningMessage, showErrorMessage
from Plugins.Extensions.archivCZSK.engine.exceptions import addon, download, updater, play
from Plugins.Extensions.archivCZSK.gsession import GlobalSession
from Plugins.Extensions.archivCZSK import _, log

class GUIExceptionHandler(object):
    errorName = _("Unknown Error")
    warningName = _("Unknown Warning")
    infoName = _("Unknown Info")

    def __init__(self,session, timeout=6):
        self.timeout = timeout
        self.session = session
        #self.session = GlobalSession.getSession()
        self.messageFormat = "[%s]\n%s"

    def infoMessage(self, text):
        showInfoMessage(self.session, self.messageFormat % (self.__class__.infoName, text), self.timeout)

    def errorMessage(self, text):
        showErrorMessage(self.session, self.messageFormat % (self.__class__.errorName, text), self.timeout)

    def warningMessage(self, text):
        showWarningMessage(self.session, self.messageFormat % (self.__class__.warningName, text), self.timeout)

    def customMessage(self, messageType, text):
        if type == 'info':
            showInfoMessage(self.session, text, self.timeout)
        elif type == 'warning':
            showWarningMessage(self.session, text, self.timeout)
        elif type == 'error':
            showErrorMessage(self.session, text, self.timeout)


class AddonExceptionHandler(GUIExceptionHandler):
    errorName = _("Addon error")
    warningName = _("Addon warning")
    infoName = _("Addon info")

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            try:
                f = open("/tmp/archivCZSK.last", "r")
                params = f.read()
                try:
                    func(*args, **kwargs)
                # addon specific exceptions
                except addon.AddonInfoError as er:
                    log.logError("Addon (AddonInfoError) error '%s'.\n%s"%(er.value,traceback.format_exc()))
                    self.infoMessage(er.value)
                except addon.AddonWarningError as er:
                    log.logError("Addon (AddonWarningError) error '%s'.\n%s"%(er.value,traceback.format_exc()))
                    self.warningMessage(er.value)
                except addon.AddonError as er:
                    log.logError("Addon (AddonError) error '%s'.\n%s"%(er.value,traceback.format_exc()))
                    self.errorMessage(er.value)
                # loading exceptions
                except urllib2.HTTPError, e:
                    log.logError("Addon (HTTPError) error '%s'.\n%s"%(e.code,traceback.format_exc()))
                    message = "%s %s:%d" % (_("Error in loading"), _("HTTP Error"), e.code)
                    self.errorMessage(message)
                except urllib2.URLError, e:
                    log.logError("Addon (URLError) error '%s'.\n%s"%(e.reason,traceback.format_exc()))
                    message = "%s %s:%s" % (_("Error in loading"), _("URL Error"), str(e.reason))
                    self.errorMessage(message)
                except addon.AddonThreadException as er:
                    log.logError("Addon (AddonThreadException) error.\n%s"%(traceback.format_exc()))
                    pass
                # we handle all possible exceptions since we dont want plugin to crash because of addon error...
                except Exception, e:
                    log.logError("Addon error.\n%s"%traceback.format_exc())
                    self.errorMessage(_("Author of this addon needs to update it"))
                    traceback.print_exc()
            except:
                log.logError("Addon (LOG) error.\n%s"%traceback.format_exc())
                # this can go to crash because want show modal from screen which is not modal
                # but this can got to fck
                #self.errorMessage("ADDON ERROR")
                pass
        return wrapped


class DownloadExceptionHandler(GUIExceptionHandler):
    errorName = _("Download error")
    warningName = _("Download warning")
    infoName = _("Download info")

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except download.NotSupportedProtocolError, e:
                message = "%s %s" % (e.message, _("protocol is not supported"))
                self.errorMessage(message)
            except urllib2.HTTPError, e:
                message = "%s %s:%d" % (_("Error in loading"), _("HTTP Error"), e.code)
                self.errorMessage(message)
            except urllib2.URLError, e:
                message = "%s %s:%s" % (_("Error in loading"), _("URL Error"), str(e.reason))
                self.errorMessage(message)
        return wrapped


class UpdaterExceptionHandler(GUIExceptionHandler):
    errorName = _("Updater error")
    warningName = _("Updater warning")
    infoName = _("Updater info")
    def __call__(self, func):
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except urllib2.HTTPError, e:
                message = "%s %s:%d" % (_("Error in loading"), _("HTTP Error"), e.code)
                self.errorMessage(message)
            except urllib2.URLError, e:
                message = "%s %s:%s" % (_("Error in loading"), _("URL Error"), str(e.reason))
                self.errorMessage(message)
        return wrapped


class PlayExceptionHandler(GUIExceptionHandler):
    errorName = _("Play error")
    warningName = _("Play warning")
    infoName = _("Play info")

    def __call__(self, func):
        def wrapped(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except play.UrlNotExistError, e:
                self.errorMessage((_("Video url doesnt exist")))
        return wrapped


import traceback
import datetime
from twisted.internet import defer

from Components.config import config
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox

from item import ItemHandler
from folder import FolderItemHandler
from Plugins.Extensions.archivCZSK import _, log
from Plugins.Extensions.archivCZSK.gui.exception import AddonExceptionHandler, DownloadExceptionHandler, PlayExceptionHandler
from Plugins.Extensions.archivCZSK.engine.items import PExit, PVideo, PVideoResolved, PVideoNotResolved, PPlaylist
from Plugins.Extensions.archivCZSK.engine.tools.util import toString
from enigma import eTimer
from Plugins.Extensions.archivCZSK.compat import eConnectCallback
from Plugins.Extensions.archivCZSK.gui.common import showInfoMessage, showErrorMessage, showWarningMessage


class MediaItemHandler(ItemHandler):
    """ Template class - handles Media Item interaction """

    def __init__(self, session, content_screen, content_provider, info_modes):
        ItemHandler.__init__(self, session, content_screen, info_modes)
        self.content_provider = content_provider

    def _open_item(self, item, mode='play', *args, **kwargs):
        self.play_item(item, mode, args, kwargs)

    def isValidForTrakt(self, item):
        if hasattr(item, 'dataItem') and item.dataItem is not None:
           if 'imdb' in item.dataItem or 'tvdb' in item.dataItem or 'trakt' in item.dataItem:
               return True
        return False

    
    # action:
    #   - play
    #   - watching /every 10minutes/
    #   - end
    def cmdStats(self, item, action, finishCB=None, sendTraktWatchedCmd=False):
        def open_item_finish(result):
            log.logDebug("Stats (%s) call finished.\n%s"%(action,result))
            if paused and not sendTraktWatchedCmd:
                self.content_provider.pause()
            if sendTraktWatchedCmd:
                return self.cmdTrakt(item, 'watched', finishCB)
            elif finishCB is not None:
                finishCB()
        paused = self.content_provider.isPaused()
        try:
            if paused:
                self.content_provider.resume()
            
            ppp = { 'cp': 'czsklib', 'stats':action, 'item': item.dataItem }
            # content provider must be in running state (not paused)
            self.content_provider.get_content(self.session, params=ppp, successCB=open_item_finish, errorCB=open_item_finish)
        except:
            log.logError("Stats call failed.\n%s"%traceback.format_exc())
            if paused:
                self.content_provider.pause()
            if finishCB is not None:
                finishCB()
            
    # action:
    #   - add
    #   - remove
    #   - watched
    #   - unwatched
    def cmdTrakt(self, item, action, finishedCB=None):
        def finishCb(result):
            if paused:
                self.content_provider.pause()
            if finishedCB is not None:
                finishedCB()
        def open_item_success_cb(result):
            log.logDebug("Trakt (%s) call success. %s"%(action, result))
            #OK, ERROR
            list_items, command, args = result
            if args['isError']:
                return showErrorMessage(self.session, args['msg'], 10, finishCb)
            else:
                return showInfoMessage(self.session, args['msg'], 10, finishCb)
        def open_item_error_cb(failure):
            log.logDebug("Trakt (%s) call failed. %s"%(action,failure))
            return showErrorMessage(self.session, "Operation failed.", 10, finishCb)

        paused = self.content_provider.isPaused()
        try:
            if paused:
                self.content_provider.resume()
            
            ppp = { 'cp': 'czsklib', 'trakt':action, 'item': item.dataItem }
            # content provider must be in running state (not paused)
            self.content_provider.get_content(self.session, params=ppp, successCB=open_item_success_cb, errorCB=open_item_error_cb)
        except:
            log.logError("Trakt call failed.\n%s"%traceback.format_exc())
            if paused:
                self.content_provider.pause()
            if finishedCB is not None:
                finishedCB()

    def play_item(self, item, mode='play', *args, **kwargs):
        def endPlayFinish():
            self.content_screen.workingFinished()
            self.content_provider.resume()
        def startWatchingTimer():
            self.cmdTimer.start(timerPeriod)
        def timerEvent():
            self.cmdStats(item, 'watching')
        def end_play():
            # @TODO toto sa tak ci tak zjebe ked sa posiela trakt a stlaca sa exit tak to znova zavola dalsie vlakno a potom je crash
            try:
                self.cmdTimer.stop()
                del self.cmdTimer
                del self.cmdTimer_conn
            except:
                log.logDebug("Release cmd timer failed.\n%s" % traceback.format_exc())
            
            sendTrakt = False
            try:
                if 'trakt' in self.content_provider.capabilities and self.isValidForTrakt(item):
                    totalSec = (datetime.datetime.now()-playStartAt).total_seconds()
                    durSec = float(item.dataItem['duration'])
                    # movie time from start play after 80% then mark as watched
                    if totalSec >= durSec*0.80:
                        sendTrakt = True
                    else:
                        log.logDebug('Movie not mark as watched ( <80% watch time).')
            except:
                log.logError("Trakt AUTO mark as watched failed.\n%s"%traceback.format_exc())

            # na DEBUG
            #sendTrakt = True
            if 'stats' in self.content_provider.capabilities:
                self.cmdStats(item, 'end', finishCB=endPlayFinish, sendTraktWatchedCmd=sendTrakt)
            else:
                endPlayFinish()

        timerPeriod = 10*60*1000 #10min
        self.cmdTimer = eTimer()
        self.cmdTimer_conn = eConnectCallback(self.cmdTimer.timeout, timerEvent)

        self.content_screen.workingStarted()
        self.content_provider.pause()
        self.content_provider.play(self.session, item, mode, end_play)

        # send command
        if 'stats' in self.content_provider.capabilities:
            playStartAt = datetime.datetime.now()
            self.cmdStats(item, 'play', finishCB=startWatchingTimer)

    def download_item(self, item, mode="", *args, **kwargs):
        @DownloadExceptionHandler(self.session)
        def start_download(mode):
            try:
                self.content_provider.download(self.session, item, mode=mode)
            except Exception:
                self.content_screen.workingFinished()
                raise
        start_download(mode)

    def _init_menu(self, item):
        provider = self.content_provider
        # TRAKT menu (show only if item got data to handle trakt)
        if 'trakt' in provider.capabilities and self.isValidForTrakt(item):
            item.add_context_menu_item(_("(Trakt) Add to Watchlist"), action=self.cmdTrakt, params={'item':item, 'action':'add'})
            item.add_context_menu_item(_("(Trakt) Remove from Watchlist"), action=self.cmdTrakt, params={'item':item, 'action':'remove'})
            item.add_context_menu_item(_("(Trakt) Mark as watched"), action=self.cmdTrakt, params={'item':item, 'action':'watched'})
            item.add_context_menu_item(_("(Trakt) Mark as not watched"), action=self.cmdTrakt, params={'item':item, 'action':'unwatched'})

        if 'download' in provider.capabilities:
            item.add_context_menu_item(_("Download"), action=self.download_item, params={'item':item, 'mode':'auto'})
        if 'play' in provider.capabilities:
            item.add_context_menu_item(_("Play"), action=self.play_item, params={'item':item, 'mode':'play'})
        if 'play_and_download' in provider.capabilities:
            item.add_context_menu_item(_("Play and Download"), action=self.play_item, params={'item':item, 'mode':'play_and_download'})

class VideoResolvedItemHandler(MediaItemHandler):
    handles = (PVideoResolved, )
    def __init__(self, session, content_screen, content_provider):
        info_handlers = ['csfd','item']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, info_handlers)



class VideoNotResolvedItemHandler(MediaItemHandler):
    handles = (PVideoNotResolved, )
    def __init__(self, session, content_screen, content_provider):
        info_modes = ['item','csfd']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, ['item','csfd'])

    def _init_menu(self, item):
        MediaItemHandler._init_menu(self, item)
        item.add_context_menu_item(_("Resolve videos"),
                                       action=self._resolve_videos,
                                       params={'item':item})
        if 'favorites' in self.content_provider.capabilities:
            item.add_context_menu_item(_("Add Shortcut"), 
                    action=self.ask_add_shortcut, 
                    params={'item':item})
        else:
            item.remove_context_menu_item(_("Add Shortcut"), 
                    action=self.ask_add_shortcut, 
                    params={'item':item})

    def ask_add_shortcut(self, item):
        self.item = item
        self.session.openWithCallback(self.add_shortcut_cb, MessageBox,
                text="%s %s %s"%(_("Do you want to add"), toString(item.name),  _("shortcut?")),
                type=MessageBox.TYPE_YESNO)

    def add_shortcut_cb(self, cb):
        if cb:
            self.content_provider.create_shortcut(self.item)

    def play_item(self, item, mode='play', *args, **kwargs):

        def video_selected_callback(res_item):
            MediaItemHandler.play_item(self, res_item, mode)

        if config.plugins.archivCZSK.showVideoSourceSelection.value:
            self._resolve_video(item, video_selected_callback)
        else:
            self._resolve_videos(item)

    def download_item(self, item, mode="", *args, **kwargs):
        def wrapped(res_item):
            MediaItemHandler.download_item(self, res_item, mode)
            self.content_screen.workingFinished()
        self._resolve_video(item, wrapped)

    def _filter_by_quality(self, items):
        pass

    def _resolve_video(self, item, callback):

        def selected_source(answer):
            if answer is not None:
                # entry point of play video source
                callback(answer[1])
            else:
                self.content_screen.workingFinished()

        def open_item_success_cb(result):
            def continue_cb(res):
                self._filter_by_quality(list_items)
                if len(list_items) > 1:
                    choices = []
                    for i in list_items:
                        name = i.name
                        # TODO remove workaround of embedding
                        # quality in title in addons
                        if i.quality and i.quality not in i.name:
                            if "[???]" in i.name:
                                name = i.name.replace("[???]","[%s]"%(i.quality))
                            else:
                                name = "[%s] %s"%(i.quality, i.name)
                        choices.append((toString(name), i))
                    self.session.openWithCallback(selected_source,
                            ChoiceBox, _("Please select source"),
                            list = choices,
                            skin_name = ["ArchivCZSKVideoSourceSelection"])
                elif len(list_items) == 1:
                    item = list_items[0]
                    callback(item)
                else: # no video
                    self.content_screen.workingFinished()

            self.content_screen.stopLoading()
            self.content_screen.showList()
            list_items, command, args = result

            try:
                #client.add_operation("SHOW_MSG", {'msg': 'some text'},
                #                                  'msgType': 'info|error|warning',     #optional
                #                                  'msgTimeout': 10,                    #optional
                #                                  'canClose': True                     #optional
                #                                 })

                if command is not None:
                   cmd = ("%s"%command).lower()
                   params = args
                   if cmd == "show_msg":
                       #dialogStart = datetime.datetime.now()
                       self.content_screen.stopLoading()
                       msgType = 'info'
                       if 'msgType' in args:
                           msgType = ("%s"%args['msgType']).lower()
                       msgTimeout = 15
                       if 'msgTimeout' in args:
                           msgTimeout = int(args['msgTimeout'])
                       canClose = True
                       if 'canClose' in args:
                           canClose = args['canClose']
                       if msgType == 'error':
                           return showErrorMessage(self.session, args['msg'], msgTimeout, continue_cb, enableInput=canClose)
                       if msgType == 'warning':
                           return showWarningMessage(self.session, args['msg'], msgTimeout, continue_cb, enableInput=canClose)
                       return showInfoMessage(self.session, args['msg'], msgTimeout, continue_cb, enableInput=canClose)
            except:
                log.logError("Execute HACK command failed (media handler).\n%s"%traceback.format_exc())
                command = None
                args = {}

            self._filter_by_quality(list_items)
            if len(list_items) > 1:
                choices = []
                for i in list_items:
                    name = i.name
                    # TODO remove workaround of embedding
                    # quality in title in addons
                    if i.quality and i.quality not in i.name:
                        if "[???]" in i.name:
                            name = i.name.replace("[???]","[%s]"%(i.quality))
                        else:
                            name = "[%s] %s"%(i.quality, i.name)
                    choices.append((toString(name), i))
                self.session.openWithCallback(selected_source,
                        ChoiceBox, _("Please select source"),
                        list = choices,
                        skin_name = ["ArchivCZSKVideoSourceSelection"])
            elif len(list_items) == 1:
                item = list_items[0]
                callback(item)
            else: # no video
                self.content_screen.workingFinished()

        @AddonExceptionHandler(self.session)
        def open_item_error_cb(failure):
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()

        self.content_screen.hideList()
        self.content_screen.startLoading()
        self.content_screen.workingStarted()
        self.content_provider.get_content(self.session, item.params, open_item_success_cb, open_item_error_cb)


    def _resolve_videos(self, item):
        def open_item_success_cb(result):
            list_items, screen_command, args = result
            list_items.insert(0, PExit())
            if screen_command is not None:
                self.content_screen.resolveCommand(screen_command, args)
            else:
                self.content_screen.save()
                content = {'parent_it':item, 'lst_items':list_items, 'refresh':False}
                self.content_screen.stopLoading()
                self.content_screen.load(content)
                self.content_screen.showList()
                self.content_screen.workingFinished()

        @AddonExceptionHandler(self.session)
        def open_item_error_cb(failure):
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()

        self.content_screen.workingStarted()
        self.content_screen.hideList()
        self.content_screen.startLoading()
        self.content_provider.get_content(self.session, item.params, open_item_success_cb, open_item_error_cb)



class PlaylistItemHandler(MediaItemHandler):
    handles = (PPlaylist, )
    def __init__(self, session, content_screen, content_provider, info_modes=None):
        if not info_modes:
            info_modes = ['item','csfd']
        MediaItemHandler.__init__(self, session, content_screen, content_provider, info_modes)

    def show_playlist(self, item):
        self.content_screen.save()
        list_items = [PExit()]
        list_items.extend(item.playlist[:])
        content = {'parent_it':item,
                          'lst_items':list_items,
                          'refresh':False}
        self.content_screen.load(content)

    def _init_menu(self, item, *args, **kwargs):
        provider = self.content_provider
        if 'play' in provider.capabilities:
            item.add_context_menu_item(_("Play"),
                                                        action=self.play_item,
                                                        params={'item':item,
                                                        'mode':'play'})
        item.add_context_menu_item(_("Show playlist"),
                                   action=self.show_playlist,
                                   params={'item':item})

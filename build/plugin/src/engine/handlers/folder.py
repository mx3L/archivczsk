import traceback
from Screens.MessageBox import MessageBox

from item import ItemHandler
from Plugins.Extensions.archivCZSK import _, log
from Plugins.Extensions.archivCZSK.gui.exception import AddonExceptionHandler
from Plugins.Extensions.archivCZSK.engine.items import PExit, PFolder, PSearchItem, PSearch
from Plugins.Extensions.archivCZSK.gui.common import showInfoMessage, showErrorMessage


class FolderItemHandler(ItemHandler):
    handles = (PFolder,)

    def __init__(self, session, content_screen, content_provider):
        info_modes = ['item', 'csfd']
        ItemHandler.__init__(self, session, content_screen, info_modes)
        self.content_provider = content_provider

    def is_search(self, item):
        return isinstance(item, (PSearchItem))

    def _open_item(self, item, *args, **kwargs):
        
        def open_item_success_cb(result):
            def continue_cb(res):
                list_items = []
                args = {}
                list_items.insert(0, PExit())
                self.content_screen.startLoading()
                if not self.content_screen.refreshing:
                    self.content_screen.save()
                else:
                    self.content_screen.refreshing = False

                if self.is_search(item):
                    parent_content = self.content_screen.getParent()
                    if parent_content:
                        parent_content['refresh'] = True

                content = {'parent_it':item,
                           'lst_items':list_items, 
                           'refresh':False,
                           'index':kwargs.get('position', 0)}
                self.content_screen.load(content)
                self.content_screen.stopLoading()
                self.content_screen.showList()
                self.content_screen.workingFinished()
            def pairTrakt_cb(res):
                import json
                import urllib2
                from Plugins.Extensions.archivCZSK.settings import USER_AGENT
                def post_json(url,data,headers={}):
                    postdata = json.dumps(data)
                    headers['Content-Type'] = 'application/json'
                    req = urllib2.Request(url,postdata,headers)
                    req.add_header('User-Agent',USER_AGENT)
                    response = urllib2.urlopen(req)
                    data = response.read()
                    response.close()
                    return data
                
                try:
                    data = json.loads(post_json(params['trakt']['url'], 
                                                data={'code':params['trakt']['code'],'client_id':params['trakt']['client_id'], 'client_secret':params['trakt']['client_secret']},
                                                headers={'Content-Type':'application/json'}))
                    TOKEN = data['access_token']
                    REFRESH_TOKEN = data['refresh_token']
                    expire = data['expires_in'] #seconds
                    created = data['created_at']
                    EXPIRE = expire+created

                    log.logDebug("Get token return token=%s, rtoken=%s, exp=%s"%(TOKEN, REFRESH_TOKEN, EXPIRE))

                    #update settings
                    self.content_provider.video_addon.set_setting(params['settings']['token'], '%s'%TOKEN)
                    self.content_provider.video_addon.set_setting(params['settings']['refreshToken'], '%s'%REFRESH_TOKEN)
                    self.content_provider.video_addon.set_setting(params['settings']['expire'], '%s'%EXPIRE)

                    return showInfoMessage(self.session, params['msg']['success'], 20, continue_cb)
                except:
                    log.logDebug("Pair trakt failed.\n%s"%traceback.format_exc())
                return showErrorMessage(self.session, params['msg']['fail'], 20, continue_cb)
            def continue_cb_normal(res):
                if not list_items and screen_command is not None:
                    self.content_screen.resolveCommand(screen_command, args)
                else:
                    list_items.insert(0, PExit())
                    if screen_command is not None:
                        self.content_screen.resolveCommand(screen_command, args)

                    if not self.content_screen.refreshing:
                        self.content_screen.save()
                    else:
                        self.content_screen.refreshing = False

                    if self.is_search(item):
                        parent_content = self.content_screen.getParent()
                        if parent_content:
                            parent_content['refresh'] = True

                    content = {'parent_it':item,
                            'lst_items':list_items, 
                            'refresh':False,
                            'index':kwargs.get('position', 0)}
                    self.content_screen.load(content)
                    self.content_screen.stopLoading()
                    self.content_screen.showList()
                    self.content_screen.workingFinished()

            list_items, screen_command, args = result
            
            try:
                #client.add_operation("TRAKT_PAIR", {'trakt': {'url':self.tapi.API+'/token', 
                #                                                      'code':self.code, 
                #                                                      'client_id':self.tapi.CLIENT_ID, 
                #                                                      'client_secret': self.tapi.CLIENT_SECRET},
                #                                    'msg': {'pair': msg, 'success':succ, 'fail':fail}, 
                #                                    'settings': {'token': 'trakt_token',
                #                                                 'refreshToken':'trakt_refresh_token', 
                #                                                 'expire':'trakt_token_expire'}})
                #client.add_operation("SHOW_MSG", {'msg': 'some text'},
                #                                  'msgType': 'info|error|warning',     #optional
                #                                  'msgTimeout': 10,                    #optional
                #                                  'canClose': True                     #optional
                #                                 })

                if screen_command is not None:
                   cmd = ("%s"%screen_command).lower()
                   params = args
                   if cmd == "trakt_pair":
                       self.content_screen.stopLoading()
                       return showInfoMessage(self.session, args['msg']['pair'], -1, pairTrakt_cb)
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
                           return showInfoMessage(self.session, args['msg'], msgTimeout, continue_cb_normal, enableInput=canClose)
                       if msgType == 'warning':
                           return showWarningMessage(self.session, args['msg'], msgTimeout, continue_cb_normal, enableInput=canClose)
                       return showInfoMessage(self.session, args['msg'], msgTimeout, continue_cb_normal, enableInput=canClose)
            except:
                log.logError("Execute HACK command failed.\n%s"%traceback.format_exc())
                screen_command = None
                args = {}

            
            if not list_items and screen_command is not None:
                self.content_screen.resolveCommand(screen_command, args)
            else:
                list_items.insert(0, PExit())
                if screen_command is not None:
                    self.content_screen.resolveCommand(screen_command, args)

                if not self.content_screen.refreshing:
                    self.content_screen.save()
                else:
                    self.content_screen.refreshing = False

                if self.is_search(item):
                    parent_content = self.content_screen.getParent()
                    if parent_content:
                        parent_content['refresh'] = True

                content = {'parent_it':item,
                        'lst_items':list_items, 
                        'refresh':False,
                        'index':kwargs.get('position', 0)}
                self.content_screen.load(content)
                self.content_screen.stopLoading()
                self.content_screen.showList()
                self.content_screen.workingFinished()

        @AddonExceptionHandler(self.session)
        def open_item_error_cb(failure):
            log.logError("Folder get_content error cb.\n%s"%failure)
            self.content_screen.stopLoading()
            self.content_screen.showList()
            self.content_screen.workingFinished()
            failure.raiseException()

        self.content_screen.workingStarted()
        self.content_screen.startLoading()
        self.content_screen.hideList()
        self.content_provider.get_content(self.session, item.params, open_item_success_cb, open_item_error_cb)


    def isValidForTrakt(self, item):
        if hasattr(item, 'dataItem') and item.dataItem is not None:
           if 'imdb' in item.dataItem or 'tvdb' in item.dataItem or 'trakt' in item.dataItem:
               return True
        return False

    # action:
    #   - add
    #   - remove
    #   - watched
    #   - unwatched
    def cmdTrakt(self, item, action):
        def finishCb(result):
            if paused:
                self.content_provider.pause()
        def open_item_success_cb(result):
            log.logDebug("Trakt (%s) call success. %s"%(action, result))
            list_items, command, args = result
            if command is not None and command.lower()=='result_msg':
                #{'msg':msg, 'isError':isError}
                if args['isError']:
                    showErrorMessage(self.session, args['msg'], 10, finishCb)
                else:
                    showInfoMessage(self.session, args['msg'], 10, finishCb)
            else:
                finishCb(None)

        def open_item_error_cb(failure):
            log.logDebug("Trakt (%s) call failed. %s"%(action,failure))
            showErrorMessage(self.session, "Operation failed.", 5, finishCb)

        paused = self.content_provider.isPaused()
        try:
            if paused:
                self.content_provider.resume()
            
            if hasattr(item, 'dataItem'): # do it only on item which have additional data
                ppp = { 'cp': 'czsklib', 'trakt':action, 'item': item.dataItem }
                # content provider must be in running state (not paused)
                self.content_provider.get_content(self.session, params=ppp, successCB=open_item_success_cb, errorCB=open_item_error_cb)
            else:
                log.logDebug("Trakt action not supported for this item %s"%item.name);
        except:
            log.logError("Trakt call failed.\n%s"%traceback.format_exc())
            if paused:
                self.content_provider.pause()
    def _init_menu(self, item, *args, **kwargs):
        # TRAKT menu (show only if item got data to handle trakt)
        if 'trakt' in self.content_provider.capabilities and self.isValidForTrakt(item):
            item.add_context_menu_item(_("(Trakt) Add to Watchlist"), action=self.cmdTrakt, params={'item':item, 'action':'add'})
            item.add_context_menu_item(_("(Trakt) Remove from Watchlist"), action=self.cmdTrakt, params={'item':item, 'action':'remove'})
            item.add_context_menu_item(_("(Trakt) Mark as watched"), action=self.cmdTrakt, params={'item':item, 'action':'watched'})
            item.add_context_menu_item(_("(Trakt) Mark as not watched"), action=self.cmdTrakt, params={'item':item, 'action':'unwatched'})

        item.add_context_menu_item(_("Open"), action=self.open_item, params={'item':item})
        if not self.is_search(item) and 'favorites' in self.content_provider.capabilities:
            item.add_context_menu_item(_("Add Shortcut"), action=self.ask_add_shortcut, params={'item':item})
        else:
            item.remove_context_menu_item(_("Add Shortcut"), action=self.ask_add_shortcut, params={'item':item})

    def ask_add_shortcut(self, item):
        self.item = item
        self.session.openWithCallback(self.add_shortcut_cb, MessageBox,
                                      text=_("Do you want to add") + " " + item.name.encode('utf-8') + " " + _("shortcut?"),
                                      type=MessageBox.TYPE_YESNO)

    def add_shortcut_cb(self, cb):
        if cb:
            self.content_provider.create_shortcut(self.item)

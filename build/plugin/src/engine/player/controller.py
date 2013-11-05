import os
import shutil
from twisted.internet.task import deferLater
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

from enigma import  eTimer, iPlayableService, eServiceReference
from Screens.MessageBox import MessageBox
from Components.config import config
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Converter.ServicePositionAdj import ServicePositionAdj
from ServiceReference import ServiceReference
from Plugins.Extensions.archivCZSK import _
from Plugins.Extensions.archivCZSK import log
from Plugins.Extensions.archivCZSK.gui.common import showInfoMessage, showErrorMessage, showYesNoDialog
from util import getBufferInfo

show_info_message = showInfoMessage
show_error_message = showErrorMessage
show_yesno_dialog = showYesNoDialog

def sleep(sec):
    # Simple helper to delay asynchronously for some number of seconds.
    return deferLater(reactor, sec, lambda: None)

    
class BaseVideoPlayerController(object):
    def __init__(self):
        self.video_player = None
        
    def start(self, play_and_download):
        pass
    
    def set_video_player(self, video_player):
        self.video_player = video_player
        
    def is_video_paused(self):
        return self.video_player.SEEK_STATE_PAUSE == self.video_player.seekstate
    
    def sec_to_pts(self, sec):
        return long(sec * 90000)
        
    def pts_to_sec(self, pts):
        return int(pts / 90000)
    
    def pts_to_hms(self, pts):
        sec = self.pts_to_sec(pts)
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        return h, m, s

#  Video Controller Actions called by Video Player  #
##################################################### 

    def seek_fwd(self):
        self._seek_fwd()
            
    def seek_back(self):
        self._seek_back()
            
    def do_seek_relative(self, relative_pts):
        self._do_seek_relative(relative_pts)
                
    def pause_service(self):
        self._pause_service()
            
    def unpause_service(self):
        self._unpause_service()
    
    def do_eof_internal(self, playing):
        self._do_eof_internal(playing)
                
    def exit_video_player(self):
        self._exit_video_player()

        

#  Video Player Actions called by Video Controller  #
#####################################################      

    def _seek_back(self):
        self.video_player._seekBack()
        
    def _seek_fwd(self):
        self.video_player._seekFwd()
    # not sure why but riginal MP doSeek method does nothing, so I use on seeking only doSeekRelative
    def _do_seek(self, pts):
        self.video_player.doSeek(pts)
    
    def _do_seek_relative(self, pts):
        self.video_player._doSeekRelative(pts)
        
    def _unpause_service(self):
        if self.is_video_paused():
            self.video_player.setSeekState(self.video_player.SEEK_STATE_PLAY)  
        
    def _pause_service(self):
        if not self.is_video_paused():
            self.video_player.setSeekState(self.video_player.SEEK_STATE_PAUSE)
    
    def _do_eof_internal(self, playing):
        self.video_player._doEofInternal(playing)
        
    def _exit_video_player(self):
        self.video_player._exitVideoPlayer()


class VideoPlayerController(BaseVideoPlayerController):
    """
    External Video Player Controller for video playback
    Handles play and download mode - restricts user to play only already downloaded content
                                   - automatically stops/resumes playing video according to download state
                                   - handles seeking in downloading video
                                   - updates information about download state
    Handles play mode - respects video settings and boundaries when seeking
    
    @param session: reference to active session for info messages
    @param download: reference for active download to control "download and play"
    @param video_check_interval: set video check interval in seconds
    @param seekable: set if video playing in videoplayer is seekable
    @param pausable: set if video playing in videoplayer is pausable 
    """
    def __init__(self, session, download=None, video_check_interval=5, buffer_time=10, seekable=True, pausable=True, autoplay=True):
        self.video_player = None
        self.video = None
        self.session = session
        self.download = download
        
        self.seekable = seekable
        self.pausable = pausable
        self.autoplay = autoplay
        
        # buffering flag
        self._buffered = True
        
        #flag for manual pause of video
        self._user_pause = False
        
        # checking interval of video when downloading and playing
        self.video_check_interval = video_check_interval * 1000
        
        # check every second when in buffering state
        self.buffer_check_interval = 1 * 1000 
        
        # to update download status
        self.download_interval_check = self.video_check_interval
        
        # to make sure that we dont come to end of file when downloading(deadlock) we set time_limit
        self.time_limit = 5 * 90000 #5 seconds
        
        # set buffer time, its counting after time_limit
        # so realistically we have buffer of size: buffer_time + time_limit 
        self.buffer_time = buffer_time * 90000
        
        # I did couple of tests and seeking is not really precise,
        # so to make sure that we can seek when download we have seek_limit 
        self.seek_limit = 140 * 90000 
        
        # timers for checking and buffering
        self.check_timer = None
        self.check_timer_running = False
        self.buffering_timer = None
        self.buffering_timer_running = False
        
        self.buffered_percent = 0
        self.buffered_time = 0
        
        self.download_position = 0
        self.player_position = 0
        self.video_length = None 
        self.video_length_total = None
        
        log.info('initializing %s', self)
        
    def __repr__(self):
        return "downloading: %s, video_check_interval:%ss buffer_time: %s seekable: %s pausable: %s autoplay: %s" % \
                (self.download is not None, self.video_check_interval, self.buffer_time, self.seekable, self.pausable, self.autoplay)
                
                
    def set_video_player(self, video_player):
        self.video_player = video_player
        sref = ServiceReference(video_player.sref)
        self.sref_url = sref.getPath()
        
    def start(self, play_and_download):
        self.video = self.video_player.video
        
        self.video_length_total = self.video.getCurrentLength()
        self.update_video_length()
        
        # only start video check when we have total length
        if play_and_download and self.video_length_total:
            
            self.buffering_timer = eTimer()
            self.buffering_timer.callback.append(self.check_position)
            self.buffering_timer.callback.append(self._update_download_status)
            self.buffering_timer.callback.append(self._update_info_bar)
            
            self.check_timer = eTimer()
            self.check_timer.callback.append(self.check_position)
            self.check_timer.callback.append(self._update_download_status)
            self.check_timer.callback.append(self._update_info_bar)
            
            self.start_video_check()
        else:
            log.debug("play_and_download=%s video_length_total=%s", play_and_download, self.video_length_total)

        
    def set_video_check_interval(self, interval):
        self.check_video_interval = interval
    
    def start_video_check(self):
        log.debug('starting video_checking')
        self.check_timer.start(self.video_check_interval)
        self.check_timer_running = True
        
        self.download_interval_check = self.video_check_interval
        self.check_position()
        
    def stop_video_check(self):
        log.debug('stopping video_checking')
        if self.check_timer_running:
            self.check_timer.stop()
            self.check_timer_running = False
        
    def start_buffer_check(self):
        log.debug('starting buffer_checking')
        self.buffering_timer.start(self.buffer_check_interval)
        self.buffering_timer_running = True
        
        self.download_interval_check = self.buffer_check_interval
        
    def stop_buffer_check(self):
        log.debug('stopping buffer_checking')
        if self.buffering_timer_running:
            self.buffering_timer.stop()
            self.buffering_timer_running = False
            
    def get_download_position(self):
        if self.video_length_total is None or self.download.length == 0:
            return None
            
        download_pts = long(float(self.download.getCurrentLength()) / float(self.download.length) * self.video_length_total)
        log.debug('download_time: %dh:%02dm:%02ds' , self.pts_to_hms(download_pts))
        self.video_length = download_pts
        return download_pts
        
    def get_player_position(self):
        player_pts = self.video.getCurrentPosition()
        
        if player_pts is None:
            log.debug('cannot retrieve player_position')
            return None
        else:
            #log.debug('player_position: %lu' % player_pts)
            log.debug('player_time: %dh:%02dm:%02ds' , self.pts_to_hms(player_pts))
            self.player_position = player_pts
            return player_pts
    
    def update_video_length(self):
        if self.download is None or self.download.downloaded:
            if self.video_length is None:
                if self.video_length_total is not None:
                    self.video_length = self.video_length_total
        else:
            self.video_length = self.get_download_position()
            
    def is_pts_available(self, pts):
        return pts >= 0 and pts < self.video_length
    

    def _update_download_status(self):
        self.download.status.update(self.download_interval_check / 1000)


#        Video Player Actions called by Video Controller                      
##############################################################
        
    def _update_info_bar(self):
        log.debug('updating infobar')
        if self.video_length is None:
            buffer_slider_percent = 0
        else:
            buffer_slider_percent = int(float(self.video_length) / float(self.video_length_total) * 100)
        info = {
                    'buffer_percent':self.buffered_percent,
                    'buffer_secondsleft':self.buffered_time,
                    'buffer_size':self.buffer_time,
                    'download_speed':self.download.status.speed,
                    'buffer_slider':buffer_slider_percent,
                    'bitrate':0
                }
        self.video_player.updateInfobar(info)
        
    # not sure why but riginal MP doSeek method does nothing, so I use on seeking only doSeekRelative
    def _do_seek(self, pts):
        log.debug('seeking to %dh:%02dm:%02ds' , self.pts_to_hms(pts))
        self.video_player.doSeek(pts)
    
    def _do_seek_relative(self, pts):
        log.debug('seeking to %dh:%02dm:%02ds' , self.pts_to_hms(pts + self.player_position))
        self.video_player._doSeekRelative(pts)
        
    def _unpause_service(self):
        log.debug('unpausing service')
        self.video_player._unPauseService()
        
    def _pause_service(self):
        log.debug('pausing service')
        self.video_player._pauseService()
    
    def _do_eof_internal(self, playing):
        log.debug('stopping timers_eof')
        if self.check_timer_running and hasattr(self, "check_timer"):
            self.check_timer.stop()
        if self.buffering_timer_running and hasattr(self, "buffering_timer"):
            self.buffering_timer.stop()
        log.debug('do_eof_internal')
        self.video_player._doEofInternal(playing)
        
    def _exit_video_player(self):
        log.debug('stopping timers_exit')
        if self.check_timer_running:
            self.check_timer.stop()
        if self.buffering_timer_running:
            self.buffering_timer.stop()
            
        del self.check_timer
        del self.buffering_timer
        log.debug('exiting service')
        self.video_player._exitVideoPlayer()

#           Video Controller Actions called by Video Player
#####################################################################
    def seek_fwd(self):
        if not self.seekable:
            show_info_message(self.session, _("Its not possible to seek in this video"), 3)
        elif self.download is not None and self.download.running:
            show_info_message(self.session, _("Its not possible to use trick seek in downloading video "), 3)
        else:
            self._seek_fwd()
            

    def seek_back(self):
        if not self.seekable:
            show_info_message(self.session, _("Its not possible to seek in this video"), 3)
        elif self.download is not None and self.download.running:
            show_info_message(self.session, _("Its not possible to use trick seek in downloading video "), 3)
        else:
            self._seek_back()
            
    
    def do_seek_relative(self, relative_pts):
        if not self.seekable:
            show_info_message(self.session, _("Its not possible to seek in this video"), 3)
        # whole video available
        elif self.download is None or self.download.downloaded:
            self._do_seek_relative(relative_pts)
                    
            # not working in some situations, disabled for now
            """    
            #we want to seek to pts
            if self.is_pts_available(pts):
                self._do_seek_relative(relative_pts)
            else:
                #If we are seeking over the end of the video, we end
                if pts > self.video_length:
                    self._exit_video_player()
                else:
                    #seek to start
                    self._do_seek_relative(-player_position)
            """
         # downloading video 
        elif self.download and self.download.running:
            player_position = self.get_player_position()
            # disable seek if downloaded video_length or play position is not available 
            if self.video_length is None or player_position is None:
                return
            pts = player_position + relative_pts
            pts_reserve = pts + self.time_limit + self.seek_limit
            if self.is_pts_available(pts_reserve):
                log.debug("position available")
                self._do_seek_relative(relative_pts)
            else:
            #position is not yet available so seek where possible
                log.debug("position not available")
                if pts > self.video_length:
                    log.debug("trying to seek where possible...")
                    possible_seek = self.video_length - player_position - self.time_limit - self.seek_limit
                    if possible_seek > 0:
                        self._do_seek_relative(possible_seek)
                    else:
                        show_info_message(self.session, _("Cannot seek, not enough video is downloaded"), 2)
                        log.debug("cannot seek, not enough video is downloaded")
                else:
                    self._do_seek_relative(-player_position)
                
    def pause_service(self):
        if not self.pausable:
            show_info_message(self.session, _("Its not possible to pause this video"), 2)
        else:
            self._user_pause = True
            self._pause_service()
            
    def unpause_service(self):
        if not self._buffered:
            show_info_message(self.session, _("Cannot unpause, Video is not buffered yet..."), 2)
            #self.check_position()
        else:
            self._user_pause = False
            self._unpause_service()
        
############ Periodically called action by VideoController

    def check_position(self):
        """Checks if buffer is not empty. If it is then automatically pause video until buffer is not empty"""
        
        # if downloading is not finished
        if not self.download.downloaded and self.download.running:
            player_position = self.get_player_position()
            
            #we cannot retrieve player position, so we wait for next check 
            if player_position is None:
                return
            
            download_position = self.get_download_position()
            if download_position is None:
                return
            
            buffered_time = download_position - player_position - self.time_limit
            
            if buffered_time < 0:
                self.buffered_percent = 0
                self.buffered_time = 0 
            elif buffered_time >= self.buffer_time:
                self.buffered_percent = 100
                self.buffered_time = buffered_time
            else:
                self.buffered_percent = int(float(buffered_time) / float(self.buffer_time) * 100)
                self.buffered_time = buffered_time
            
            # We have to wait, so pause video
            if self.buffered_percent < 5:
                log.debug('buffering %d' , self.buffered_percent)
                self._buffered = False
                
                if not self.is_video_paused():
                    self._pause_service()
                    
                if self.check_timer_running:
                    self.stop_video_check()

                if not self.buffering_timer_running:
                    self.start_buffer_check()
                    
            # We can unpause video
            elif self.buffered_percent > 90:
                log.debug('buffered %d' , self.buffered_percent)
                self._buffered = True
                
                if self.is_video_paused() and not self._user_pause:
                    if self.autoplay:
                        self._unpause_service()
                
                if self.buffering_timer_running:
                    self.stop_buffer_check()
                
                if not self.check_timer_running:
                    self.start_video_check()
                    
                               
        # download finished, so stop checking timers
        else:
            self.stop_buffer_check()
            self.stop_video_check()
            self._buffered = True
                

class GStreamerDownloadController(BaseVideoPlayerController):
    """
    Handles gstreamer download mode
    """
    
    def __init__(self, download_path, prebuffer_seconds=0, prebuffer_percent=0):
        
        self.video_player = None
        self.session = None
        self.istreamed = None
        # where we want to save download
        self.download_path = download_path
        # where is gstreamer downloading
        self.gst_download_path = None
        
        # pre-buffering
        self.prebuffer_percent = prebuffer_percent
        self.prebuffer_seconds = prebuffer_seconds
        self.prebufferred_seconds = 0
        self.prebuffered_percent = 0
        self.prebuffering = (self.prebuffer_percent != 0 or self.prebuffer_seconds != 0)
        
        # seek-limit percent
        self.seek_limit_percent = 2
        
        # download/buffer state
        self.download_percent = 0
        self.download_speed = 0
        self.download_finished = False
        self.buffered_percent = 0
        self.buffer_size = 0
        self.temp_length = 0
        
        log.debug("GstreamerDownloadController started")
        
        # register download/buffer events
        self.__event_tracker = None
        
    def get_istreamed(self):
        return self.session.nav.getCurrentService().streamed()
        
    def set_video_player(self, video_player):
        self.video_player = video_player
        self.video = video_player.video
        self.session = video_player.session
        
        ServiceEventTracker(screen=video_player, eventmap=
        {
            iPlayableService.evBuffering: self.__ev_updated_buffer_info,
            iPlayableService.evUser + 21: self.__ev_download_finished,
            iPlayableService.evUser + 22: self.__ev_updated_download_status,
        })
    
    def start(self, play_and_download):
        if self.istreamed is None:
            self.istreamed = self.get_istreamed()
        self.video = self.video_player.video
        
    def __ev_updated_buffer_info(self):
        self.istreamed = self.get_istreamed()
        info = getBufferInfo(self.istreamed)
        self.buffered_percent = info['percentage']
        self._update_info_bar()
    
    # called every 1 seconds
    def __ev_updated_download_status(self):
        if self.istreamed is None:
            return
        info = getBufferInfo(self.istreamed)
        self.download_speed = info['avg_in_rate']
        self.download_percent = info['download_percent']
        self.buffered_percent = info['percentage']
        self.buffer_size = info['size']
        log.debug('download_percent: %d, buffer_size %lu', self.download_percent, self.buffer_size)
        self._update()
    
    def __ev_download_finished(self):
        self.download_finished = True
        show_info_message(self.session, _("Downloading succesfully finished"))
    
    
    def _update(self):
        if self.prebuffering:
            self._prebuffer()
            self._update_playing_state()
        if self.gst_download_path is None:
            self._update_download_location()
        self._update_info_bar()
        
    def _update_download_location(self):
        path = self.istreamed.getBufferCharge()[6]
        if path != "":
            self.gst_download_path = path
            log.debug("download location is %s", self.gst_download_path)
        
    def _prebuffer(self):
        if self.prebuffering:
            self.prebufferred_seconds += 1
            self.prebuffered_percent = int(float(self.download_percent) / float(self.prebuffer_percent) * 100)
            log.debug("Prebuffered seconds : %ds, Prebuffered percent %d%%", self.prebufferred_second, self.prebuffered_percent)
            
    def _update_playing_state(self):
        if self.prebufferred_seconds < self.prebuffer_seconds:
            self.pause_service()
            self.prebuffering = True
        elif self.download_percent < self.prebuffer_percent:
            self.pause_service()
            self.prebuffering = True
        else:
            self.prebuffering = False
            self.unpause_service()
    
    def _update_info_bar(self):
        info = {
                'buffer_percent': self.buffered_percent,
                'buffer_secondsleft':0,
                'buffer_size':self.buffer_size,
                'download_speed':self.download_speed,
                'buffer_slider':self.download_percent,
                'bitrate':0
                }
        self.video_player.updateInfobar(info)
        
    def get_download_position(self):
        total_length = self.video.getCurrentLength()
        if total_length is None:
            return None
        return float(self.download_percent - self.seek_limit_percent) / 100 * total_length

    # not implemented yet..
    def seek_fwd(self):
        if not self.download_finished:
            show_info_message(self.session, _("Its not possible to use trick seek in downloading video "), 3)
        else:
            self._seek_fwd()
    
    def seek_back(self):
        if not self.download_finished:
            show_info_message(self.session, _("Its not possible to use trick seek in downloading video "), 3)
        else:
            self._seek_back()
    
    def do_seek(self):
        pass
    
    def do_seek_relative(self, pts):
        if self.download_percent == 100 or pts < 0:
            self._do_seek_relative(pts)
            return
        
        play_pts = self.video.getCurrentPosition()
        download_pts = self.get_download_position()
        if play_pts is None or download_pts is None:
            show_info_message(self.session, _("Error when trying to seek"), 2)
            return
        
        if (play_pts + pts) < download_pts:
            self._do_seek_relative(pts)
            return
        else:
            want_seek_minutes = pts / 90000 / 60
            can_seek = self.pts_to_hms(download_pts - play_pts)
            can_seek_minutes = can_seek[1]
            show_info_message(self.session, _("Cannot seek") + " " + str(want_seek_minutes) + " " + 
                                            _("minutes forward not enough video is downloaded.\n") + 
                                            _("You can seek maximum") + " " + str(can_seek_minutes) + " " + _("minutes forward"))
                                              
    def unpause_service(self):
        if self.prebuffering:
            log.debug("Forcing unpause... while prebuffering")
            self.prebuffering = False
        self._unpause_service()
    
    # exit actions - save/cancel download depending on download state
    def _ask_cancel_download(self):
        show_yesno_dialog(self.session, _("Download is not finished yet. Do you want to cancel downloading?"), cb=self._cancel_download)
        
    def _cancel_download(self, cb=None):
        if cb:
            # clear tmp gstreamer download path
            if os.path.exists(self.gst_download_path):
                os.remove(self.gst_download_path)
                
            self._exit_video_player()
        
    def _ask_save_download(self):
        show_yesno_dialog(self.session, _("Download is not saved yet. Do you want to save download?"), cb=self._save_download)
    
    def _save_download(self, cb=None):
        if cb:
            # we need to pause playing downloaded file because we want to move
            # it to our download location
            self.pause_service()
            log.debug("saving %s to %s", self.gst_download_path, self.download_path)
            os.system('mv %s %s' % (self.gst_download_path, self.download_path))
            #shutil.move(self.gst_download_path, self.download_path)
            show_info_message(self.session, _("Download was succesfully saved"))
            self._exit_video_player()
        else:
            self._exit_video_player()
            

    def exit_video_player(self):
        # download dont started
        if self.gst_download_path is None:
            self._exit_video_player()
        elif self.gst_download_path is not None and not self.download_finished:
            self._ask_cancel_download()
        elif self.gst_download_path is not None and self.download_finished:
            self._ask_save_download()
            
        
class RTMPController(BaseVideoPlayerController):
    """ 
        Ugly workaround for rtmp seek/pause 
        Needs to be fixed in libgstrtmp or librtmp where the problem probably lies..
        
        Handles seeking in RTMP by restarting stream with added session parameter "start=timeInMS",
        since some rtmp streams played by GStreamer looses sound after seeking """
        
    def __init__(self):
        self.video = None
        self.video_player = None
        self.video_length_total = None
        self._play_pts = 0
        self._seek_pts = 0
        self._base_pts = 0
        self._offset_pts = 0
        self._offset_mode = False
        
        # eplayer gets correct video length of rtmp streams, but after this seeking workaround
        # it cannot get correct video position and starts with 0 position every time after un-pause/seek
        # so we adjust only play position since length is correct
        self._eplayer_mode = False
        
        # With some rtmp streams we cannot get correct video length on gstreamer 0.10
        # Video duration on these streams represents accumulated value of buffered seconds instead of actual video length
        # so we will provide offset_mode_limit which will helps us to determine if we will use offset mode or not
        # Value should be around maximum buffer seconds for rtmp stream(default for librtmp is 30 seconds)
        self._offset_mode_limit = 60 * 1000 * 90
        
        # when we try to seek in quick succession
        # sometimes can happen that we don't have video service set yet
        # so if we want to seek again we need to wait until is current service available 
        self._seek_try_limit = 5
        self._seek_try_delay = 300 #ms

        
    def set_video_player(self, video_player):
        self.video_player = video_player
        self.video = video_player.video
        self.session = video_player.session
        sref = ServiceReference(video_player.sref)
        self.sref_url = sref.getPath()
        self.sref_id = sref.getType()
        self.sref_name = sref.getServiceName()
        self._eplayer_mode = video_player.__class__.__name__ in ('EPlayer3VideoPlayer', 'EPlayer2VideoPlayer')

        
    def _update_video_state(self, play_pts):
        if self.video_length_total is None:
            self.video_length_total = self.video.getCurrentLength()
        if self.video_length_total is not None:
            if self.video_length_total - play_pts <= self._offset_mode_limit:
                self.video_length_total = None
        if self.video_length_total is None or self._eplayer_mode:
            self._offset_mode = True
        else:
            self._offset_mode = False
            
    #@inlineCallbacks   
    def do_seek_relative(self, relative_pts):
        play_pts = self.video.getCurrentPosition()
        #yield sleep(0.1)
        if play_pts is not None:
            self._update_video_state(play_pts)
            if self._offset_mode:
                current_pts = self._base_pts + play_pts
            else:
                current_pts = play_pts

            self._seek_pts = current_pts + relative_pts
            if self.video_length_total is not None:
                if self._seek_pts >= self.video_length_total:
                    return
            if self._seek_pts < 0:
                return
            seek_time = self.pts_to_sec(self._seek_pts) * 1000
            self.rtmp_seek(seek_time)
            
    def unpause_service(self):
        if self._offset_mode:
            current_pts = self._base_pts
        else:
            current_pts = play_pts
        time = self.pts_to_sec(current_pts) * 1000
        self.rtmp_seek(time)
    
    #@inlineCallbacks    
    def pause_service(self):
        play_pts = self.video.getCurrentPosition()
        #yield sleep(0.1)
        if play_pts is not None:
            self._update_video_state(play_pts)
            if self._offset_mode:
                self._base_pts = self._base_pts + play_pts
            else:
                self._play_pts = play_pts
            self._pause_service()
    
    @inlineCallbacks 
    def rtmp_seek(self,seek_time,seek_try=0):
        if self.video.service:
            self.do_rtmp_seek(seek_time)
        elif seek_try < self._seek_try_limit:
            seek_try +=1
            yield sleep(self._seek_try_delay)
            self.rtmp_seek(seek_time, seek_try)
            
    def do_rtmp_seek(self, seek_time):
        log.info('RTMPSeek to %ss', seek_time)
        self.session.nav.stopService()
        seeking_ref = self.sref_url.find(' start=')
        if seeking_ref != -1:
            sref_url = self.sref_url[:seeking_ref] + ' start=%s' % str(seek_time)
        else:
            sref_url = self.sref_url + ' start=%s' % str(seek_time)
        seek_sref = eServiceReference(self.sref_id, 0, sref_url)
        seek_sref.setName(self.sref_name)
        if self._offset_mode:
            self._base_pts = self._seek_pts
            ServicePositionAdj.setBasePts(self._base_pts)
            if not self._eplayer_mode:
                ServicePositionAdj.setBaseLength(self._base_pts)
        self.session.nav.playService(seek_sref)

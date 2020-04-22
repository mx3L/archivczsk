import Queue
import os
import shutil
import urlparse
import random
from datetime import datetime

from Plugins.Extensions.archivCZSK.engine.tools import util
from Plugins.Extensions.archivCZSK.compat import eConnectCallback

from Components.AVSwitch import AVSwitch
from Tools.LoadPixmap import LoadPixmap

from enigma import eTimer, ePicLoad

class PosterProcessing:
    def __init__(self, poster_limit, poster_dir):
        self.poster_limit = poster_limit
        self.poster_dir = poster_dir
        self.got_image_callback = None

        self.poster_files = []

        self._init_poster_dir()

    def _init_poster_dir(self):
        if not os.path.isdir(self.poster_dir):
            try:
                os.makedirs(self.poster_dir)
            except Exception:
                pass
        for filename in os.listdir(self.poster_dir):
            file_path = os.path.join(self.poster_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    def _remove_oldest_poster_file(self):
        _, path = self.poster_files.pop(0)
        print "PosterProcessing._remove_oldest_poster_file: {0}".format(path)
        try:
            os.unlink(path)
        except Exception as e:
            print "PosterProcessing._remove_oldest_poster_file: {0}".format(str(e))

    def _create_poster_path(self):
        dt = datetime.now()
        filename = datetime.strftime(dt, "poster_%y_%m_%d__%H_%M_%S")
        filename += "_"+ str(random.randint(1,9)) + ".jpg"
        dest = os.path.join(self.poster_dir, filename)
        return dest

    def _image_downloaded(self, url, path):
        if path is None:
            return

        if len(self.poster_files) == self.poster_limit:
            print "PosterProcessing._image_downloaded: download limit reached({0})".format(self.poster_limit)
            self._remove_oldest_poster_file()
        print "PosterProcessing._image_downloaded: {0}".format(path)
        self.poster_files.append((url, path))
        self.got_image_callback(url, path)

    def get_image_file(self, poster_url):
        if os.path.isfile(poster_url):
            print "PosterProcessing.get_image_file: found poster path (local)"
            return poster_url

        for idx, (url, path) in enumerate(self.poster_files):
            if (url == poster_url):
                print "PosterProcessing.get_image_file: found poster path on position {0}/{1}".format(idx, self.poster_limit)
                return path
        
        from Plugins.Extensions.archivCZSK.settings import USER_AGENT
        headers = {"User-Agent": USER_AGENT }
        util.download_to_file_async(util.toString(poster_url), self._create_poster_path(), self._image_downloaded, headers=headers, timeout=3)
        return None


class PosterPixmapHandler:
    def __init__(self, poster_widget, poster_processing, no_image_path):
        self.poster_widget = poster_widget
        self.poster_processing = poster_processing
        self.poster_processing.got_image_callback = self._got_image_data
        self.no_image_path = no_image_path
        self._decoding_url = None
        self._decoding_path = None
        self.last_decoded_url = None
        self.last_selected_url = None
        self.picload = ePicLoad()
        self.picload_conn = eConnectCallback(self.picload.PictureData, self._got_picture_data)
        self.retry_timer = eTimer()
        self.retry_timer_conn = eConnectCallback(self.retry_timer.timeout, self._decode_current_image)
        self._max_retry_times = 3
        self._retry_times = 0

    def __del__(self):
        print "PosterImageHandler.__del__"
        self.retry_timer.stop()
        del self.retry_timer_conn
        del self.retry_timer
        del self.picload_conn
        del self.picload

    def _got_image_data(self, url, path):
        self._start_decode_image(url, path)

    def _decode_current_image(self):
        if self._retry_times < self._max_retry_times:
            self._retry_times += 1
            self._start_decode_image(self.last_selected_url, self._decoding_path)
        else:
            self._start_decode_image(None, self.no_image_path)
            self._retry_times = 0
            self.retry_timer.stop()

    def _start_decode_image(self, url, path):
        print "PosterImageHandler._start_decode_image: {0}".format(path)
        if self._decode_image(path):
            print "PosterImageHandler._start_decode_image: started..."
            self.retry_timer.stop()
            self._decoding_path = None
            self._decoding_url = url
        else:
            print "PosterImageHandler._start_decode_image: failed..."
            self._decoding_path = path
            self.retry_timer.start(200)

    def _decode_image(self, path):
        wsize = self.poster_widget.instance.size()
        sc = AVSwitch().getFramebufferScale()
        self.picload.setPara((wsize.width(), wsize.height(),
                              sc[0], sc[1], False, 1, "#00000000"))
        self.last_decoded_url = None
        return 0 == self.picload.startDecode(path)

    def _got_picture_data(self, picInfo=None):
        picPtr = self.picload.getData()
        if picPtr is not None:
            print "PosterImageHandler._got_picture_data, success"
            self.poster_widget.instance.setPixmap(picPtr)
            self.last_decoded_url = self._decoding_url
        else:
            print "PosterImageHandler._got_picture_data, failed"
            self.last_decoded_url = None
        self._decoding_url = None

    def set_image(self, url):
        print "PosterImageHandler.set_image: {0}".format(url)
        if self.last_selected_url:
            if self.last_selected_url == url:
                print "PosterImageHandler.set_image: same url as before"
                return
        self.last_selected_url = url
        if self.last_decoded_url:
            if self.last_decoded_url == url:
                print "PosterImageHandler.set_image: same decoded url as before"
                return

        self.retry_timer.stop()

        print "PosterImageHandler.set_image: {0}".format(url)
        if url is None:
            imgPtr = LoadPixmap(path=self.no_image_path, cached=True)
            if imgPtr:
                self.poster_widget.instance.setPixmap(imgPtr)
        else:
            path = self.poster_processing.get_image_file(url)
            print "PosterImageHandler.set_image: path={0}".format(path)
            self.poster_widget.instance.setPixmap(None)
            self.last_decoded_url = None
            # sync 
            if path is not None:
                self._start_decode_image(url, path)


# -*- coding: utf-8 -*-
#########################################################
# SERVICE : frames.py                                   #
#           Extract frames from video with avconv       #
#           I. Helwegen 2017                            #
#########################################################

####################### IMPORTS #########################
from avconv import avconv
from tempfile import gettempdir
from time import strftime
import os

#########################################################

####################### GLOBALS #########################

#########################################################
# Class : frames                                        #
#########################################################
class frames(avconv):
    def __init__(self, file, debug = False, quickstep = True):
        self.AV_TIME_BASE = 1000000
        self.debug = debug
        self.container = None
        self.streams = None
        self.video_stream = None
        self.frame_rate = 1
        self.time_base = 1
        self.frame_count = 0
        self.current_frame = 0
        self.current_sec = 0
        self.gop = 12
        self.tempdir=gettempdir()
        self.imagecounter = 0
        self.images=[]
        super(frames, self).__init__(file)

        if self.available():
            self._open_file(file)        

        if self.video_stream:
            self.frame_rate = self._get_frame_rate()
            self.time_base = self._get_time_base()
            self.frame_count = self._get_frame_count()
            if quickstep:
                self.gop = self._find_gop()    
            if self.debug:
                self._print_info()

    def __del__(self):
        super(frames, self).__del__()
        self._delimages()
        self.images={}
        self.imagecounter = 0
        self.tempdir=""
        self.debug = False
        self.container = None
        self.video_stream = None
        self.frame_rate = 1
        self.time_base = 1
        self.frame_count = 0
        self.current_frame = 0
        self.current_sec = 0
        self.gop = 1

    def av_installed(self):
        return self.available()

    def get_frame_time(self, target_sec, genimage=True, image="", keepimage=False):
        if self.debug:
            target_pts = int((target_sec/self.time_base)) + self.container.start_time
            target_frame = self._time_to_frame(target_sec)
            print("Target sec:", target_sec, ", Target pts:", target_pts, ", target frame:", target_frame)
        if genimage or image:
            image=self._generateimage(image, keepimage)
            if self._seek_frame(target_sec, image):
                return image
        else:
            self._probe_frame_time(target_sec)
        return None

    def get_frame(self, target_frame, genimage=True, image="", keepimage=False):
        target_sec = self._frame_to_time(target_frame)
        if self.debug:
            target_pts = self._frame_to_pts(target_frame)
            print("Target sec:", target_sec, ", Target pts:", target_pts, ", target frame:", target_frame)
        if genimage or image:
            image=self._generateimage(image, keepimage)
            if self._seek_frame(target_sec, image):
                return image
        else:
            self._probe_frame_time(target_sec)
        return None

    def get_next_frame(self, genimage=True, image="", keepimage=False):
        current_frame = self.current_frame
        target_frame = current_frame
        while (target_frame < self.frame_count) and (current_frame == self.current_frame):
            self._probe_frame(target_frame)
            target_frame +=self.gop
        if genimage or image:
            image=self._generateimage(image, keepimage)
            if self._seek_frame(self.current_sec, image):
                return image
        return None

    def get_previous_frame(self, genimage=True, image="", keepimage=False):
        current_frame = self.current_frame
        target_frame = current_frame
        while (target_frame >= 0) and (current_frame == self.current_frame):
            self._probe_frame(target_frame)
            target_frame -=self.gop
        if genimage or image:
            image=self._generateimage(image, keepimage)
            if self._seek_frame(self.current_sec, image):
                return image
        return None

    def get_time_info(self):
        if self.available():
            keyframeinterval = self.gop//self.frame_rate
            return (self.container.start_time, self.container.duration, keyframeinterval)
        else:
            return (0, -1, 0)

    def get_current_frame(self):
        return self.current_frame

    def get_current_time(self):
        return self.current_sec

    def get_frame_rate(self):
        if self.available():
            return self.frame_rate
        else:
            return 50.0

    def DeleteImage(self, image):
        for imagefile in self.images:
            if os.path.isfile(imagefile) and (imagefile == image):
                os.remove(imagefile)
        return

    def _probe_frame(self, target_frame):
        target_sec = self._frame_to_time(target_frame)
        return self._probe_frame_time(target_sec)

    def _probe_frame_time(self, target_sec):
        frame = None

        if self.available() and self.video_stream:
            frame = self.probe_frame(self.video_stream, target_sec)

        if frame:
            self.current_sec = frame.time
            self.current_frame = self._pts_to_frame(frame.pts)
            if self.debug:
                print("time:", self.current_sec)
                #print "time_base:", frame.time_base
                #print "index:", frame.index
                print("pts:", frame.pts)
                print("dts:", frame.dts)
                print("frame:", self.current_frame)
        return frame

    def _generateimage(self, image = "", keepimage = False, pre = "tempframe_", ext = ".png"):
        if image:
            name = image
        else:
            name=pre + str(self.imagecounter).zfill(5) + "_" + strftime("%Y%m%d%H%M%S") + ext
        self.imagecounter += 1
        if self.imagecounter < 99999:
            filename=os.path.join(self.tempdir, name)
            if not keepimage:
                self.images.append(filename)
        else:
            self.imagecounter = 99999
            return os.devnull
        return filename

    def _delimages(self):
        for imagefile in self.images:
            if os.path.isfile(imagefile):
                os.remove(imagefile)
        self.imagecounter = 0
        return

    def _seek_frame(self, target_sec, image=os.devnull):
        frame = self._probe_frame_time(target_sec)

        if frame:
            out = self.convframes(self.video_stream, image, frame.time, 1)
        else:
            out = False

        return out

    def _open_file(self, file):
        self.container = self.probe_format()
        if self.container:
            self.streams = self.probe_streams()
        if self.streams:
            self.video_stream = self.streams.get_stream('video')
        return

    def _print_info(self):
        print("===============")
        print("Duration:", self.container.duration)
        print("Start time:", self.container.start_time)
        print("Stream_Rate:", float(self.video_stream.rate))
        print("Time_base:", self.time_base)
        print("GOP size:", self.gop)
        print("Frame rate:", self.frame_rate)
        print("Frame count:", self.frame_count)
        print("===============")

    def _time_to_frame(self, ftime):
        return int((ftime-self.container.start_time) * self.frame_rate)

    def _frame_to_time(self, frame):
        return float((frame/self.frame_rate)) + self.container.start_time

    def _pts_to_frame(self, pts):
        return int(pts * self.time_base * self.frame_rate) - int(self.container.start_time * self.time_base * self.frame_rate)

    def _pts_to_frame2(self, pts, time_base, frame_rate, start_time):
        return int(pts * time_base * frame_rate) - int(start_time * time_base * frame_rate)

    def _frame_to_pts(self, frame):
        if self.container:
            target_sec = frame//self.frame_rate
            return int((target_sec/self.time_base)) + self.container.start_time
        else:
            return 0

    def _get_frame_rate(self):
        if self.video_stream:
            if self.video_stream.average_rate.denominator and self.video_stream.average_rate.numerator:
                return float(self.video_stream.average_rate)
            if self.video_stream.time_base.denominator and self.video_stream.time_base.numerator:
                return 1.0 / float(self.video_stream.time_base)
            else:
                return 0
        else:
            return 0

    def _get_time_base(self):
        if self.video_stream:
            if self.video_stream.time_base.denominator and self.video_stream.time_base.numerator:
                return float(self.video_stream.time_base)
            else:
                return 0   
        else:
            return 0

    def _get_frame_count(self):
        if self.container and self.video_stream:
            if self.video_stream.frames:
                return self.video_stream.frames
            elif self.video_stream.duration:
                if self.video_stream.time_base:
                    tb = float(self.video_stream.time_base)
                else:
                    tb = 1 / float(self.AV_TIME_BASE)
                return self._pts_to_frame2(self.video_stream.duration, tb, self._get_frame_rate(), 0)
            elif self.container.duration:
                return int(self.container.duration * self._get_frame_rate())
            else:
                return 0
        else:
            return 0

    def _find_gop(self):
        self.get_frame(0, False)
        frame1=self.current_frame
        self.get_next_frame(False)
        frame2=self.current_frame
        if (frame2-frame1 > 0):
            return (frame2-frame1)
        else:
            return self.gop

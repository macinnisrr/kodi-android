# -*- coding: utf-8 -*-
#########################################################
# SERVICE : avconv.py                                   #
#           executed avconv/ ffmpeg commands            #
#           I. Helwegen 2017                            #
#########################################################

####################### IMPORTS #########################
import subprocess
import re
import os
from platform import system
from json import loads
from fractions import Fraction

####################### GLOBALS #########################

#########################################################
# Class : avconv                                        #
#########################################################
class avconv(object):
    def __init__(self, filename, prefer_ffmpeg = False):
        self.prefer_ffmpeg = prefer_ffmpeg
        self.basename = None
        self.probe_basename = None
        self._versions = None
        self._paths = {}
        self.filename = filename
        self.fpp = -1
        self._determine_executables()

    def __del__(self):
        self.prefer_ffmpeg = False
        self.basename = None
        self.probe_basename = None
        self._versions = None
        self._paths = {}
        self.filename = ""

    def available(self):
        return self.conv_available and self.probe_available

    def probe(self, args = []):
        if os.path.isfile(self.filename) and self.probe_available:
            try:
                cmd = [self.probe_executable] + args + [self.filename]
                out, _ = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
            except OSError:
                return False
        else:
            return False

        return out

    def probe_format(self):
        result = self.probe(["-show_format","-print_format","json"])
        if result:
            try:
                res = loads(self._stripjson(result))
            except:
                return False
            return format(res)
        return False

    def probe_streams(self):
        result = self.probe(["-show_streams","-print_format","json"])
        if result:
            try:
                res = loads(self._stripjson(result))
            except:
                return False
            return streams(res)
        return False

    def probe_frame(self, stream, frmtime):
        index = stream.index
        frameindex = -1
        keyframe = False
        if self.fpp < 0:
            fpp = 1
        else:
            fpp = self.fpp
        while not keyframe:
            if float(frmtime) <= float(0):
                prbtime = "%+#" + str(fpp)
            else:
                prbtime = str(frmtime) + "%+#" + str(fpp) # "03:27%+#1"
            result = self.probe(["-select_streams",str(index),"-show_frames","-read_intervals",prbtime,"-print_format","json"])
            if result:
                try:
                    res = loads(self._stripjson(result))
                    frames = res['frames']
                    if len(frames) == 0:
                        fpp += 1
                    else:
                        for i,aframe in enumerate(frames):
                            if frame(aframe).key_frame:
                                keyframe = True
                                frameindex = i
                                break
                            else:
                                fpp += 1
                        if len(frames)>2 and frameindex == 0:
                            fpp -= 1
                except:
                    return False
                #keyframe = True
            else:
                return False
        self.fpp = fpp
        if frameindex >= 0:
            return frame(frames[frameindex])
        else:
            return False

    # get picture:
    # ffmpeg -ss 202.666667 -i max.mp4 -frames:v 1 out1.png -y
    #
    # or something like this:
    # ffmpeg -ss 202.666667 -i max.mp4 -f image2pipe -frames:v 1 -
    def conv(self, outfile, globargs = [], inargs = [], outargs = []):
        if os.path.isfile(self.filename) and self.conv_available:
            try:
                cmd = [self.executable] + globargs + inargs + ["-i",self.filename] + outargs + [outfile]
                out, _ = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
            except OSError:
                return False
        else:
            return False

        return out

    def convframes(self, stream, outfile, frmtime = 0, nframes = 1, outformat = "", overwrite = True, globargs = [], inargs = [], outargs = []):
        index = stream.index

        if overwrite:
            globargs = ["-y"] + globargs

        fname, ext = os.path.splitext(outfile)
        if not outformat and not ext:
            outformat = "image2"

        inargs = ["-ss", str(frmtime)] + inargs

        outargs = ["-frames:"+str(index),str(nframes)] + outargs
        if outformat:
            outargs = ["-f",outformat] + outargs

        return self.conv(outfile, globargs, inargs, outargs)

    def _stripjson(self, s):
        js = s.find('\n{')+1
        je = s.rfind('\n}')+2
        return s[js:je]

    def _determine_executables(self):
        programs = ['avprobe', 'avconv', 'ffmpeg', 'ffprobe']

        self._paths = self._getlocation(programs)

        if not self._paths:
            print(
                'ffmpeg does not exist! '
                'Continuing without avconv/ffmpeg.')
            self._versions = {}
            return

        self._versions = dict(
            (p, self._get_exe_version(self._paths[p], args=['-version'])) for p in self._paths)

        if self.prefer_ffmpeg:
            prefs = ('ffmpeg', 'avconv')
        else:
            prefs = ('avconv', 'ffmpeg')
        for p in prefs:
            if p in self._versions:
                self.basename = p
                break

        if self.prefer_ffmpeg:
            prefs = ('ffprobe', 'avprobe')
        else:
            prefs = ('avprobe', 'ffprobe')
        for p in prefs:
            if p in self._versions:
                self.probe_basename = p
                break

    def _getlocation(self, programs):
        paths = {}
        for program in programs:
            if system() == "Windows":
                prog = program + ".exe"
            else:
                prog = program
            for path in os.environ["PATH"].split(os.pathsep):
                if os.path.exists(os.path.join(path, prog)):
                    paths[program] = os.path.join(path, prog)

        return paths

    def _get_exe_version(self, exe, args=['-version'],
                    version_re=None, unrecognized='present'):
        try:
            out, _ = subprocess.Popen(
                [exe] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
        except OSError:
            return False
        if isinstance(out, bytes):  # Python 2.x
            out = out.decode('ascii', 'ignore')
        if version_re is None:
            version_re = r'version\s+([-0-9._a-zA-Z]+)'
        m = re.search(version_re, out)
        if m:
            return m.group(1)
        else:
            return unrecognized

    @property
    def conv_available(self):
        return self.basename is not None

    @property
    def executable(self):
        return self._paths[self.basename]

    @property
    def probe_available(self):
        return self.probe_basename is not None

    @property
    def probe_executable(self):
        return self._paths[self.probe_basename]

#########################################################
# Class : format                                        #
#########################################################
class format(object):
    def __init__(self, infmt):
        try:
            self.streams = int(infmt['format']['nb_streams'])
        except:
            self.streams = 0

        try:
            self.programs = int(infmt['format']['nb_programs'])
        except:
            self.programs = 0

        try:
            self.start_time = float(infmt['format']['start_time'])
        except:
            self.start_time = 0.0

        try:
            self.duration = float(infmt['format']['duration'])
        except:
            self.duration = 0.0

        try:
            self.size = int(infmt['format']['size'])
        except:
            self.size = 0

        try:
            self.bit_rate = int(infmt['format']['bit_rate'])
        except:
            self.bit_rate = 0

#########################################################
# Class : streams                                       #
#########################################################
class streams(object):
    def __init__(self, instrms):
        self.streams = {}
        for strm in instrms['streams']:
            try:
                index = strm['index']
                self.streams[index] = stream(strm)
            except:
                pass

    def get_stream(self, type):
        return self.streams[next(s for s in self.streams if self.streams[s].codec_type.lower() == type.lower())]

#########################################################
# Class : stream                                        #
#########################################################
class stream(object):
    def __init__(self, instrm):
        try:
            self.index = instrm['index']
        except:
            self.index = ""
        try:

            self.codec_type = instrm['codec_type']
        except:
            self.codec_type = ""

        try:
            self.codec_name = instrm['codec_name']
        except:
            self.codec_name = ""        

        try:
            self.average_rate = Fraction(instrm['avg_frame_rate'])
            self.rate = self.average_rate
        except:
            self.average_rate = 0
            self.rate = 0

        try:
            self.start_time = instrm['start_pts']
        except:
            self.start_time = 0

        try:
            self.duration = instrm['duration_ts']
        except:
            self.duration = 0

        try:
            self.frames = instrm['nb_frames']
        except:
            self.frames = 0

        try:
            self.profile = instrm['profile']
        except:
            self.profile = ""

        try:
            self.time_base = Fraction(instrm['time_base'])
        except:
            self.time_base = ""   

        try:
            self.height = instrm['height']
        except:
            self.height = ""

        try:
            self.width = instrm['width']
        except:
            self.width = ""         

#########################################################
# Class : frame                                         #
#########################################################
class frame(object):
    def __init__(self, infrm):
        try:
            self.pkt_pos = infrm['pkt_pos']
        except:
            self.pkt_pos = 0

        try:
            self.pkt_size = infrm['pkt_size']
        except:
            self.pkt_size = 0 

        try:
            self.key_frame = infrm['key_frame']
        except:
            self.key_frame = 0

        try:
            self.pts = infrm['pkt_pts']
        except:
            self.pts = 0

        try:
            self.time = infrm['pkt_pts_time']
        except:
            self.time = 0

        try:
            self.dts = infrm['best_effort_timestamp']
        except:
            self.dts = 0
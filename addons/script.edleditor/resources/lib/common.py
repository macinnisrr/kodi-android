# -*- coding: utf-8 -*-
#########################################################
# SCRIPT  : common.py                                   #
#           Common functions for edleditor              #
#           I. Helwegen 2017                            #
#########################################################

####################### IMPORTS #########################
import os, subprocess
import xbmc, xbmcaddon, xbmcgui
from threading import Timer

#########################################################
####################### GLOBALS #########################
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('id')
__path__ = __addon__.getAddonInfo('path')
__datapath__ = xbmc.translatePath(os.path.join('special://temp/', __addonname__))
__logfile__ = os.path.join(__datapath__, __addonname__ + '.log')
__LS__ = __addon__.getLocalizedString

IconStop = xbmc.translatePath(os.path.join(__path__, 'resources', 'media', 'stop.png'))
IconError = xbmc.translatePath(os.path.join(__path__, 'resources', 'media', 'error.png'))

OSD = xbmcgui.Dialog()

MSG = 'message'
MSGCNT = 'mescount'

__parameterwindow__ = 10000
#########################################################

DLG_TYPE_FOLDER = 0
DLG_TYPE_FILE = 1

STS_NONE = 0
STS_NOEDL = 1
STS_DIS   = 2
STS_ENA   = 3

EDLEXT = ".edl"
TXTEXT = ".txt"
DISEDLEXT = ".ed_"
DISTXTEXT = ".tx_"

__video_extensions__ = xbmc.getSupportedMedia('video')

### Use to select video file (mask= videoformat)
### Defaultpath is setting
def GUI_BrowseVideos(title='Videos', defaultPath=None, dialogType=DLG_TYPE_FILE, mask=__video_extensions__):
        """
        @param title:
        @param dialogType: Integer - 0 : ShowAndGetDirectory
                                     1 : ShowAndGetFile
                                     2 : ShowAndGetImage
                                     3 : ShowAndGetWriteableDirectory
        shares         : string or unicode - from sources.xml. (i.e. 'myprograms')
        mask           : [opt] string or unicode - '|' separated file mask. (i.e. '.jpg|.png')
        useThumbs      : [opt] boolean - if True autoswitch to Thumb view if files exist.
        treatAsFolder  : [opt] boolean - if True playlists and archives act as folders.
        default        : [opt] string - default path or file.
        enableMultiple : [opt] boolean - if True multiple file selection is enabled.
        """
        destFile = OSD.browse(dialogType, title, 'videos', mask, True, True, defaultPath)
        if destFile == defaultPath:
            destFile = ""
        return destFile

def GUI_SelectAction(Status):
    opt = []
    if Status == STS_NOEDL:
        heading = __LS__(60002)
        opt.append(__LS__(60005)) 
    elif Status == STS_DIS:
        heading = __LS__(60003)
        opt.append(__LS__(60006))
    elif Status == STS_ENA:
        heading = __LS__(60004)
        opt.append(__LS__(60007))
        opt.append(__LS__(60008))

    selected = OSD.select(heading, opt)

    return selected

def GUI_Progress(title, line2):
    pDialog = xbmcgui.DialogProgress()
    pDialog.create(title, line2)

    return pDialog

def GUI_Input(title, default):
    return OSD.input(title, default, type=xbmcgui.INPUT_ALPHANUM) 

def GetStatus(videofile):
    status = STS_NONE
    editfile = ""
    __prefer_edl__ = True if __addon__.getSetting('prefer_edl').upper() == 'TRUE' else False
    if os.path.exists(videofile):
        name, ext = os.path.splitext(videofile)
        edlfile = name + EDLEXT
        txtfile = name + TXTEXT
        disedlfile = name + DISEDLEXT
        distxtfile = name + DISTXTEXT
        if __prefer_edl__:
            if os.path.exists(edlfile):
                editfile = edlfile
                status = STS_ENA
            elif os.path.exists(txtfile):
                editfile = txtfile
                status = STS_ENA
            elif os.path.exists(disedlfile):
                editfile = disedlfile
                status = STS_DIS
            elif os.path.exists(distxtfile):
                editfile = distxtfile
                status = STS_DIS
            else:
                editfile = edlfile
                status = STS_NOEDL
        else:
            if os.path.exists(txtfile):
                editfile = txtfile
                status = STS_ENA
            elif os.path.exists(edlfile):
                editfile = edlfile
                status = STS_ENA 
            elif os.path.exists(distxtfile):
                editfile = distxtfile
                status = STS_DIS  
            elif os.path.exists(disedlfile):
                editfile = disedlfile
                status = STS_DIS
            else:
                editfile = txtfile
                status = STS_NOEDL
    return status, editfile

def EnableEDL(editfile):
    neweditfile = ""
    name, ext = os.path.splitext(editfile)
    if ext.lower() == DISEDLEXT:
        neweditfile = name + EDLEXT
        os.rename(editfile, neweditfile)
    elif ext.lower() == DISTXTEXT:
        neweditfile = name + TXTEXT
        os.rename(editfile, neweditfile)
    return neweditfile

def DisableEDL(editfile):
    neweditfile = ""
    name, ext = os.path.splitext(editfile)
    if ext.lower() == EDLEXT:
        neweditfile = name + DISEDLEXT
        os.rename(editfile, neweditfile)
    elif ext.lower() == TXTEXT:
        neweditfile = name + DISTXTEXT
        os.rename(editfile, neweditfile)
    return neweditfile

def PrettyIndex(item, framebased):
    pretty = ""
    if framebased:
        pretty = "#" + str(int(item))
    else:
        h = int(item//3600)
        m = int((item%3600)//60)
        s = int(item%60)
        t = int(round(item%1*1000))
        pretty = str(h)+":"+str(m).zfill(2)+":"+str(s).zfill(2)+'.'+str(t).zfill(3)
    return pretty

def PrettyIndexFrm(item, framerate):
    h = int(item//3600)
    m = int((item%3600)//60)
    s = int(item%60)
    t = int(round(item%1*1000))
    pretty = str(h)+":"+str(m).zfill(2)+":"+str(s).zfill(2)+'.'+str(t).zfill(3)
    if framerate>0:
        frame = " (#"+str(int(item*framerate))+")"
        pretty = pretty + frame
    return pretty

def Pretty2Index(pretty, framebased):
    item = 0
    # remove #
    if (pretty[0] == "#"):
        pretty = pretty[1:]
    if framebased:
        try:
            item = int(pretty)
        except:
            pass
    else:
        try:
            prettysplit=pretty.split(':')
            if len(prettysplit)>1:
                if len(prettysplit)>2:
                    h = float(prettysplit[0])
                    m = float(prettysplit[1])
                    s = float(prettysplit[2])
                else:
                    h = 0.0
                    m = float(prettysplit[0])
                    s = float(prettysplit[1])
                item = h*3600+m*60+s
            else:
                item = float(prettysplit[0])
        except:
            pass
    return item

#########################################################
# Functions : Local                                     #
#########################################################
def num(s):
    try:
        return int(s)
    except ValueError:
        return 0

def setParam(param, value):
    xbmcgui.Window(__parameterwindow__).setProperty(__addonname__ + '_' + param, value)

def getParam(param):
    return xbmcgui.Window(__parameterwindow__).getProperty(__addonname__ + '_' + param)

def clearParam(param):
    xbmcgui.Window(__parameterwindow__).clearProperty(__addonname__ + '_' + param)

def incParam(param):
    val = num(getParam(param))
    val += 1
    setParam(param,str(val))

def notifyOSD(header, message, icon=xbmcgui.NOTIFICATION_INFO):
    OSD.notification(header.encode('utf-8'), message.encode('utf-8'), icon)

def writeLog(message, level=xbmc.LOGNOTICE, forcePrint=False):
    if getParam(MSG) == message and not forcePrint:
        incParam(MSGCNT)
        return
    else:
        if num(getParam(MSGCNT)) > 0:
            xbmc.log('%s: >>> Last message repeated %s time(s)\n' % (__addonname__, num(getParam(MSGCNT))), level)
        setParam(MSG, message)
        clearParam(MSGCNT)
        xbmc.log('%s: %s' % (__addonname__, message.encode('utf-8')), level)    

#########################################################


#########################################################
# Class : aTimer                                        #
#########################################################
class aTimer(object):
    def __init__(self, interval, repeat, function, *args, **kwargs):
        self._timer     = None
        self.interval   = interval
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.repeat     = repeat
        self.start()

    def _run(self):
        self.is_running = False
        if self.repeat:
            self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys, os, traceback, subprocess
#from lib.yd_private_libs import util, servicecontrol, updater
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import re
import urllib
import datetime, time

ADDON = xbmcaddon.Addon(id='script.module.youtube.dl')
DEBUG = ADDON.getSetting('debug') == 'true'

#sys.path.insert(1, '../script.module.youtube.dl/lib/')
sys.path.append('../script.module.youtube.dl/lib/')

###############################################################################
# FIX: xbmcout instance in sys.stderr does not have isatty(), so we add it
###############################################################################

class replacement_stderr(sys.stderr.__class__):
    def isatty(self):
        return False


sys.stderr.__class__ = replacement_stderr

###############################################################################
# FIX: _subprocess doesn't exist on Xbox One
###############################################################################

try:
    import _subprocess
except ImportError:
    from yd_private_libs import _subprocess

###############################################################################

try:
    import youtube_dl
except:
    util.ERROR('Failed to import youtube-dl')
    youtube_dl = None

###############################################################################
# FIXES: datetime.datetime.strptime evaluating as None in Kodi
###############################################################################

try:
    datetime.datetime.strptime('0', '%H')
except TypeError:
    # Fix for datetime issues with XBMC/Kodi
    class new_datetime(datetime.datetime):
        @classmethod
        def strptime(cls, dstring, dformat):
            return datetime.datetime(*(time.strptime(dstring, dformat)[0:6]))

    datetime.datetime = new_datetime
###############################################################################


perc = 0
addon = xbmcaddon.Addon()
addonID = addon.getAddonInfo('id')
addonFolder = xbmc.translatePath('special://home/addons/'+addonID).decode('utf-8')
finalformat = ""

def getDownloadPath(use_default=None):
    if use_default is None:
        use_default = not ADDON.getSetting('confirm_download_path') == True
    path = ADDON.getSetting('last_download_path')
    if path:
        if not use_default:
            new = xbmcgui.Dialog().yesno("Use Default?", "Use default path:", path, "Or choose a new path?", "Default", "New")
            if new:
                path = ''
    if not path:
        path = xbmcgui.Dialog().browse(3, "Select Directory", 'files', '', False, True)
    if not path:
        return
    ADDON.setSetting('last_download_path', path)
    return path

class MyLogger(object):
    def debug(self, msg):
        global perc
        global pDialog
        perc += 20
        LOG("dbg "+msg, debug=True)
        pDialog.update(perc, msg)

    def warning(self, msg):
        global perc
        global pDialog
        global finalformat
        perc += 20
        LOG("wrn "+msg, debug=True)
        pDialog.update(perc, msg)
        if 'merged into mkv' in msg:
            finalformat='mkv'
        elif 'merged into webm' in msg:
            finalformat='webm'
        elif 'merged into mp4' in msg:
            finalformat='mp4'

    def error(self, msg):
        global perc
        global pDialog
        perc += 20
        LOG("err "+msg, debug=True)
        pDialog.update(perc, msg)

def my_hook(d):
    global pDialog
    if d['status'] == 'downloading':
        pDialog.update(int(float(d['_percent_str'][:-1])), d['_eta_str'])

def LOG(msg,debug=False):
    if debug and not DEBUG: return
    xbmc.log('context.youtube.dl.menu: {0}'.format(msg), xbmc.LOGNOTICE)

def ERROR(msg=None,hide_tb=False):
    if msg: LOG('ERROR: {0}'.format(msg))
    if hide_tb and not DEBUG:
        errtext = sys.exc_info()[1]
        LOG('%s::%s (%d) - %s' % (msg or '?', sys.exc_info()[2].tb_frame.f_code.co_name, sys.exc_info()[2].tb_lineno, errtext))
        return
    xbmc.log(traceback.format_exc(), xbmc.LOGNOTICE)

class main():
    def __init__(self):
        self.download()

    def download(self):
        ytid = False
        title = xbmc.getInfoLabel('Player.Title')
        YOUTUBE_VIDEO_URL = 'http://www.youtube.com/v/%s'

        if xbmc.Player().isPlaying():
            url = xbmc.Player().getPlayingFile()
            thumbnail = xbmc.getInfoLabel('Player.Art(thumb)')
            if 'ytimg' in thumbnail:
                ytid = thumbnail.rsplit('/',2)
                ytid = ytid[-2]

        if not ytid:
            #Check if listitem property exists
            if not sys.listitem:
                xbmc.log('context.youtube.dl.menu: Could not obtain video id', xbmc.LOGERROR)
                return 1

            #Listitem exists, obtaining filename/url to extract video id
            plugin_url = sys.listitem.getfilename()
            #urldecoding url 5 times to account for nested addon-calls
            plugin_url = urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(urllib.unquote(plugin_url)))))
            xbmc.log('context.youtube.dl.menu: '+'ListItem.FileNameAndPath: |%s|' % plugin_url, xbmc.LOGNOTICE)
            if plugin_url:
                result = re.search('video_id=(?P<video_id>[a-zA-Z0-9_-]+)', plugin_url)
                if result:
                    xbmc.log('context.youtube.dl.menu: '+'Found video_id in url: |%s|' % result.group('video_id'), xbmc.LOGNOTICE)
                    video_id=result.group('video_id')
                else:
                    xbmc.log('context.youtube.dl.menu: '+'video_id not found in url '+plugin_url, xbmc.LOGERROR)
                    xbmcgui.Dialog().notification('youtube-dl error','video_id not found in url',os.path.join(addonFolder, "icon.png"),5000,True)
                    return 1
                        
                if video_id:
                    ytid = video_id
                else:
                    xbmc.log('context.youtube.dl.menu: '+'video_id not found', xbmc.LOGERROR)
                    xbmcgui.Dialog().notification('youtube-dl error','video_id not found in url',os.path.join(addonFolder, "icon.png"),5000,True)
                    return 1
            else:
                xbmc.log('context.youtube.dl.menu: '+'Plugin URL not found', xbmc.LOGERROR)
                xbmcgui.Dialog().notification('youtube-dl error','url not found',os.path.join(addonFolder, "icon.png"),5000,True)
                return 1

            title = sys.listitem.getLabel()
            thumbnail = sys.listitem.getArt('thumb')
            
        url=YOUTUBE_VIDEO_URL % ytid
 
        #Debuginfo
        info = {'url': url, 'title': title, 'thumbnail': thumbnail, 'id': ytid, 'media_type': 'video'}
        LOG(repr(info), debug=True)

        targetdir = getDownloadPath()

        #checking if configured target directory is writeable
        f = xbmcvfs.File(os.path.join(targetdir, "koditmp.txt"), 'w')
        writeconfirm = f.write(str("1"))
        f.close()
        if writeconfirm:
          #cleaning up
          xbmcvfs.delete(os.path.join(targetdir, "koditmp.txt"))
        else:
          LOG("Destination path "+targetdir+" not writeable, aborting", debug=True)
          xbmcgui.Dialog().notification('youtube-dl path not writeable',os.path.join(addonFolder, "icon.png"),5000,True)
          return False

#        yes = xbmcgui.Dialog().yesno('Continue downloading?', 'Download YouTube ID '+ytid+' ?', '')
        yes = True
        if yes:
            LOG("Downloading video with youtube-dl "+url, debug=True)

            global pDialog
            if xbmc.Player().isPlaying():
                xbmcgui.Dialog().notification('youtube-dl download started',title,os.path.join(addonFolder, "icon.png"),5000,True)
                pDialog = xbmcgui.DialogProgressBG()
            else:
                pDialog = xbmcgui.DialogProgressBG()

            pDialog.create('YoutubeDL '+title.decode('latin1'), 'Preparing to download '+title.decode('latin1')+' ...')

            from youtube_dl.postprocessor import FFmpegPostProcessor
            ffm_ver = FFmpegPostProcessor()._versions
            LOG("FFmpeg/AVCONV versions: "+repr(ffm_ver), debug=True)

            ydl_opts = {
                'outtmpl': os.path.join(xbmc.translatePath('special://temp'))+'%(title)s [%(height)sp].%(ext)s',
                'nopart': True,
#                'forcefilename': True,
                'logger': MyLogger(),
                'progress_hooks': [my_hook],
                }

            #if neither ffmpeg nor avconv is available, use best combined format
            if ffm_ver.get("avconv")==False and ffm_ver.get("ffmpeg")==False:
                ydl_opts.update( { "format": "best" } )

            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                try:
                    ydl_info = ydl.extract_info(url,download=False)
# ExtractorError not available or raised, removing for now
#                except ExtractorError as ee:
#                    #Extractor Error: could not find JS function, youtube dl may need to be updated or bug raised
#                    xbmc.log('context.youtube.dl.menu: '+'ExtractorError '+ee, xbmc.LOGERROR)
#                    pDialog.close()
#                    xbmcgui.Dialog().notification('youtube-dl error','YTD JS Error, check logs',os.path.join(addonFolder, "icon.png"),5000,True)
#                    return False
                except:
                    #other YTD error, abort
                    xbmc.log('context.youtube.dl.menu: '+'Fatal error '+sys.exc_info()[0], xbmc.LOGERROR)
                    pDialog.close()
                    xbmcgui.Dialog().notification('youtube-dl error','Fatal YTD Error, check logs',os.path.join(addonFolder, "icon.png"),5000,True)
                    return False

                #ydl_formats = ydl.list_formats(ydl_info)
                #LOG("YTD Formats: "+repr(ydl_formats), debug=True)

                filename = ydl.prepare_filename(ydl_info)

                #Check if file already downloaded
                if xbmcvfs.exists(os.path.join(targetdir,os.path.basename(filename))):
                    LOG("File already exists "+os.path.basename(filename), debug=True)
                    continuedownload = xbmcgui.Dialog().yesno('Continue downloading?', os.path.basename(filename)+' already exists!\nDownload again and overwrite ?', '')
                    if not continuedownload:
                        LOG("File already exist, not overwriting", debug=True)
                        pDialog.close()
                        xbmcgui.Dialog().notification('youtube-dl','Download cancelled',os.path.join(addonFolder, "icon.png"),5000,True)
                        return False

                #Continue downloading file
                pDialog.update(0, 'Downloading '+title.decode('latin1')+' ...')
                ydl.process_ie_result(ydl_info, download=True)
                pDialog.update(95, 'youtube-dl finished downloading '+title.decode('latin1'))
                pDialog.update(98, 'youtube-dl moving file '+title.decode('latin1'))
                handleFinished(filename,title)

def handleFinished(filename,title):
    global pDialog
    targetdir = getDownloadPath()
    LOG("final format "+finalformat, debug=True)
    if not finalformat == "":
        base = os.path.splitext(filename)[0]
        filename = base + "." + finalformat

    if moveFile(filename,targetdir):
        LOG("File "+filename+" moved to "+targetdir, debug=True)
        pDialog.update(100, 'youtube-dl file moved '+title.decode('latin1'))
        xbmc.sleep(1000)
        pDialog.close()
        xbmcgui.Dialog().notification('youtube-dl finished',title,os.path.join(addonFolder, "icon.png"),5000,True)
    else:
        LOG("File "+os.path.basename(filename)+" could not be moved to "+targetdir, debug=True)
        pDialog.update(100, 'youtube-dl file not moved '+title.decode('latin1'))
        xbmc.sleep(1000)
        pDialog.close()
        delete = xbmcgui.Dialog().yesno('Move error','Failed to move\n'+os.path.basename(filename)+'\nto '+targetdir+'\n\nDelete temp file?','')
        if delete:
            xbmcvfs.delete(filename)
            xbmcgui.Dialog().notification('youtube-dl deleted',title,os.path.join(addonFolder, "icon.png"),5000,True)

def moveFile(file_path, dest_path, filename=None):
    fname = filename or os.path.basename(file_path)
    destFilePath = os.path.join(dest_path, fname)
    LOG("Moving file "+fname+" from "+file_path+" to "+destFilePath, debug=True)
    if xbmcvfs.exists(file_path):
        if xbmcvfs.copy(file_path, destFilePath):
            xbmcvfs.delete(file_path)
            return True
        return False
    else:
        LOG("Could not find source file "+file_path, debug=True)
        return False


main()

import os
import pipes
import shlex
import subprocess
import threading
import xbmc
import xbmcaddon


class ListeningPlayer(xbmc.Player):

    def __init__(self):
        super(ListeningPlayer, self).__init__()
        self.isVideo = None
        self.isVideoGuard = threading.Lock()
        self.addon = xbmcaddon.Addon()

    def onPlayBackStarted(self):
        isVideo = self.isPlayingVideo()
        startScriptPath = self.addon.getSetting('startScriptPath')
        with self.isVideoGuard:
            self.isVideo = isVideo
        if (isVideo and
                self.addon.getSetting('startScriptEnabled') and
                os.path.isfile(startScriptPath)):
            startScriptCmd = ([startScriptPath] + shlex.split(
                self.addon.getSetting('startScriptArgs')))
            xbmc.log(
                'Video starting triggered script: ' +
                ' '.join(pipes.quote(arg) for arg in startScriptCmd),
                xbmc.LOGINFO)
            try:
                subprocess.check_call(startScriptCmd)
            except subprocess.CalledProcessError as e:
                xbmc.log('Video start script failed: ' + str(e))

    def onPlayBackStopped(self):
        with self.isVideoGuard:
            wasVideo = self.isVideo
            self.isVideo = None
        stopScriptPath = self.addon.getSetting('stopScriptPath')
        if (wasVideo and
                self.addon.getSetting('stopScriptEnabled') and
                os.path.isfile(stopScriptPath)):
            stopScriptCmd = ([stopScriptPath] + shlex.split(
                self.addon.getSetting('stopScriptArgs')))
            xbmc.log(
                'Video stopping triggered script: ' +
                ' '.join(pipes.quote(arg) for arg in stopScriptCmd),
                xbmc.LOGINFO)
            try:
                subprocess.check_call(stopScriptCmd)
            except subprocess.CalledProcessError as e:
                xbmc.log('Video stop script failed: ' + str(e))


def main():
    playback = ListeningPlayer()
    xbmc.Monitor().waitForAbort()


if __name__ == "__main__":
    main()

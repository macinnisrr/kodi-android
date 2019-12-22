# -*- coding: utf-8 -*-
#########################################################
# SCRIPT  : script.py                                   #
#           Script handling commands for WebGrab++      #
#           I. Helwegen 2015                            #
#########################################################

####################### IMPORTS #########################
import sys, os
import xbmc, xbmcaddon, xbmcgui
#########################################################

####################### GLOBALS #########################
__addon__ = xbmcaddon.Addon()
__addonname__ = __addon__.getAddonInfo('id')
__addonpath__ = __addon__.getAddonInfo('path')
__LS__ = __addon__.getLocalizedString
__lib__ = xbmc.translatePath( os.path.join( __addonpath__, 'resources', 'lib' ).encode("utf-8") ).decode("utf-8")

NoPicture = xbmc.translatePath(os.path.join(__addonpath__, 'resources', 'media', 'DefaultVideoCover.png'))
SearchPicture = xbmc.translatePath(os.path.join(__addonpath__, 'resources', 'media', 'DefaultVideoSearch.png'))

sys.path.append(__lib__)
import common
from frames import frames
from edl import edl

### EXIT STATUS ###
EXIT_CANCEL = 0
EXIT_STORE  = 1
EXIT_EDIT   = 2
EXIT_ADD    = 3
EXIT_DELETE = 4
EXIT_OK     = 5

#########################################################
# Class : EDLEditor                                     #
#########################################################
class EDLEditor(object):
    def __init__(self):
        self.video_folder = __addon__.getSetting('video_folder')
        self.frame_edl = True if __addon__.getSetting('frame_edl').upper() == 'TRUE' else False
        self.framelist = []
        self.status = {}

    def __del__(self):
        del self.framelist
        del self.status

    def run(self):
        common.writeLog("EDL editor started")
        #First select a video file

        videofile = common.GUI_BrowseVideos(__LS__(60001), self.video_folder)

        if videofile == "":
            common.notifyOSD(__LS__(60000),__LS__(60009))
        else:
            # check existence and status of EDL
            status, editfile = common.GetStatus(videofile)

            # select the desired action
            action=common.GUI_SelectAction(status)

            if action != -1:
                if status == common.STS_NOEDL:
                    self.EditFile(videofile=videofile, editfile=editfile, create=True)
                elif status == common.STS_DIS:
                    neweditfile=os.path.basename(common.EnableEDL(editfile))
                    common.notifyOSD(__LS__(60000),__LS__(60021)%neweditfile)
                elif status == common.STS_ENA:
                    if action == 0:
                        self.EditFile(videofile=videofile, editfile=editfile, create=False)
                    elif action == 1:
                        neweditfile=os.path.basename(common.DisableEDL(editfile))
                        common.notifyOSD(__LS__(60000),__LS__(60020)%neweditfile)
            else:
                common.notifyOSD(__LS__(60000),__LS__(60009))

        common.writeLog("EDL editor finished")

    def EditFile(self, videofile, editfile, create):
        ExitMainUi = False
        # load or create EDL
        Progress=common.GUI_Progress(__LS__(60000), __LS__(60022))
        EDL = edl(editfile, create, self.frame_edl)
        Frames = frames(videofile)
        if Progress.iscanceled():
            return
        Progress.close()
        if not Frames.av_installed():
            common.writeLog(__LS__(60024))
            common.notifyOSD(__LS__(60000), __LS__(60024))
        
        canceled=self.FillFrameList(Frames, EDL)
        self.FillStatus(Frames, EDL, videofile, editfile)
        if not canceled or not self.status:
            common.writeLog(__LS__(60009)) 
            ExitMainUi = True

        while not ExitMainUi:
            __gui_type = "Classic" if __addon__.getSetting('gui_type').upper() == 'CLASSIC' else "Default"
            MainUi = GUIMain("%s.xml" % __addonname__.replace(".","-") , __addonpath__, __gui_type, status=self.status, framelist=self.framelist)

            if MainUi:
                MainUi.doModal()
                ExitStatus = MainUi.GetExitStatus()
                ListIndex = MainUi.GetListIndex()
                if ExitStatus == EXIT_STORE:
                    common.writeLog("Store editlist ....")
                    ExitMainUi = True
                elif ExitStatus == EXIT_EDIT:
                    common.writeLog("Edit item ....")
                    self.EditItem(Frames, EDL, ListIndex)
                elif ExitStatus == EXIT_ADD:
                    common.writeLog("Add item ....")
                    self.AddItem(Frames, EDL, ListIndex)
                elif ExitStatus == EXIT_DELETE:
                    common.writeLog("Delete item ....")
                    self.DeleteItem(EDL, ListIndex)
                else:
                    common.writeLog("Cancel ....")
                    ExitMainUi = True
                    EDL.cancel()
                del MainUi
        return

    def FillFrameList(self, Frames, EDL):
        EDLlist = EDL.getlist()
        framebased = EDL.is_framebased()

        Progress=common.GUI_Progress(__LS__(60000), __LS__(60023))
        items = len(EDLlist)
        for index, item in enumerate(EDLlist):
            Progress.update(100*index//items)
            FrameInfo=self.AddFrameInfo(Frames, item, framebased)
            if Progress.iscanceled():
                del self.framelist
                self.framelist = []
                return False
            self.framelist.append(FrameInfo)
        Progress.update(100)
        Progress.close()
        return True

    def AddFrameInfo(self, Frames, item, framebased = False):
        FrameInfo = {}
        FrameInfo['IndexStart']=item[0]
        FrameInfo['IndexStop']=item[1]
        if Frames.av_installed():
            if framebased:
                FrameInfo['PictureStart']=Frames.get_frame(int(item[0]))
                FrameInfo['PictureStop']=Frames.get_frame(int(item[1]))
            else:
                FrameInfo['PictureStart']=Frames.get_frame_time(float(item[0]))
                FrameInfo['PictureStop']=Frames.get_frame_time(float(item[1]))
        else:
            FrameInfo['PictureStart']=NoPicture
            FrameInfo['PictureStop']=NoPicture
        return FrameInfo

    def AddSingleFrameInfo(self, Frames, item):
        try:
            Progress=common.GUI_Progress(__LS__(60000), __LS__(60023))
            FrameInfo=self.AddFrameInfo(Frames, item, self.status[__LS__(60113)])
            if Progress.iscanceled():
                return False
            Progress.close()
        except:
            return False
        return FrameInfo

    def AddEmptyFrameInfo(self, Frames):
        return self.AddSingleFrameInfo(Frames, (0,0))

    def AddFrameListItem(self, RetItem):
        pos=self.GetPos(RetItem)
        if pos >= 0:
            self.framelist.insert(pos, RetItem)

    def EditFrameListItem(self, index, RetItem):
        self.RemoveFrameListItem(index)
        self.AddFrameListItem(RetItem)

    def RemoveFrameListItem(self, index):
        self.framelist.pop(index)

    def GetPos(self, Item):
        pos = -1
        if len(self.framelist) == 0:
            pos = 0
        else:
            start=Item['IndexStart']
            for i, frameitem in enumerate(self.framelist):
                if frameitem['IndexStart'] > start:
                    pos = i
                    break
            if pos < 0:
                pos = len(self.framelist)
        return pos


    def FillStatus(self, Frames, EDL, videofile, editfile):
        self.status[__LS__(60110)] = os.path.basename(videofile)
        self.status[__LS__(60111)] = os.path.basename(editfile)
        self.status[__LS__(60112)] = EDL.is_edl()
        self.status[__LS__(60113)] = EDL.is_framebased()
        self.status[__LS__(60114)] = len(EDL.getlist())
        timeinfo = Frames.get_time_info()
        self.status[__LS__(60115)] = timeinfo[0]
        self.status[__LS__(60116)] = timeinfo[1]
        self.status[__LS__(60117)] = timeinfo[2]
        self.status[__LS__(60118)] = Frames.get_frame_rate()
        return True

    def StatusEditNumberEdits(self, EDL):
        self.status[__LS__(60114)] = len(EDL.getlist())
        return True

    def EditItem(self, Frames, EDL, ListIndex):
        if ListIndex >= 0:
            CurrItem = self.framelist[ListIndex].copy()
            Canceled, RetItem = self.EditGUI(Frames, CurrItem)
            if not Canceled:
                EDL.editline(self.framelist[ListIndex]['IndexStart'], RetItem['IndexStart'], RetItem['IndexStop'])
                self.EditFrameListItem(ListIndex, RetItem)
        return

    def AddItem(self, Frames, EDL, ListIndex):
        if ListIndex < 0:
            ListIndex = 0
            CurrItem = self.AddEmptyFrameInfo(Frames)
        else:
            cut = self.GetCut(Frames, ListIndex)
            CurrItem = self.AddSingleFrameInfo(Frames, (cut, cut))
        Canceled, RetItem = self.EditGUI(Frames, CurrItem)
        if not Canceled:
                EDL.addline(RetItem['IndexStart'], RetItem['IndexStop'])
                self.AddFrameListItem(RetItem)
        return

    def DeleteItem(self, EDL, ListIndex):
        if ListIndex >= 0:
            EDL.removeline(self.framelist[ListIndex]['IndexStart'])
            self.RemoveFrameListItem(ListIndex)
            self.StatusEditNumberEdits(EDL)
        return

    def EditGUI(self, Frames, CurrItem):
        RetItem = CurrItem
        Canceled = True
        __gui_type = "Classic" if __addon__.getSetting('gui_type').upper() == 'CLASSIC' else "Default"
        EditUi = GUIEdit("%s-edit.xml" % __addonname__.replace(".","-") , __addonpath__, __gui_type, item=CurrItem, Frames=Frames, status=self.status)
        
        if EditUi:
            EditUi.doModal()
            ExitStatus = EditUi.GetExitStatus()
            RetItem = EditUi.GetItem()
            if ExitStatus == EXIT_OK:
                common.writeLog("Store edit ....")
                Canceled = False
            del EditUi

        return Canceled, RetItem

    def GetCut(self, Frames, ListIndex):
        rawcut = 0
        try:
            framerate = Frames.get_frame_rate()
            if self.status[__LS__(60113)] == False: # Time based    
                if len(self.framelist) > ListIndex:
                    rawcut=self.framelist[ListIndex]['IndexStop'] + (self.framelist[ListIndex+1]['IndexStart'] - self.framelist[ListIndex]['IndexStop'])//2
                elif self.status[__LS__(60116)] >= 0:
                    rawcut=self.framelist[ListIndex]['IndexStop'] + (self.status[__LS__(60116)] - self.framelist[ListIndex]['IndexStop'])//2
                else:
                    rawcut = self.framelist[ListIndex]['IndexStop']
    
                interval=self.status[__LS__(60117)]
                if interval <= 0:
                    interval = 12//framerate
                cut = round((rawcut/interval),0)*interval
            else: # Frame based
                if len(self.framelist) > ListIndex:
                    rawcut=self.framelist[ListIndex]['IndexStop'] + (self.framelist[ListIndex+1]['IndexStart'] - self.framelist[ListIndex]['IndexStop'])//2
                elif self.status[__LS__(60116)] >= 0:
                    rawcut=self.framelist[ListIndex]['IndexStop'] + (self.status[__LS__(60116)*framerate] - self.framelist[ListIndex]['IndexStop'])//2
                else:
                    rawcut = self.framelist[ListIndex]['IndexStop']
    
                interval=self.status[__LS__(60117)]*framerate
                if interval <= 0:
                    interval = 12
                cut = int(round((rawcut/interval),0)*interval)
        except:
            cut = 0
        return cut

### CONTROLS ###
BUTTON_STORE    = 10
BUTTON_CANCEL   = 11
BUTTON_EXIT     = 20
LABEL_TITLE     = 15
LIST_EDL        = 40
BUTTON_EDIT     = 70
BUTTON_ADD      = 71
BUTTON_DELETE   = 72

LABEL_VIDEOFILE = 100
LABEL_EDITFILE  = 101
LABEL_EDITTYPE  = 102
LABEL_EDITUNIT  = 103
LABEL_EDITNR    = 104
LABEL_STARTTIME = 105
LABEL_DURATION  = 106
LABEL_INTERVAL  = 107
LABEL_FRAMERATE = 108

FIELD_VIDEOFILE = 110
FIELD_EDITFILE  = 111
FIELD_EDITTYPE  = 112
FIELD_EDITUNIT  = 113
FIELD_EDITNR    = 114
FIELD_STARTTIME = 115
FIELD_DURATION  = 116
FIELD_INTERVAL  = 117
FIELD_FRAMERATE = 118

CANCEL_DIALOG = (9, 10, 216, 247, 257, 275, 61448, 61467)

######################

#########################################################
# Class : GUIMain                                       #
#########################################################
class GUIMain(xbmcgui.WindowXMLDialog):	
    def __init__(self, *args, **kwargs):
        self.status = kwargs.pop('status')
        self.framelist = kwargs.pop('framelist')
        self.ExitStatus = EXIT_CANCEL
        self.CurrentListIndex = -1

    def onInit(self):
        self.getControl(LABEL_TITLE).setLabel(__LS__(60000))

        self.PopulateEDLList()

        self.getControl(LABEL_VIDEOFILE).setLabel(__LS__(60110))
        self.getControl(FIELD_VIDEOFILE).setLabel(self.status[__LS__(60110)])
        self.getControl(LABEL_EDITFILE).setLabel(__LS__(60111))
        self.getControl(FIELD_EDITFILE).setLabel(self.status[__LS__(60111)])
        if self.status[__LS__(60112)]:
            tempstr = "EDL"
        else:
            tempstr = "TXT"
        self.getControl(LABEL_EDITTYPE).setLabel(__LS__(60112))
        self.getControl(FIELD_EDITTYPE).setLabel(tempstr)
        if self.status[__LS__(60113)]:
            tempstr = "Frames"
        else:
            tempstr = "Time"
        self.getControl(LABEL_EDITUNIT).setLabel(__LS__(60113))
        self.getControl(FIELD_EDITUNIT).setLabel(tempstr)
        self.getControl(LABEL_EDITNR).setLabel(__LS__(60114))
        self.getControl(FIELD_EDITNR).setLabel(str(self.status[__LS__(60114)]))
        self.getControl(LABEL_STARTTIME).setLabel(__LS__(60115))
        if self.status[__LS__(60115)] >= 0:
            self.getControl(FIELD_STARTTIME).setLabel(common.PrettyIndex(self.status[__LS__(60115)], False))
        else:
            self.getControl(FIELD_STARTTIME).setLabel(__LS__(60102))
        self.getControl(LABEL_DURATION).setLabel(__LS__(60116))
        if self.status[__LS__(60116)] >= 0:
            self.getControl(FIELD_DURATION).setLabel(common.PrettyIndexFrm(self.status[__LS__(60116)], self.status[__LS__(60118)]))
        else:
            self.getControl(FIELD_DURATION).setLabel(__LS__(60102))
        self.getControl(LABEL_INTERVAL).setLabel(__LS__(60117))
        if self.status[__LS__(60117)] > 0:
            self.getControl(FIELD_INTERVAL).setLabel(common.PrettyIndexFrm(self.status[__LS__(60117)], self.status[__LS__(60118)]))
        else:
            self.getControl(FIELD_INTERVAL).setLabel(__LS__(60102))
        self.getControl(LABEL_FRAMERATE).setLabel(__LS__(60118))
        if self.status[__LS__(60118)] > 0:
            self.getControl(FIELD_FRAMERATE).setLabel(str(self.status[__LS__(60118)]))
        else:
            self.getControl(FIELD_FRAMERATE).setLabel(__LS__(60102))


        self.getControl(BUTTON_EDIT).setLabel(__LS__(60103))
        self.getControl(BUTTON_ADD).setLabel(__LS__(60104))
        self.getControl(BUTTON_DELETE).setLabel(__LS__(60105))
        if self.getControl(LIST_EDL).size() <= 0:
            self.getControl(BUTTON_EDIT).setEnabled(False)
            self.getControl(BUTTON_DELETE).setEnabled(False)
        else:
            self.getControl(BUTTON_EDIT).setEnabled(True)
            self.getControl(BUTTON_DELETE).setEnabled(True)
        self.getControl(BUTTON_STORE).setLabel(__LS__(60100))
        self.getControl(BUTTON_CANCEL).setLabel(__LS__(60101))

    def GetExitStatus(self):
        return self.ExitStatus

    def GetListIndex(self):
        return self.CurrentListIndex

    def onClick(self, controlId):
        if (controlId == BUTTON_STORE):
            self.ExitStatus = EXIT_STORE
            self.ExitEditor()
        if (controlId == BUTTON_EDIT):
            self.ExitStatus = EXIT_EDIT
            self.ExitEditor()
        if (controlId == BUTTON_ADD):
            self.ExitStatus = EXIT_ADD
            self.ExitEditor()
        if (controlId == BUTTON_DELETE):
            self.ExitStatus = EXIT_DELETE
            self.ExitEditor()
        if (controlId == BUTTON_CANCEL) or (controlId == BUTTON_EXIT):
            self.ExitStatus = EXIT_CANCEL
            self.ExitEditor()

    def onAction(self, action):
        if (action.getButtonCode() in CANCEL_DIALOG):
            self.ExitStatus = EXIT_CANCEL
            self.ExitEditor()

    def ExitEditor(self):
        common.writeLog("Exit EDL Editor")
        self.CurrentListIndex = self.getControl(LIST_EDL).getSelectedPosition()
        self.close()

    def PopulateEDLList(self):
        listitems = []
        for item in self.framelist:
            listitem=xbmcgui.ListItem(common.PrettyIndex(item['IndexStart'],self.status[__LS__(60113)]), common.PrettyIndex(item['IndexStop'],self.status[__LS__(60113)]))
            listitem.setArt({ 'start': item['PictureStart'], 'stop' : item['PictureStop'] })
            listitems.append(listitem)
        self.getControl(LIST_EDL).addItems(listitems)

#########################################################

### CONTROLS ###
BUTTON_OK2      = 210
BUTTON_CANCEL2  = 211
BUTTON_EXIT2    = 220
LABEL_TITLE2    = 215

IMAGE_START     = 230
TIME_START      = 231
LABEL_START     = 232
IMAGE_STOP      = 235
TIME_STOP       = 236
LABEL_STOP      = 237

BUTTON_M5_START = 240
BUTTON_M1_START = 241
BUTTON_MG_START = 242
BUTTON_PG_START = 243
BUTTON_P1_START = 244
BUTTON_P5_START = 245

BUTTON_M5_STOP  = 250
BUTTON_M1_STOP  = 251
BUTTON_MG_STOP  = 252
BUTTON_PG_STOP  = 253
BUTTON_P1_STOP  = 254
BUTTON_P5_STOP  = 255

BUTTON_ED_START = 249
BUTTON_ED_STOP  = 259

JUMP_TIME       = 1.0

#CANCEL_DIALOG = (9, 10, 216, 247, 257, 275, 61448, 61467)

######################

#########################################################
# Class : GUIEdit                                       #
#########################################################
class GUIEdit(xbmcgui.WindowXMLDialog): 
    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        self.Frames = kwargs.pop('Frames')
        self.status = kwargs.pop('status')
        self.timer = None
        self.ExitStatus = EXIT_CANCEL
        self.FirstStart = True
        self.FirstStop = True
        self.search_delay = True if __addon__.getSetting('search_delay').upper() == 'TRUE' else False

    def onInit(self):
        self.getControl(LABEL_TITLE2).setLabel(__LS__(60000))
        self.getControl(LABEL_START).setLabel(__LS__(60119))
        self.getControl(LABEL_STOP).setLabel(__LS__(60120))

        self.getControl(BUTTON_OK2).setLabel(__LS__(60106))
        self.getControl(BUTTON_CANCEL2).setLabel(__LS__(60101))

        self.getControl(BUTTON_ED_START).setLabel(__LS__(60121))
        self.getControl(BUTTON_ED_STOP).setLabel(__LS__(60122))

        self.getControl(IMAGE_START).setImage(self.item['PictureStart'], False)
        self.getControl(IMAGE_STOP).setImage(self.item['PictureStop'], False)
        self.getControl(TIME_START).setLabel(common.PrettyIndex(self.item['IndexStart'],self.status[__LS__(60113)]))
        self.getControl(TIME_STOP).setLabel(common.PrettyIndex(self.item['IndexStop'],self.status[__LS__(60113)]))

        self.EnableButtons()

    def GetExitStatus(self):
        return self.ExitStatus

    def GetItem(self):
        return self.item

    def onClick(self, controlId):
        if controlId == BUTTON_OK2:
            self.ExitStatus = EXIT_OK
            self.ExitEditor()
        elif controlId == BUTTON_P5_START:
            self.Jump(+5, False, True)
        elif controlId == BUTTON_P1_START:
            self.Jump(+1, False, True)
        elif controlId == BUTTON_PG_START:
            self.Jump(+1, True, True)
        elif controlId == BUTTON_MG_START:
            self.Jump(-1, True, True)
        elif controlId == BUTTON_M1_START:
            self.Jump(-1, False, True)
        elif controlId == BUTTON_M5_START:
            self.Jump(-5, False, True)
        elif controlId == BUTTON_ED_START:
            self.EnterTime(True)
        elif controlId == BUTTON_P5_STOP:
            self.Jump(+5, False, False)
        elif controlId == BUTTON_P1_STOP:
            self.Jump(+1, False, False)
        elif controlId == BUTTON_PG_STOP:
            self.Jump(+1, True, False)
        elif controlId == BUTTON_MG_STOP:
            self.Jump(-1, True, False)
        elif controlId == BUTTON_M1_STOP:
            self.Jump(-1, False, False)
        elif controlId == BUTTON_M5_STOP:
            self.Jump(-5, False, False)
        elif controlId == BUTTON_ED_STOP:
            self.EnterTime(False)
        if (controlId == BUTTON_CANCEL2) or (controlId == BUTTON_EXIT2):
            self.ExitStatus = EXIT_CANCEL
            self.ExitEditor()

    def onAction(self, action):
        if (action.getButtonCode() in CANCEL_DIALOG):
            if self.timer != None:
                return
            self.ExitStatus = EXIT_CANCEL
            self.ExitEditor()
        elif action == ACTION_CHANNEL_DOWN:
            self.Jump(-5, False, self.getStartFocus())
        elif action == ACTION_PREV_ITEM:
            self.Jump(-1, False, self.getStartFocus())
        elif action == ACTION_REWIND:
            self.Jump(-1, True, self.getStartFocus())
        elif action == ACTION_FORWARD:
            self.Jump(+1, True, self.getStartFocus())
        elif action == ACTION_NEXT_ITEM:
            self.Jump(+1, False, self.getStartFocus())
        elif action == ACTION_CHANNEL_UP:
            self.Jump(+5, False, self.getStartFocus())

    def getStartFocus(self):
        Left = False
        FocusId = self.getFocusId()
        if (FocusId>=240) and (FocusId<=249):
            Left = True
        return Left

    def ExitEditor(self):
        if self.timer != None:
            self.timer.stop()
            del self.timer
            self.timer = None
        common.writeLog("Exit EDL Editor")
        self.close()

        # +5, +1, -1, -5
    def Jump(self, interval, Gop = True, Start = True):
        if self.timer != None:
            self.timer.stop()
            del self.timer
            self.timer = None
        if Start:
            self.getControl(IMAGE_START).setImage(SearchPicture, False)
        else:
            self.getControl(IMAGE_STOP).setImage(SearchPicture, False)
        self.DoJump(interval, Gop, Start)
        if Start:
            self.getControl(TIME_START).setLabel(common.PrettyIndex(self.item['IndexStart'],self.status[__LS__(60113)]))
        else:
            self.getControl(TIME_STOP).setLabel(common.PrettyIndex(self.item['IndexStop'],self.status[__LS__(60113)]))
        
        if self.search_delay:  
            self.timer = common.aTimer(JUMP_TIME, False, self.Seek, Start)
        else:
            self.Seek(Start)  

    def Seek(self, Start = True):
        if self.timer != None:
            self.timer.stop()
            del self.timer
            self.timer = None
        # Do seek
        framebased = self.status[__LS__(60113)]
        if Start:
            if self.Frames.av_installed():
                if not self.FirstStart:
                    self.Frames.DeleteImage(self.item['PictureStart'])
                self.FirstStart=False
                if framebased:
                    self.item['PictureStart']=self.Frames.get_frame(self.item['IndexStart'])
                else:
                    self.item['PictureStart']=self.Frames.get_frame_time(self.item['IndexStart'])
            else:
                self.item['PictureStart']=NoPicture
            self.getControl(IMAGE_START).setImage(self.item['PictureStart'], False)
        else:
            if self.Frames.av_installed():
                if not self.FirstStop:
                    self.Frames.DeleteImage(self.item['PictureStop'])
                self.FirstStop=False
                if framebased:
                    self.item['PictureStop']=self.Frames.get_frame(self.item['IndexStop'])
                else:
                    self.item['PictureStop']=self.Frames.get_frame_time(self.item['IndexStop'])
            else:
                self.item['PictureStart']=NoPicture
            self.getControl(IMAGE_STOP).setImage(self.item['PictureStop'], False)
        common.writeLog("Seeking .....")

    def EnterTime(self, Start = True):
        if self.timer != None:
            self.timer.stop()
            del self.timer
        # Do enter and jump
        if Start:
            self.getControl(IMAGE_START).setImage(SearchPicture, False)
        else:
            self.getControl(IMAGE_STOP).setImage(SearchPicture, False)
        framebased = self.status[__LS__(60113)]
        starttime = self.item['IndexStart']
        stoptime = self.item['IndexStop']
        framerate = self.Frames.get_frame_rate()

        if framebased:
            gopinterval = self.status[__LS__(60117)]*framerate
            if gopinterval <= 0:
                gopinterval = 12
        else:
            gopinterval = self.status[__LS__(60117)]
            if gopinterval <= 0:
                gopinterval = 12//framerate
        if Start:
            enteredtime = common.GUI_Input(__LS__(60025),common.PrettyIndex(self.item['IndexStart'],self.status[__LS__(60113)]))
            starttime = common.Pretty2Index(enteredtime,self.status[__LS__(60113)])
            newtime = round((starttime/gopinterval),0)*gopinterval
            if framebased or self.status[__LS__(60115)] < 0:
                if newtime < 0:
                    newtime = 0
            else:
                if newtime < self.status[__LS__(60115)]:
                    newtime = self.status[__LS__(60115)]
            if newtime > stoptime:
                newtime = stoptime
            self.item['IndexStart'] = newtime
        else:
            enteredtime = common.GUI_Input(__LS__(60026),common.PrettyIndex(self.item['IndexStop'],self.status[__LS__(60113)]))
            stoptime = common.Pretty2Index(enteredtime,self.status[__LS__(60113)])
            newtime = round((stoptime/gopinterval),0)*gopinterval
            if newtime < starttime:
                newtime = starttime
            if self.status[__LS__(60116)] >= 0:
                if newtime > self.status[__LS__(60116)] * framerate:
                    newtime = self.status[__LS__(60116)] * framerate
            self.item['IndexStop'] = newtime
        if Start:
            self.getControl(TIME_START).setLabel(common.PrettyIndex(self.item['IndexStart'],self.status[__LS__(60113)]))
        else:
            self.getControl(TIME_STOP).setLabel(common.PrettyIndex(self.item['IndexStop'],self.status[__LS__(60113)]))

        if self.search_delay:  
            self.timer = common.aTimer(JUMP_TIME, False, self.Seek, Start)
        else:
            self.Seek(Start)  

    def DoJump(self, interval, Gop = True, Start = True):
        framebased = self.status[__LS__(60113)]
        starttime = self.item['IndexStart']
        stoptime = self.item['IndexStop']
        framerate = self.Frames.get_frame_rate()

        if framebased:
            gopinterval = self.status[__LS__(60117)]*framerate
            if gopinterval <= 0:
                gopinterval = 12
            if Gop:
                if interval > 0:
                    jump = 0 + gopinterval
                else:
                    jump = 0 - gopinterval
            else:
                jump = (interval * 60 * framerate)
            if Start:
                starttime += jump
                newtime = int(round((starttime/gopinterval),0)*gopinterval)
                if newtime < 0:
                    newtime = 0
                if newtime > stoptime:
                    newtime = stoptime
            else:
                stoptime += jump 
                newtime = int(round((stoptime/gopinterval),0)*gopinterval)
                if newtime < starttime:
                    newtime = starttime
                if self.status[__LS__(60116)] >= 0:
                    if framebased:
                        if newtime > self.status[__LS__(60116)] * framerate:
                            newtime = self.status[__LS__(60116)] * framerate
                    else:
                        if newtime > self.status[__LS__(60116)]:
                            newtime = self.status[__LS__(60116)]
        else:
            gopinterval = self.status[__LS__(60117)]
            if gopinterval <= 0:
                gopinterval = 12//framerate
            if Gop:
                if interval > 0:
                    jump = 0 + gopinterval
                else:
                    jump = 0 - gopinterval
            else:
                jump = (interval * 60)
            if Start:
                starttime += jump
                newtime = round((starttime/gopinterval),0)*gopinterval
                if self.status[__LS__(60115)] >= 0:
                    if newtime < self.status[__LS__(60115)]:
                        newtime = self.status[__LS__(60115)]    
                elif newtime < 0:
                    newtime = 0
                if newtime > stoptime:
                    newtime = stoptime
            else:
                stoptime += jump 
                newtime = round((stoptime/gopinterval),0)*gopinterval
                if newtime < starttime:
                    newtime = starttime
                if self.status[__LS__(60116)] >=0:
                    if newtime > self.status[__LS__(60116)]:
                        newtime = self.status[__LS__(60116)]

        if Start:
            self.item['IndexStart'] = newtime
        else:
            self.item['IndexStop'] = newtime

    def EnableButtons(self):
        self.getControl(BUTTON_OK2).setEnabled(True)
        self.getControl(BUTTON_CANCEL2).setEnabled(True)
        self.getControl(BUTTON_EXIT2).setEnabled(True)
        self.getControl(BUTTON_P5_START).setEnabled(True)
        self.getControl(BUTTON_P1_START).setEnabled(True)
        self.getControl(BUTTON_PG_START).setEnabled(True)
        self.getControl(BUTTON_MG_START).setEnabled(True)
        self.getControl(BUTTON_M1_START).setEnabled(True)
        self.getControl(BUTTON_M5_START).setEnabled(True)
        self.getControl(BUTTON_ED_START).setEnabled(True)
        self.getControl(BUTTON_P5_STOP).setEnabled(True)
        self.getControl(BUTTON_P1_STOP).setEnabled(True)
        self.getControl(BUTTON_PG_STOP).setEnabled(True)
        self.getControl(BUTTON_MG_STOP).setEnabled(True)
        self.getControl(BUTTON_M1_STOP).setEnabled(True)
        self.getControl(BUTTON_M5_STOP).setEnabled(True)
        self.getControl(BUTTON_ED_STOP).setEnabled(True)

#########################################################
######################## MAIN ###########################
#########################################################
Editor = EDLEditor()
Editor.run()
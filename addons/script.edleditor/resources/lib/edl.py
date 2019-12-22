# -*- coding: utf-8 -*-
#########################################################
# SERVICE : edl.py                                      #
#           Parse and edit edl and txt video edit files #
#           I. Helwegen 2017                            #
#########################################################

####################### IMPORTS #########################
from os import path
#########################################################

####################### GLOBALS #########################

#########################################################
# Class : edl                                           #
#########################################################
class edl(object):
    def __init__(self, file, create = False, frames = False, debug = False):
        self.debug = debug
        self.edllist = []
        self.file = file
        self.edlfile = True
        self.frames = frames
        self.textlines = ""
        self.filechanged = False
        if create:
            self._create_file()
        else:
            self._readparse_file()
        
    def __del__(self):
        if self.filechanged:
            self._save_file()
        self.debug = False
        del self.edllist
        self.edllist = []
        self.file = ""
        self.edlfile = True
        self.frames = False
        self.textlines = ""
        self.filechanged = False
        
    def getlist(self):
        return self.edllist

    def editline(self, old_start, start, stop, etype=0):
        self.removeline(old_start)
        self.addline(start, stop, etype)
        """
        pos = self._getpos(old_start)
        if pos >= 0:
            self.filechanged = True
            newtup = (start,stop,etype)
            self.edllist[pos] = newtup            
        """

    def addline(self, start, stop, etype=0):
        pos = self._getpos(start, True)
        if pos >= 0:
            self.filechanged = True
            newtup = (start,stop,etype)
            self.edllist.insert(pos, newtup)     

    def removeline(self, start):
        pos = self._getpos(start)
        if pos >= 0:
            self.filechanged = True
            self.edllist.pop(pos)            

    def cancel(self):
        self.filechanged = False

    def is_framebased(self):
        return self.frames

    def is_edl(self):
        return self.edlfile

    def _getpos(self, start, new = False, first = True):
        pos = -1
        if len(self.edllist) == 0:
            pos = 0
        else:
            for i, linetup in enumerate(self.edllist):
                if new:
                    if linetup[0] > start:
                        pos = i
                        break 
                else:
                    if linetup[0] == start:
                        pos = i
                        if first:
                            break
            if new and (pos < 0):
                pos = len(self.edllist)
        return pos

    def _save_file(self):
        if self.edlfile:
            lines=self._build_edl()
        else:
            lines=self._build_txt()
        
        try:
            with open(self.file,"w") as file:
                file.write(lines)
        except:
            pass

    def _create_file(self):
        if path.isfile(self.file):
            self.file = ""
        else:    
            self.filechanged = False
            filename, fileext = path.splitext(self.file)
            if fileext.lower() == ".edl":
                self.edlfile = True
            else:
                self.edlfile = False
                self.frames = True

    def _readparse_file(self):
        if path.isfile(self.file):
            self.filechanged = False
            filename, fileext = path.splitext(self.file)
            if fileext.lower() == ".edl":
                self.edlfile = True
                self._parse_edl()
            else:
                self.edlfile = False
                self.frames = True
                self._parse_txt()
        else:
            self.file = ""

    def _num(self, s):
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                try:
                    val = 0
                    for ss in s.split(":"):
                        val = val*60 + float(ss)
                    return val
                except:
                    return 0

    def _parse_edl(self):
        try:
            with open(self.file) as file:
                for line in file:
                    linetup = ()
                    for i, ll in enumerate(line.split()):
                        if (i<2):
                            if ll[0] == '#':
                                self.frames = True
                                linetup += (self._num(ll[1:]),)
                            else:
                                self.frames = False
                                linetup += (self._num(ll),)
                        else:
                            linetup += (self._num(ll),)
                    self.edllist.append(linetup)
        except:
            pass

    def _parse_txt(self):
        proc_line = False
        self.textlines = ""
        try:
            with open(self.file) as file:
                for line in file:
                    if proc_line:
                        linetup = []
                        for i, ll in enumerate(line.split()):
                            linetup += (self._num(ll),)
                        linetup += (self._num(0),)
                        self.edllist.append(linetup)                    
                    else:
                        self.textlines += line
                        if (line[:3] == "---"):
                            proc_line = True
        except:
            pass

    def _build_edl(self):
        lines = ""
        for linetup in self.edllist:
            if len(linetup)==2:
                if self.frames:
                    line = "#%d\t\t%d\n"%(linetup[0],linetup[1])
                else:
                    line = "%g\t\t%d\n"%(linetup[0],linetup[1])
            elif len(linetup)==3:
                if self.frames:
                    line = "#%d\t#%d\t%d\n"%(linetup[0],linetup[1],linetup[2])
                else:
                    line = "%g\t%g\t%d\n"%(linetup[0],linetup[1],linetup[2])
            lines += line

        if (len(lines)>1):
            return lines[:-1]
        else:
            return lines

    def _build_txt(self):
        lines = self.textlines
        for linetup in self.edllist:
            if len(linetup)==3:
                line = "%d\t%d\n"%(linetup[0],linetup[1])
            lines += line

        if (len(lines)>1):
            return lines[:-1]
        else:
            return lines

    """
    EDL 1:
    5.3   7.1    0
    15    16.7   1
    420   822    3
    1     255.3  2
    720.1        2

    Only 0, cut and 3, commercial are used
    """

    """
    EDL 2:
    #127   #170    0
    #360   #400    1
    #10080 #19728  3
    #1     #6127   2
    #17282         2

    """

    """
    TXT:

    FILE PROCESSING COMPLETE 678900 FRAMES AT 25
    ------------------------
    12693   17792
    28578   34549
    43114   48222

    all processed as 0, cut
    """
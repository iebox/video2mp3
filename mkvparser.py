#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import os
import time, datetime

MARGIN = 80

def str2tms(str):
    return datetime.datetime.strptime(str.strip(), "%H:%M:%S,%f")

def tms2str(tms):
    return tms.strftime("%H:%M:%S")

def tms2lrc(tms):
    return "%02d:%02d.%02d" % (tms.hour * 60 + tms.minute, tms.second, tms.microsecond/10000)

def tms2seconds(hms):
    #return hms[0] * 3600 + hms[1] * 60 + hms[2]
    return (hms - datetime.datetime(1900, 1, 1)).total_seconds()

def tmsdiff(t1, t2):
    return (t1-t2).total_seconds()

def seconds2tms(seconds):
    pass

class Parser:
    def __init__(self, mkv):
        self.mkv = mkv
        self.subtitle = self.mkv + ".srt"
        self.clips = []

    def getSubtitleFile(self):
        cmd = "mkvextract tracks %s 5:%s" % (self.mkv, self.subtitle)
        os.system(cmd)

    def srt2lrc(self, srt):
        if srt:
            f = open(srt)
        else:
            f = open(self.subtitle)
        lines = f.readlines()
        i = 0
        last_end_tms = datetime.datetime(1900, 1, 1)
        clip_offset = 0
        while i < len(lines):
            line = lines[i]
            if line.find('-->') == -1:
                i = i + 1
                continue

            s = line.split('-->')
            tms = str2tms(s[0])
            tms_end = str2tms(s[1])
            if tms2seconds(tms) == 0:
                i = i + 1
                continue

            i = i + 1
            s = lines[i].strip()
            i = i + 1
            while i < len(lines) and len(lines[i].strip()) > 0:
                s = s + lines[i].strip()
                i = i + 1

            s = re.sub("<.*>", "", s)
            if len(s) == 0:
                continue

            print("[%s]%s" % (tms2lrc(tms), s))

            point = tms2seconds(tms)
            last_end_point = tms2seconds(last_end_tms)
            if point - last_end_point > MARGIN:
                self.clips.append(last_end_tms)
                self.clips.append(tms)
                clip_offset = tms

            clip_tms = tms - clip_offset

            last_end_tms = tms_end
        self.clips.append(last_end_tms)

        f.close()

    def splitmp3(self):
        i = 1
        while i < len(self.clips):
            if i % 2 == 0:
                print tms2str(self.clips[i-1]), tms2str(self.clips[i]), tmsdiff(self.clips[i], self.clips[i-1])
                cmd = "ffmpeg -i %s -acodec libmp3lame -ss %s -to %s %d.mp3" % \
                        (self.mkv, tms2str(self.clips[i-1]), tms2str(self.clips[i]), i/2)
                os.system(cmd)
            i = i + 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage srt2lrc.py mkvfile")
        sys.exit(1)

    parser = Parser(sys.argv[1])
    parser.getSubtitleFile()
    parser.srt2lrc(sys.argv[1])
    parser.splitmp3()

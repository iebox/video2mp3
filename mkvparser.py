#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import os

MARGIN = 80

def str2tms(str):
    time = str.split(':')
    ms = '00'
    if len(time) >= 3:
        hour = int(time[0])
        minute = int(time[1])
        seconds = time[2].split(',')
        second = int(seconds[0])
        ms = int(seconds[1])
    else:
        hour = 0
        minute = int(time[2])
        seconds = time[3].split(',')
        second = int(seconds[0])
        ms = int(seconds[1])
    return (hour, minute, second, ms)

def tms2str(tms):
    return "%d:%.2d:%d.%.2d" % (tms[0], tms[1], tms[2], tms[3])

def tms2seconds(hms):
    return hms[0] * 3600 + hms[1] * 60 + hms[2]

def seconds2tms(seconds):
    pass

class Parser:

    def srt2lrc(self, f):
        f = open(sys.argv[1])
        lines = f.readlines()
        i = 0
        last_end_tms = (0, 0, 0, 0)
        clips = []
        while i < len(lines):
            line = lines[i]
            if line.find('-->') == -1:
                i = i + 1
                continue

            s = line.split('-->')
            tms = str2tms(s[0])
            tms_end = str2tms(s[1])
            if tms[0] == 0 and tms[1] == 0 and tms[2] == 0 and tms[3] == 0:
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

            #print("[%.2d:%s.%.2s]%s" % (tms[0]*60 + tms[1], tms[2], tms[3], s))

            point = tms2seconds(tms)
            last_end_point = tms2seconds(last_end_tms)
            if point - last_end_point > MARGIN:
                #print tms2str(last_end_tms), tms2str(tms)
                clips.append(last_end_tms)
                clips.append(tms)
            last_end_tms = tms_end

        f.close()

    def splitmp3(self, clips):
        i = 1
        while i < len(clips):
            if i % 2 == 0:
                print tms2str(clips[i-1]), tms2str(clips[i]), tms2seconds(clips[i]) - tms2seconds(clips[i-1])
                os.system("./mkv2mp3.sh %s" % sys.argv[1])

            i = i + 1



if len(sys.argv) != 2:
    print("Usage srt2lrc.py file")
    sys.exit(1)

    parser = Parser(sys.argv[1])

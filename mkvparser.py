#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import os
import time, datetime

MARGIN = 40

def str2tms(str):
    return datetime.datetime.strptime(str.strip(), "%H:%M:%S,%f")

def tms2str(tms):
    return tms.strftime("%H:%M:%S")

def tms2lrc(tms):
    return "%02d:%02d.%02d" % (tms.hour * 60 + tms.minute, tms.second, tms.microsecond/10000)

def tms2seconds(hms):
    #return hms[0] * 3600 + hms[1] * 60 + hms[2]
    return (hms - datetime.datetime(1900, 1, 1)).total_seconds()

def delta2tms(delta):
    return datetime.datetime(1900,1,1) + delta

def tmsdiff(t1, t2):
    return (t1-t2).total_seconds()

def seconds2tms(seconds):
    pass

class Parser:
    def __init__(self, mkv):
        self.mkv = mkv
        #self.subtitle = os.path.basename(self.mkv) + ".srt"
        self.tms_clips = []
        self.file_dir = os.path.basename(self.mkv)
        os.system("mkdir \"%s\"" % self.file_dir)
        self.subtitle = os.path.join(self.file_dir, "0.srt")
        self.mp3 = os.path.join(self.file_dir, "0.mp3")
        self.lyric = ""
        self.lyrics_clips = []

    def getSubtitleFile(self):
        if not os.path.exists(self.subtitle):
            track_id = os.popen("mkvinfo \"%s\"|grep \"track ID for mkvmerge\"|tail -1" % self.mkv).read()[-3:-2]
            track_id = 4
            cmd = "mkvextract tracks \"%s\" %s:%s" % (self.mkv, track_id, self.subtitle)
            print cmd
            os.system(cmd)

    def getmp3(self):
        if not os.path.exists(self.mp3):
            cmd = "ffmpeg -i \"%s\" -acodec libmp3lame -ar 44100 -ab 192k \"%s\"" % \
                    (self.mkv, self.mp3)
            os.system(cmd)

    def srt2lrc(self):
        os.system("rm -f \"%s\"/*.lrc" % self.file_dir)
        f = open(self.subtitle)
        lines = f.readlines()
        i = 0
        last_end_tms = datetime.datetime(1899, 1, 1)
        clip_offset = datetime.datetime(1900, 1, 1)
        self.lyrics_clips = []
        lrc_str = ""
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

            self.lyric += "[%s]%s\n" % (tms2lrc(tms), s)

            point = tms2seconds(tms)
            last_end_point = tms2seconds(last_end_tms)
            if point - last_end_point > MARGIN:
                self.lyrics_clips.append(lrc_str)
                self.tms_clips.append(last_end_tms)
                self.tms_clips.append(tms)
                clip_offset = tms
                lrc_str = ""

            clip_tms = delta2tms(tms - clip_offset)
            lrc_str += "[%s]%s\n" % (tms2lrc(clip_tms), s)

            last_end_tms = tms_end
        self.tms_clips.append(last_end_tms)
        self.lyrics_clips.append(lrc_str)

        f.close()
        i = 1
        while i < len(self.lyrics_clips):
            f = open(os.path.join(self.file_dir, "%d.lrc" % i), 'w')
            f.write(self.lyrics_clips[i])
            f.close()
            i = i + 1

        f = open(os.path.join(self.file_dir, "0.lrc"), 'w')
        f.write(self.lyric)
        f.close()

    def splitmp3(self):
        os.system("rm -f \"%s\"/*.mp3" % self.file_dir)
        i = 1
        while i < len(self.tms_clips):
            if i % 2 == 0:
                mp3_path = os.path.join(self.file_dir, "%d.mp3" % (i/2))
                print tms2str(self.tms_clips[i-1]), tms2str(self.tms_clips[i]), tmsdiff(self.tms_clips[i], self.tms_clips[i-1])
                cmd = "ffmpeg -i \"%s\" -acodec libmp3lame -ss %s -to %s -ar 44100 -ab 192k \"%s\"" % \
                        (self.mkv, tms2str(self.tms_clips[i-1]), tms2str(self.tms_clips[i]), mp3_path)
                os.system(cmd)
                #cmd = "id3v2 --USLT \"%s\" \"%s\"" % (self.lyrics_clips[i/2], mp3_path)
                #os.system(cmd)
                #cmd = "id3v2 -c tingmofun \"%s\"" % mp3_path
                #os.system(cmd)
            i = i + 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage srt2lrc.py video_file srt_file")
        sys.exit(1)

    parser = Parser(sys.argv[1])
    if len(sys.argv) >= 3:
        os.system("cp \"%s\" \"%s\"" % (sys.argv[2], parser.subtitle))
    else:
        parser.getSubtitleFile()

    parser.getmp3()
    parser.srt2lrc()
    #parser.splitmp3()

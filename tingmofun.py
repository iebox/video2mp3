#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import os
import time, datetime

def str2tms(str):
    return datetime.datetime.strptime(str.strip(), "%H:%M:%S,%f")

def tms2str(tms):
    return tms.strftime("%H:%M:%S")

def tms2lrc(tms):
    return "%02d:%02d.%02d" % (tms.hour * 60 + tms.minute, tms.second, tms.microsecond/10000)

def tms2seconds(hms):
    #return hms[0] * 3600 + hms[1] * 60 + hms[2]
    if hms.year == 1901:
        return -500
    return (hms - datetime.datetime(1900, 1, 1)).total_seconds()

def delta2tms(delta):
    return datetime.datetime(1900,1,1) + delta

def tmsdiff(t1, t2):
    return (t1-t2).total_seconds()

def seconds2tms(seconds):
    pass

class Parser:
    def __init__(self, video, root):
        self.margin = 90
        self.title = "default"
        self.video = ""
        filename, self.type = os.path.splitext(video)
        if self.type == ".iso":
            volume_path = os.popen("hdiutil mount %s" % video).read().strip().split("\t")[-1]
            self.title = os.path.basename(volume_path)
            self.video = os.path.join(volume_path, "BDMV/STREAM/00000.m2ts")
        elif self.type == ".mkv":
            if filename[-4:] == "CMCT":
                infos = os.path.basename(filename).split(".")
                self.title = ".".join(infos[1:-5])
                self.year = infos[2]
            else:
                self.title = os.path.basename(filename)
            self.video = video

        self.root = os.path.join(root, self.title)
        self.subtitle = os.path.join(self.root, "%s.srt" % self.title)
        self.mp3 = os.path.join(self.root, "%s.mp3" % self.title)
        self.lyric = ""
        self.lyrics_clips = []

        if not os.path.exists(self.root):
            os.system("mkdir \"%s\"" % self.root)

    def getmp3(self):
        if not os.path.exists(self.mp3):
            cmd = "ffmpeg -i \"%s\" -acodec libmp3lame -ar 44100 -ab 192k \"%s\"" % \
                    (self.video, self.mp3)
            os.system(cmd)

            cmd = "id3v2 -t %s -c tingmofun \"%s\"" % (self.title, self.mp3)
            os.system(cmd)

    def getSubtitleFile(self):
        if not os.path.exists(self.subtitle) and self.type == ".mkv":
            print os.popen("mkvinfo \"%s\"|grep -E \"track ID for mkvmerge|Codec ID|Name:\"" % self.video).read()
            track_id = raw_input("please input track id:")
            type = os.popen("mkvinfo \"%s\"|grep \"Codec ID\"" % self.video).readlines()[int(track_id)].split("/")[-1].strip()
            print type
            if type == "ASS":
                path = os.path.join(self.root, "%s.ass" % self.title)
                os.system("mkvextract tracks \"%s\" %s:%s" % (self.video, track_id, path))
                os.system("ffmpeg -i %s -scodec srt %s" % (path, self.subtitle))
            else:
                os.system("mkvextract tracks \"%s\" %s:%s" % (self.video, track_id, self.subtitle))

    def srt2lrc(self):
        self.tms_clips = []
        if not os.path.exists(self.subtitle):
            print "no subrip file found"
            return
        os.system("rm -f \"%s\"/*.lrc" % self.root)
        f = open(self.subtitle)
        lines = f.readlines()
        i = 0
        last_end_tms = datetime.datetime(1901, 1, 1)
        clip_offset = datetime.datetime(1900, 1, 1)
        self.lyrics_clips = []
        lrc_str = ""
        isFirst = 1
        self.tms_clips.append(datetime.datetime(1900,1,1))
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

            s = re.sub("<.*?>", "", s)
            if len(s) == 0:
                continue

            self.lyric += "[%s]%s\n" % (tms2lrc(tms), s)

            if tms.minute % 20 == 0 and isFirst and tms2seconds(tms) > 60:
                isFirst = 0
                self.tms_clips.append(tms)

                self.lyrics_clips.append(lrc_str)
                clip_offset = tms
                lrc_str = ""
            if tms.minute % 20 != 0:
                isFirst = 1

            #point = tms2seconds(tms)
            #last_end_point = tms2seconds(last_end_tms)
            #if point - last_end_point > self.margin:
            #    self.lyrics_clips.append(lrc_str)
            #    self.tms_clips.append(last_end_tms)
            #    self.tms_clips.append(tms)
            #    clip_offset = tms
            #    lrc_str = ""

            clip_tms = delta2tms(tms - clip_offset)
            lrc_str += "[%s]%s\n" % (tms2lrc(clip_tms), s)

            last_end_tms = tms_end
        self.tms_clips.append(last_end_tms)
        self.lyrics_clips.append(lrc_str)

        f.close()
        i = 0
        while i < len(self.lyrics_clips):
            f = open(os.path.join(self.root, "%d.lrc" % (i+1)), 'w')
            f.write(self.lyrics_clips[i])
            f.close()
            i = i + 1

        f = open(os.path.join(self.root, "%s.lrc" % self.title), 'w')
        f.write(self.lyric)
        f.close()

    def splitmp3(self):
        os.system("rm -f \"%s\"/[0-9].mp3" % self.root)
        i = 1
        while i < len(self.tms_clips):
            mp3_path = os.path.join(self.root, "%d.mp3" % i)
            print tms2str(self.tms_clips[i-1]), tms2str(self.tms_clips[i]), tmsdiff(self.tms_clips[i], self.tms_clips[i-1])
            cmd = "ffmpeg -i \"%s\" -acodec copy -ss %s -to %s \"%s\"" % \
                    (self.mp3, tms2str(self.tms_clips[i-1]), tms2str(self.tms_clips[i]), mp3_path)
            os.system(cmd)
            #cmd = "id3v2 --USLT \"%s\" \"%s\"" % (self.lyrics_clips[i/2], mp3_path)
            #os.system(cmd)
            cmd = "id3v2 -t %s_%d-%d -c tingmofun \"%s\"" % (self.title, len(self.tms_clips)-1, i, mp3_path)
            os.system(cmd)
            i = i + 1

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage srt2lrc.py video_file outputdir")
        sys.exit(1)

    parser = Parser(sys.argv[1], sys.argv[2])
    parser.getSubtitleFile()
    parser.getmp3()
    #while len(parser.lyrics_clips) < 8 or len(parser.lyrics_clips) > 20:
    #    if len(parser.lyrics_clips) < 8:
    #        parser.margin = parser.margin - 10
    #    else:
    #        parser.margin = parser.margin + 10
    parser.srt2lrc()
    parser.splitmp3()

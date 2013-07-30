#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re

if len(sys.argv) != 2:
    print("Usage srt2lrc.py file")
    sys.exit(1)

f = open(sys.argv[1])
lines = f.readlines()
i = 0
while i < len(lines):
    line = lines[i]
    if line.find('-->') == -1:
        i = i + 1
        continue

    s = line.split('-->')
    time = s[0].split(':')
    ms = '00'
    if len(time) >= 3:
        hour = time[0]
        minute = time[1]
        seconds = time[2].split(',')
        second = seconds[0]
        ms = seconds[1]
    else:
        hour = 0
        minute = time[2]
        seconds = time[3].split(',')
        second = seconds[0]
        ms = seconds[1]

    if int(hour) == 0 and int(minute) == 0 and int(second) == 0 and int(ms) == 0:
        i = i + 1
        continue

    i = i + 1
    s = lines[i].strip()
    i = i + 1
    while i < len(lines) and len(lines[i].strip()) > 0:
        s = s + lines[i].strip()
        i = i + 1

    s = re.sub("<.*>", "", s)
    if len(s) > 0:
        print("[%.2d:%s.%.2s]%s" % (int(hour)*60+int(minute.strip()), second.strip(), ms.strip(), s))

f.close()

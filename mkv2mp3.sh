#!/bin/sh

ffmpeg -i "$1" -acodec libmp3lame -ss $2 -to $3 $4

#ffmpeg -i "$1" -acodec libmp3lame "$1".mp3

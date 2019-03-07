#!/usr/bin/env python
# -*- coding: utf-8 -*-

BASEDIR = "/Users/yuanliqiang/workspace/y2t"
DATADIR = "/Volumes/SamsungTF"
# YOUTUBEPARAM="-f '(bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4])' --buffer-size 16k --write-thumbnail --retries infinite"
YOUTUBEPARAM = "-f '(bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4])' --buffer-size 16k --retries infinite"
YOUTUBESUB="--write-auto-sub --sub-lang=zh-Hans --convert-subs=srt"

PROXYLIST = []

PROXYLIST.append("127.0.0.1:1080")
PROXYLIST.append("127.0.0.1:1081")
PROXYLIST.append("127.0.0.1:1082")
PROXYLIST.append("127.0.0.1:1083")

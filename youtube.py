#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, subprocess, time
import hashlib
from moviepy.editor import VideoFileClip

import cnf


def checkproxy(proxy):
    shell = "curl -I -x socks5://{proxy} https://www.google.com/".format(proxy=proxy)
    idx = 0
    while True:
        idx += 1
        p = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
        out = out.splitlines()
        if len(out) > 1 and out[0].decode('utf-8').find("200") > 0:
            print("proxy: {proxy} OK!".format(proxy=proxy))
            break
        elif idx == 5:
            exit(0)
        time.sleep(3)


def download(proxy, display):
    shell = ""
    if "sub" in display:
        shell = "{bin}/youtube-dl {param} {sub} --proxy socks5://{proxy} {url} -o '{dir}/download/%(title)s.%(ext)s'".format(
            bin=cnf.BASEDIR,
            param=cnf.YOUTUBEPARAM,
            sub=cnf.YOUTUBESUB,
            proxy=proxy,
            url=display["url"],
            dir=cnf.DATADIR
        )
    else:
        shell = "{bin}/youtube-dl {param} --proxy socks5://{proxy} {url} -o '{dir}/download/%(title)s.%(ext)s'".format(
            bin=cnf.BASEDIR,
            param=cnf.YOUTUBEPARAM,
            proxy=proxy,
            url=display["url"],
            dir=cnf.DATADIR
        )
    os.system(shell)

    shell = "{bin}/youtube-dl {param} --proxy socks5://{proxy} {url} --get-title".format(
        bin=cnf.BASEDIR,
        param=cnf.YOUTUBEPARAM,
        proxy=proxy,
        url=display["url"]
    )
    p = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    title = out.strip().decode('utf-8')

    hl = hashlib.md5()
    hl.update(title.encode())
    md5str = hl.hexdigest()
    display["title"] = title
    display["tmp"] = md5str
    display["middle"] = md5str + ".m.mp4"
    display["target"] = title.replace("'", " ") + ".mp4"

    decode(proxy, display)


def decode(proxy, display):
    src_file = "{dir}/{title}.mp4".format(dir=cnf.DATADIR, title=display["title"])
    if os.path.exists(src_file):
        subtitle(display)
        cut(display)
    else:
        download(proxy, display)


def cut(display):
    shell = ["ffmpeg"]
    if "ss" in display:
        shell.append("-ss {ss}".format(ss=display["ss"]))
    if "to" in display:
        shell.append("-to {to}".format(to=display["to"]))
    if "t" in display:
        clip = VideoFileClip("{dir}/{tmp}.mp4".format(dir=cnf.DATADIR, tmp=display["tmp"]))
        clip_duration = clip.duration - display["ss"] - display["t"]
        shell.append("-t {t}".format(t=clip_duration))
    shell.append("-i {dir}/{tmp}.mp4".format(dir=cnf.DATADIR, tmp=display["tmp"]))
    if "lx" in display:
        delogo = "x={lx}:y={ly}:w={w}:h={h}".format(
            x=display["lx"],
            y=display["ly"],
            w=display["rx"]-display["lx"],
            h=display["ry"]-display["ly"]
        )
        shell.append("-vf delogo={delogo} -vcodec h264_videotoolbox -b:v 5000K".format(delogo=delogo))
    else:
        shell.append("-vcodec copy -acodec copy")

    shell.append("{dir}/{middle}".format(dir=cnf.DATADIR, middle=display["middle"]))

    os.system(" ".join(shell))

    os.system("ffmpeg 'concat:{head}|{dir}/{middle}' -vcodec copy -acodec copy {target}".format(
        head=cnf.HDADMP4,
        dir=cnf.DATADIR,
        middle=display["middle"],
        target=display["target"]
    ))


def subtitle(display):
    if "sub" in display:
        os.rename("{dir}/{title}.zh-Hans.srt".format(dir=cnf.DATADIR, title=display["title"]),
                  "{dir}/{tmp}.srt".format(dir=cnf.DATADIR, tmp=display["tmp"]))
        os.system(
            "ffmpeg -i {dir}/{title}.mp4 -vf subtitles={dir}/{tmp}.srt -vcodec h264_videotoolbox -b:v 5000K {dir}/{tmp}.mp4".format(
                dir=cnf.DATADIR,
                title=display["title"],
                tmp=display["tmp"]
            ))
    else:
        os.rename("{dir}/{title}.mp4".format(dir=cnf.DATADIR, title=display["title"]),
                  "{dir}/{tmp}.mp4".format(dir=cnf.DATADIR, tmp=display["tmp"]))

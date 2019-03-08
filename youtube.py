#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, subprocess, time
import hashlib, re
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
    shell = "{bin}/youtube-dl {param} --proxy socks5://{proxy} {url} --get-title".format(
        bin=cnf.BASEDIR,
        param=cnf.YOUTUBEPARAM,
        proxy=proxy,
        url=display["url"]
    )
    p = subprocess.Popen(shell, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    title = out.strip().decode('utf-8')
    display["id"] = display["url"].replace("https://www.youtube.com/watch?v=", "")

    if "sub" in display:
        shell = "{bin}/youtube-dl {param} {sub} --proxy socks5://{proxy} {url} -o '{dir}/%(id)s.%(ext)s'".format(
            bin=cnf.BASEDIR,
            param=cnf.YOUTUBEPARAM,
            sub=cnf.YOUTUBESUB,
            proxy=proxy,
            url=display["url"],
            dir=cnf.DATADIR
        )
    else:
        shell = "{bin}/youtube-dl {param} --proxy socks5://{proxy} {url} -o '{dir}/%(id)s.%(ext)s'".format(
            bin=cnf.BASEDIR,
            param=cnf.YOUTUBEPARAM,
            proxy=proxy,
            url=display["url"],
            dir=cnf.DATADIR
        )
    os.system(shell)

    hl = hashlib.md5()

    hl.update(title.encode())
    md5str = hl.hexdigest()
    display["title"] = re.sub(r'[\\\/\:\*\?\"\'\<\>\|\.]', "", title)
    display["tmp"] = md5str
    display["middle"] = md5str + ".m.mp4"
    display["target"] = display["id"] + ".mp4"

    decode(proxy, display)


def decode(proxy, display):
    src_file = "{dir}/{id}.mp4".format(dir=cnf.DATADIR, id=display["id"])
    print(src_file)
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
            lx=display["lx"],
            ly=display["ly"],
            w=display["rx"] - display["lx"],
            h=display["ry"] - display["ly"]
        )
        shell.append("-vf delogo={delogo} -vcodec h264_videotoolbox -b:v 5000K".format(delogo=delogo))
    else:
        shell.append("-vcodec copy -acodec copy")

    shell.append("{dir}/{middle}".format(dir=cnf.DATADIR, middle=display["middle"]))
    os.system(" ".join(shell))

    os.system("ffmpeg -i {dir}/{middle} -vcodec copy -acodec copy -vbsf h264_mp4toannexb {dir}/{id}.ts".format(
        dir=cnf.DATADIR,
        middle=display["middle"],
        id=display["id"]
    ))

    os.system(
        "ffmpeg -i 'concat:{head}|{dir}/{id}.ts' -acodec copy -vcodec copy -absf aac_adtstoasc {dir}/{target}".format(
            head=cnf.HDADMP4,
            dir=cnf.DATADIR,
            id=display["id"],
            target=display["target"]
        ))

    os.remove("{dir}/{middle}".format(dir=cnf.DATADIR, middle=display["middle"]))
    os.remove("{dir}/{id}.ts".format(dir=cnf.DATADIR, id=display["id"]))
    os.remove("{dir}/{tmp}.mp4".format(dir=cnf.DATADIR, tmp=display["tmp"]))

    os.rename("{dir}/{target}".format(dir=cnf.DATADIR, target=display["target"]),
              "{dir}/{title}.mp4".format(dir=cnf.DATADIR, title=display["title"]))


def subtitle(display):
    if "sub" in display:
        os.rename("{dir}/{id}.zh-Hans.srt".format(dir=cnf.DATADIR, id=display["id"]),
                  "{dir}/{tmp}.srt".format(dir=cnf.DATADIR, tmp=display["tmp"]))
        os.system(
            "ffmpeg -i {dir}/{id}.mp4 -vf subtitles={dir}/{tmp}.srt -vcodec h264_videotoolbox -b:v 5000K {dir}/{tmp}.mp4".format(
                dir=cnf.DATADIR,
                id=display["id"],
                tmp=display["tmp"]
            ))
        os.remove("{dir}/{id}.mp4".format(dir=cnf.DATADIR, id=display["id"]))
        os.remove("{dir}/{tmp}.srt".format(dir=cnf.DATADIR, tmp=display["tmp"]))
    else:
        os.rename("{dir}/{id}.mp4".format(dir=cnf.DATADIR, id=display["id"]),
                  "{dir}/{tmp}.mp4".format(dir=cnf.DATADIR, tmp=display["tmp"]))

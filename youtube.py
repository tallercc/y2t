#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, subprocess, time, hashlib, re

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


def time2duration(t):
    h, m, s = t.split(':')
    if s.find(".") > 0:
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms.ljust(3, "0")) * 0.001
    else:
        return int(h) * 3600 + int(m) * 60 + int(s)


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
    hl = hashlib.md5()

    hl.update(title.encode())
    md5str = hl.hexdigest()
    display["title"] = re.sub(r'[\\\/\:\*\?\"\'\<\>\|\.]', "", title)
    display["tmp"] = md5str
    display["middle"] = md5str + "_m.mp4"
    display["target"] = md5str + "_t.mp4"
    display["id"] = md5str + "_id"

    if "sub" in display:
        shell = "{bin}/youtube-dl {param} {sub} --proxy socks5://{proxy} {url} -o '{dir}/{id}.%(ext)s'".format(
            bin=cnf.BASEDIR,
            param=cnf.YOUTUBEPARAM,
            sub=cnf.YOUTUBESUB,
            proxy=proxy,
            url=display["url"],
            dir=cnf.DATADIR,
            id=display["id"]
        )
    else:
        shell = "{bin}/youtube-dl {param} --proxy socks5://{proxy} {url} -o '{dir}/{id}.%(ext)s'".format(
            bin=cnf.BASEDIR,
            param=cnf.YOUTUBEPARAM,
            proxy=proxy,
            url=display["url"],
            dir=cnf.DATADIR,
            id=display["id"]
        )
    os.system(shell)

    decode(proxy, display)


def decode(proxy, display):
    src_file = "{dir}/{id}.mp4".format(dir=cnf.DATADIR, id=display["id"])
    # print(src_file)
    if os.path.exists(src_file):
        # subtitle(display)
        cut(display)
    else:
        download(proxy, display)


# mkfifo 3d2b3e859dd6a7fe2689ce85906d9fbd.ts ;
# ffmpeg -y -i 3d2b3e859dd6a7fe2689ce85906d9fbd_id.mp4 -vf subtitles=a.srt -vcodec h264_videotoolbox -s hd1080 -b:v 4582K -acodec copy -f matroska pipe:1 |
# ffmpeg -i pipe:0 -vf delogo=x=1360:y=1030:w=280:h=30 -vcodec h264_videotoolbox -s hd1080 -b:v 4582K -acodec copy -f matroska pipe:1 |
# ffmpeg -y -i pipe:0 -vcodec copy -acodec copy -bsf:v h264_mp4toannexb -f mpegts 3d2b3e859dd6a7fe2689ce85906d9fbd.ts |
# ffmpeg -y -f mpegts -i "concat:dota2.mp4.ts|3d2b3e859dd6a7fe2689ce85906d9fbd.ts" -vcodec copy -acodec copy -bsf:a aac_adtstoasc 3d2b3e859dd6a7fe2689ce85906d9fbd_t.mp4
def cut(display):
    p = subprocess.Popen("ffmpeg -i {dir}/{id}.mp4 2>&1".format(dir=cnf.DATADIR, id=display["id"]), shell=True,
                         stdout=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode('utf-8')
    # movie info
    mt = re.search(r'Duration: ([0-9:\.]+),', out, re.M | re.I).group(1)
    mp = out.find("1920x1080") > 0
    kbs = re.search(r'bitrate: ([0-9]+) kb', out, re.M | re.I).group(1)
    # tmp.ts
    if os.path.exists("{dir}/{tmp}.ts".format(dir=cnf.DATADIR, tmp=display["tmp"])):
        os.remove("{dir}/{tmp}.ts".format(dir=cnf.DATADIR, tmp=display["tmp"]))
    os.system("mkfifo {dir}/{tmp}.ts".format(dir=cnf.DATADIR, tmp=display["tmp"]))
    # head ts
    if not os.path.exists("{dir}/{head}.ts".format(dir=cnf.DATADIR, head=display["head"])):
        os.system(
            "ffmpeg -y -i {headdir}/{head} -vcodec copy -acodec copy -bsf:v h264_mp4toannexb -f mpegts {dir}/{head}.ts".format(
                headdir=cnf.HEADDIR,
                head=display["head"],
                dir=cnf.DATADIR
            ))

    shell = ["cd {dir};".format(dir=cnf.DATADIR)]
    # cut movie
    havecut =False
    cutshell = ["ffmpeg -y"]
    if "ss" in display:
        havecut = True
        cutshell.append("-ss {ss}".format(ss=display["ss"]))
    if "to" in display:
        havecut = True
        cutshell.append("-to {to}".format(to=display["to"]))
    if "t" in display:
        havecut = True
        clip_duration = time2duration(mt) - display["ss"] - display["t"]
        cutshell.append("-t {t}".format(t=clip_duration))
    if havecut:
        cutshell.append("-i {id}.mp4 -vcodec copy -acodec copy -f matroska pipe:1 |".format(id=display["id"]))
        shell.append(" ".join(cutshell))
        shell.append("ffmpeg -y -i pipe:0")
    else:
        shell.append("ffmpeg -y -i {id}.mp4".format(id=display["id"]))
    #movie sub
    havesub = False
    vfshell = []
    subshell = []
    if "sub" in display and os.path.exists("{dir}/{id}.zh-Hans.srt".format(dir=cnf.DATADIR, id=display["id"])):
        havesub = True
        os.rename("{dir}/{id}.zh-Hans.srt".format(dir=cnf.DATADIR, id=display["id"]),
                  "{dir}/{tmp}.srt".format(dir=cnf.DATADIR, tmp=display["tmp"]))
        vfshell.append("subtitles={tmp}.srt".format(tmp=display["tmp"]))

    if "lx" in display:
        havesub = True
        delogo = "x={lx}:y={ly}:w={w}:h={h}".format(
            lx=display["lx"],
            ly=display["ly"],
            w=display["rx"] - display["lx"],
            h=display["ry"] - display["ly"]
        )
        vfshell.append(
            "delogo={delogo}".format(
                delogo=delogo
            ))
    if havesub:
        subshell.append("-vf \"{vf}\" -vcodec h264_videotoolbox -s hd1080 -b:v {kbs}K -acodec copy -f matroska pipe:1 |".format(
            vf=";".join(vfshell),
            kbs=kbs
        ))
        shell.append(" ".join(subshell))
        shell.append("ffmpeg -y -i pipe:0")
    elif not mp:
        subshell.append("-s hd1080 -b:v {kbs}K -acodec copy -f matroska pipe:1 |")
        shell.append(" ".join(subshell))
        shell.append("ffmpeg -y -i pipe:0")
    elif not havecut:
        shell.append("ffmpeg -y -i {id}.mp4".format(id=display["id"]))

    shell.append(
        "-vcodec copy -acodec copy -bsf:v h264_mp4toannexb -f mpegts {tmp}.ts &".format(
            middle=display["middle"],
            tmp=display["tmp"]
        ))
    shell.append(
        "ffmpeg -y -f mpegts -i \"concat:{head}.ts|{tmp}.ts\" -vcodec copy -acodec copy -bsf:a aac_adtstoasc {target}".format(
            head=display["head"],
            tmp=display["tmp"],
            target=display["target"]
        ))
    #print(" ".join(shell))
    os.system(" ".join(shell))

    file_path = "{dir}/{tmp}.srt".format(dir=cnf.DATADIR, tmp=display["tmp"])
    if os.path.exists(file_path):
        os.remove(file_path)

    os.rename("{dir}/{target}".format(dir=cnf.DATADIR, target=display["target"]),
              "{dir}/{title}.mp4".format(dir=cnf.DATADIR, title=display["title"]))

    os.rename("{dir}/{id}.jpg".format(dir=cnf.DATADIR, id=display["id"]),
              "{dir}/{title}.jpg".format(dir=cnf.DATADIR, title=display["title"]))

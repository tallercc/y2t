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


def cut(display):
    p = subprocess.Popen("ffmpeg -i {dir}/{id}.mp4 2>&1".format(dir=cnf.DATADIR, id=display["id"]), shell=True,
                         stdout=subprocess.PIPE)
    out, err = p.communicate()
    out = out.decode('utf-8')
    # print(out)
    mt = re.search(r'Duration: ([0-9:\.]+),', out, re.M | re.I).group(1)
    mp = out.find("1920x1080") > 0
    kbs = re.search(r'bitrate: ([0-9]+) kb', out, re.M | re.I).group(1)

    if "sub" in display:
        os.rename("{dir}/{id}.zh-Hans.srt".format(dir=cnf.DATADIR, id=display["id"]),
                  "{dir}/{tmp}.srt".format(dir=cnf.DATADIR, tmp=display["tmp"]))
        os.system(
            "ffmpeg -y -i {dir}/{id}.mp4 -vf subtitles={dir}/{tmp}.srt -vcodec h264_videotoolbox -s hd1080 -b:v {kbs}K -acodec copy {dir}/{tmp}.mp4 ".format(
                dir=cnf.DATADIR,
                id=display["id"],
                tmp=display["tmp"],
                kbs=kbs
            ))
    else:
        os.system("ln -s {dir}/{id}.mp4 {dir}/{tmp}.mp4 ".format(dir=cnf.DATADIR, id=display["id"], tmp=display["tmp"]))
    shell = []
    shell.append("cd {dir} ; mkfifo {tmp}_h.ts {tmp}.ts ;".format(
        dir=cnf.DATADIR,
        tmp=display["tmp"]
    ))
    shell.append("ffmpeg -y")
    if "ss" in display:
        shell.append("-ss {ss}".format(ss=display["ss"]))
    if "to" in display:
        shell.append("-to {to}".format(to=display["to"]))
    if "t" in display:
        clip_duration = time2duration(mt) - display["ss"] - display["t"]
        shell.append("-t {t}".format(t=clip_duration))
    shell.append("-i {dir}/{tmp}.mp4".format(dir=cnf.DATADIR, tmp=display["tmp"]))
    if "lx" in display:
        delogo = "x={lx}:y={ly}:w={w}:h={h}".format(
            lx=display["lx"],
            ly=display["ly"],
            w=display["rx"] - display["lx"],
            h=display["ry"] - display["ly"]
        )

        shell.append(
            "-vf delogo={delogo} -vcodec h264_videotoolbox -s hd1080 -b:v {kbs}K -acodec copy".format(delogo=delogo,
                                                                                                      kbs=kbs))
    else:
        if mp:
            shell.append("-vcodec copy -acodec copy")
        else:
            shell.append("-vcodec h264_videotoolbox -s hd1080 -b:v {kbs}K -acodec copy".format(kbs=kbs))

    shell.append("{dir}/{middle}".format(dir=cnf.DATADIR, middle=display["middle"]))

    os.system(" ".join(shell))
    shell = []
    shell.append(
        "ffmpeg -y -i {head} -vcodec copy -acodec copy -bsf:v h264_mp4toannexb -f mpegts {dir}/{tmp}_h.ts 2> /dev/null &".format(
            head=cnf.HDADMP4,
            kbs=kbs,
            dir=cnf.DATADIR,
            tmp=display["tmp"]
        ))
    shell.append(
        "ffmpeg -y -i {dir}/{middle} -vcodec copy -acodec copy -bsf:v h264_mp4toannexb -f mpegts {dir}/{tmp}.ts 2> /dev/null &".format(
            dir=cnf.DATADIR,
            middle=display["middle"],
            tmp=display["tmp"]
        ))
    shell.append(
        "ffmpeg -y -f mpegts -i \"concat:{dir}/{tmp}_h.ts|{dir}/{tmp}.ts\" -vcodec copy -acodec copy -bsf:a aac_adtstoasc {dir}/{target}".format(
            dir=cnf.DATADIR,
            tmp=display["tmp"],
            target=display["target"]
        ))

    os.system(" ".join(shell))

    file_path="{dir}/{tmp}.mp4".format(dir=cnf.DATADIR,tmp=display["tmp"])
    if os.path.exists(file_path):
        os.remove(file_path)
    file_path = "{dir}/{middle}".format(dir=cnf.DATADIR, middle=display["middle"])
    if os.path.exists(file_path):
        os.remove(file_path)
    file_path = "{dir}/{tmp}.srt".format(dir=cnf.DATADIR, tmp=display["tmp"])
    if os.path.exists(file_path):
        os.remove(file_path)

    os.rename("{dir}/{target}".format(dir=cnf.DATADIR, target=display["target"]),
              "{dir}/{title}.mp4".format(dir=cnf.DATADIR, title=display["title"]))

    os.rename("{dir}/{id}.jpg".format(dir=cnf.DATADIR, id=display["id"]),
              "{dir}/{title}.jpg".format(dir=cnf.DATADIR, title=display["title"]))


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

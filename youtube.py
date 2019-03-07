#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, subprocess, time
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
        time.sleep(5)


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
    print(title)

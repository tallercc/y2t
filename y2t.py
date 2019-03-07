#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, time, math
from multiprocessing import Process

import cnf
import list
import youtube


def chunks(arr, m):
    n = int(math.ceil(len(arr) / float(m)))
    return [arr[i:i + n] for i in range(0, len(arr), n)]


def foreach(proxy, displays):
    for item in displays:
        p = Process(target=youtube.download, args=(proxy, item))
        p.start()
        p.join()


if __name__ == "__main__":
    arr = chunks(list.DISPLAYLIST, len(cnf.PROXYLIST))
    l = len(arr)
    idx = 0
    plist = []

    for proxy in cnf.PROXYLIST:
        youtube.checkproxy(proxy)

    for proxy in cnf.PROXYLIST:
        if idx < l:
            p = Process(target=foreach, args=(proxy, arr[idx]))
            idx = idx + 1
            plist.append(p)
            p.start()

    for p in plist:
        p.join()

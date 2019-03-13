#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, time, math, json
from multiprocessing import Process
from flask import Flask, request, jsonify

import cnf
import list
import youtube

app = Flask(__name__)


def chunks(arr, m):
    n = int(math.ceil(len(arr) / float(m)))
    return [arr[i:i + n] for i in range(0, len(arr), n)]


def foreach(proxy, displays):
    for item in displays:
        p = Process(target=youtube.download, args=(proxy, item))
        p.start()
        p.join()


@app.route('/', methods=['POST'])
def y2thandler():
    if request.method == 'GET':
        return jsonify({"success": "false"})
    else:
        displaylist =request.get_json()
        arr = chunks(displaylist, len(cnf.PROXYLIST))
        l = len(arr)
        idx = 0
        plist = []

        #    for proxy in cnf.PROXYLIST:
        #        youtube.checkproxy(proxy)

        for proxy in cnf.PROXYLIST:
            if idx < l:
                p = Process(target=foreach, args=(proxy, arr[idx]))
                idx = idx + 1
                plist.append(p)
                p.start()
    return jsonify({"success": "true"})

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080)

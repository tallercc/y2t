#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, time, math, json
from multiprocessing import Process
from flask import Flask, request, jsonify,render_template

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

# curl --header "Content-Type: application/json" --request POST
# --data '[{"url":"https://www.youtube.com/watch?v=Z-pU-wKr8ew","head":"dota2.mp4", "ss": 11, "t": 15,"lx":1360,"ly":1030,"rx":1640,"ry":1060},
# {"url":"https://www.youtube.com/watch?v=xD-iKQcDM-o","head":"dota2.mp4", "ss": 11, "t": 15,"lx":1360,"ly":1030,"rx":1640,"ry":1060}]'
# http://127.0.0.1:8080/y2t
@app.route('/y2t', methods=['POST'])
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
    return jsonify({"askid": round(time.time()*1000)})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask')
def ask():
    return render_template('ask.html')

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080)
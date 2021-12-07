#!/usr/bin/env python3
from flask import Flask, render_template, Response, request, jsonify
from typing import Final
from parking.motion_detector import *
import json
import sys

app = Flask(__name__)

default_url: Final[str] = 'https://frn.rtsp.me/SAUNckeorr8y8CRuAwZspw/1636313331/hls/yssKD2RY.m3u8?ip=93.75.241.227'
detector = MotionDetector(default_url)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/slot', methods=["POST"])
def add_slot():
    data = json.loads(request.data.decode())
    detector.add_slot(data)
    return jsonify(success=True)


@app.route('/slot', methods=["DELETE"])
def delete_slot():
    data = json.loads(request.data.decode())
    detector.delete_slot(data)
    return jsonify(success=True)


@app.route('/feed')
def video_feed():
    return Response(detector.detect_motion(), mimetype='multipart/x-mixed-replace; boundary=frame')


@detector.slot_handler
def test(count):
    print(f"Free slots {count}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        detector = MotionDetector(sys.argv[1])
    app.run(host="0.0.0.0")


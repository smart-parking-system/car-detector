from flask import Flask, render_template, Response, request, jsonify
import json
from parking.motion_detector import *

app = Flask(__name__, static_url_path='/static')

# detector = MotionDetector('https://frn.rtsp.me/SAUNckeorr8y8CRuAwZspw/1636313331/hls/yssKD2RY.m3u8?ip=93.75.241.227')
detector = MotionDetector('videos/parking_lot_2.mp4')


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/corners', methods=["POST"])
def add_corners():
    data = json.loads(request.data.decode())
    detector.add_slot(data)
    return jsonify(success=True)


@app.route('/corners', methods=["DELETE"])
def delete_corners():
    data = json.loads(request.data.decode())
    detector.delete_slot(data)
    return jsonify(success=True)


@app.route('/video_feed')
def video_feed():
    return Response(detector.detect_motion(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run()

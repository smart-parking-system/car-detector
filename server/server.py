from flask import Flask, render_template, Response, request, jsonify
from typing import Final, List
import json

DEFAULT_URL: Final[str] = 'https://frn.rtsp.me/SAUNckeorr8y8CRuAwZspw/1636313331/hls/yssKD2RY.m3u8?ip=93.75.241.227'

class Server:
    def __init__(self, detector):
        self.detector = detector
        self.app = Flask('SPS', static_folder='server/static', template_folder='server/templates')

        @self.app.route('/')
        def index():
            return render_template('index.html')

        @self.app.route('/slot', methods=["POST"])
        def add_slot():
            data = json.loads(request.data.decode())
            detector.add_slot(data)
            return jsonify(success=True)

        @self.app.route('/slot', methods=["DELETE"])
        def delete_slot():
            data = json.loads(request.data.decode())
            detector.delete_slot(data)
            return jsonify(success=True)

        @self.app.route('/feed')
        def video_feed():
            return Response(detector.detect_motion(), mimetype='multipart/x-mixed-replace; boundary=frame')

        @self.detector.slot_handler
        def test(count):
            print(f"Free slots {count}")

    def run(self, args: List[str]):
        self.app.run(host=args['host'], port=args['port'])

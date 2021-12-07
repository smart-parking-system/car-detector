from .drawing_utils import draw_contours
from .colors import COLOR_GREEN, COLOR_WHITE, COLOR_BLUE
from typing import List, Tuple, Dict, Callable
import numpy as np
import threading
import time
import hashlib
import json
import cv2
import os

class MotionDetector:
    def __init__(self, video, laplacian: float = 1, detect_delay: float = 1):
        self.video = video
        self.coordinates_data = self.__load_points()
        self.contours = []
        self.bounds = []
        self.mask = []
        self.statuses = []
        self.laplacians = []
        self.times = []
        self.__width, self.__height = 0, 0
        self.laplacian = laplacian
        self.detect_delay = detect_delay

    def detect_motion(self):
        capture = cv2.VideoCapture(self.video)
        self.__width = capture.get(3)
        self.__height = capture.get(4)

        for point in self.coordinates_data:
            self.__add_slot(point)

        while capture.isOpened():
            result, frame = capture.read()
            if frame is None:
                break

            if not result:
                raise CaptureReadError(f"Error reading video capture on frame {str(frame)}")

            blurred = cv2.GaussianBlur(frame.copy(), (5, 5), 3)
            grayed = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            new_frame = frame.copy()

            position_in_seconds = capture.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            for index, c in enumerate(self.coordinates_data):
                status, l = self.__apply(grayed, index, c)
                if self.times[index] is not None and self.same_status(self.statuses, index, status):
                    self.times[index] = None
                    continue

                if self.times[index] is not None and self.status_changed(self.statuses, index, status):
                    if position_in_seconds - self.times[index] >= self.detect_delay:
                        self.statuses[index] = status
                        self.laplacians[index] = l
                        self.times[index] = None
                    continue

                if self.times[index] is None and self.status_changed(self.statuses, index, status):
                    self.times[index] = position_in_seconds

            for index, p in enumerate(self.coordinates_data):
                coordinates = self.__coordinates(p)
                color = COLOR_GREEN if self.statuses[index] else COLOR_BLUE
                draw_contours(new_frame, coordinates, str(round(self.laplacians[index], 2)), COLOR_WHITE, color)

            ret, buffer = cv2.imencode('.jpg', new_frame)
            new_frame = buffer.tobytes()
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + new_frame + b'\r\n')

    def __apply(self, grayed: List, index: int, p: Dict) -> Tuple:
        coordinates = self.__coordinates(p)
        rect = self.bounds[index]
        roi_gray = grayed[rect[1]:(rect[1] + rect[3]), rect[0]:(rect[0] + rect[2])]
        laplacian = cv2.Laplacian(roi_gray, cv2.CV_64F)
        coordinates[:, 0] = coordinates[:, 0] - rect[0]
        coordinates[:, 1] = coordinates[:, 1] - rect[1]
        l_result = np.mean(np.abs(laplacian * self.mask[index]))
        #l_result = np.mean(np.abs(np.dot(laplacian, self.mask[index])))
        status = l_result < self.laplacian
        return status, l_result

    @staticmethod
    def __coordinates(p: Dict):
        return np.array(p["coordinates"])

    @staticmethod
    def same_status(coordinates_status: List, index: int, status):
        return status == coordinates_status[index]

    @staticmethod
    def status_changed(coordinates_status: List, index: int, status):
        return status != coordinates_status[index]

    def __add_slot(self, point):
        self.statuses.append(False)
        self.times.append(None)
        self.laplacians.append(0.00)
        coordinates = self.__coordinates(point)
        rect = cv2.boundingRect(coordinates)
        new_coordinates = coordinates.copy()
        new_coordinates[:, 0] = coordinates[:, 0] - rect[0]
        new_coordinates[:, 1] = coordinates[:, 1] - rect[1]
        self.contours.append(coordinates)
        self.bounds.append(rect)
        mask = cv2.drawContours(
            np.zeros((rect[3], rect[2]), dtype=np.uint8),
            [new_coordinates],
            contourIdx=-1,
            color=255,
            thickness=-1,
            lineType=cv2.LINE_8)

        mask = mask == 255
        self.mask.append(mask)

    def add_slot(self, _point: Dict):
        point = {'id': len(self.coordinates_data), 'coordinates': []}
        for coordinate in _point:
            point['coordinates'].append([int(self.__width * coordinate['x']), int(self.__height * coordinate['y'])])
        self.coordinates_data.append(point)
        self.__add_slot(point)
        self.save()

    def delete_slot(self, _point: Dict):
        point = [int(self.__width * _point['x']), int(self.__height * _point['y'])]
        for i, coordinates in enumerate(self.coordinates_data):
            coordinates = coordinates['coordinates']
            if is_inside(*coordinates[0], *coordinates[1], *coordinates[2], *point) or \
                    is_inside(*coordinates[1], *coordinates[2], *coordinates[3], *point):
                del self.coordinates_data[i], self.contours[i], self.bounds[i], self.mask[i], self.statuses[i], \
                    self.laplacians[i], self.times[i]
                break
        self.save()

    def slot_handler(self, func: Callable):
        def init():
            count = len([i for i in self.statuses if i])
            while True:
                _count = len([i for i in self.statuses if i])
                if _count != count:
                    func(_count)
                    count = _count
                time.sleep(1)

        threading.Thread(target=init, daemon=True).start()

    def save(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        with open(f"data/{hashlib.md5(self.video.encode()).hexdigest()}.points", "w") as file:
            json.dump(self.coordinates_data, file)

    def __load_points(self) -> List:
        if os.path.exists(f"data/{hashlib.md5(self.video.encode()).hexdigest()}.points"):
            with open(f"data/{hashlib.md5(self.video.encode()).hexdigest()}.points", "r") as file:
                return json.loads(file.read())
        return []

class CaptureReadError(Exception):
    pass

def area(x1, y1, x2, y2, x3, y3):
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0)

def is_inside(x1, y1, x2, y2, x3, y3, x, y):
    a = [area(x1, y1, x2, y2, x3, y3),
         area(x, y, x2, y2, x3, y3),
         area(x1, y1, x, y, x3, y3),
         area(x1, y1, x2, y2, x, y)]
    return a[0] == a[1] + a[2] + a[3]


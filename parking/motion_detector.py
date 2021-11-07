import cv2 as open_cv
import numpy as np
from parking.drawing_utils import draw_contours
from parking.colors import COLOR_GREEN, COLOR_WHITE, COLOR_BLUE


class MotionDetector:
    LAPLACIAN = .9
    DETECT_DELAY = 1

    def __init__(self, video):
        self.video = video
        self.coordinates_data = []
        self.contours = []
        self.bounds = []
        self.mask = []
        self.statuses = []
        self.laplacian = []
        self.times = []
        self.__width, self.__height = 0, 0

    def detect_motion(self):
        capture = open_cv.VideoCapture(self.video)
        self.__width = capture.get(3)
        self.__height = capture.get(4)

        for point in self.coordinates_data:
            self.__add_slot(point)

        while capture.isOpened():
            result, frame = capture.read()
            if frame is None:
                break

            if not result:
                raise CaptureReadError("Error reading video capture on frame %s" % str(frame))

            blurred = open_cv.GaussianBlur(frame.copy(), (5, 5), 3)
            grayed = open_cv.cvtColor(blurred, open_cv.COLOR_BGR2GRAY)
            new_frame = frame.copy()

            position_in_seconds = capture.get(open_cv.CAP_PROP_POS_MSEC) / 1000.0
            for index, c in enumerate(self.coordinates_data):
                status, l = self.__apply(grayed, index, c)
                if self.times[index] is not None and self.same_status(self.statuses, index, status):
                    self.times[index] = None
                    continue

                if self.times[index] is not None and self.status_changed(self.statuses, index, status):
                    if position_in_seconds - self.times[index] >= MotionDetector.DETECT_DELAY:
                        self.statuses[index] = status
                        self.laplacian[index] = l
                        self.times[index] = None
                    continue

                if self.times[index] is None and self.status_changed(self.statuses, index, status):
                    self.times[index] = position_in_seconds
            for index, p in enumerate(self.coordinates_data):
                coordinates = self._coordinates(p)
                color = COLOR_GREEN if self.statuses[index] else COLOR_BLUE
                draw_contours(new_frame, coordinates, str(round(self.laplacian[index], 2)), COLOR_WHITE, color)

            ret, buffer = open_cv.imencode('.jpg', new_frame)
            new_frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + new_frame + b'\r\n')  #

    def __apply(self, grayed, index, p):
        coordinates = self._coordinates(p)

        rect = self.bounds[index]

        roi_gray = grayed[rect[1]:(rect[1] + rect[3]), rect[0]:(rect[0] + rect[2])]
        laplacian = open_cv.Laplacian(roi_gray, open_cv.CV_64F)

        coordinates[:, 0] = coordinates[:, 0] - rect[0]
        coordinates[:, 1] = coordinates[:, 1] - rect[1]
        l_result = np.mean(np.abs(laplacian * self.mask[index]))
        status = l_result < MotionDetector.LAPLACIAN
        return status, l_result

    @staticmethod
    def _coordinates(p):
        return np.array(p["coordinates"])

    @staticmethod
    def same_status(coordinates_status, index, status):
        return status == coordinates_status[index]

    @staticmethod
    def status_changed(coordinates_status, index, status):
        return status != coordinates_status[index]

    def __add_slot(self, point):
        self.statuses.append(False)
        self.times.append(None)
        self.laplacian.append(0.00)
        coordinates = self._coordinates(point)
        rect = open_cv.boundingRect(coordinates)
        new_coordinates = coordinates.copy()
        new_coordinates[:, 0] = coordinates[:, 0] - rect[0]
        new_coordinates[:, 1] = coordinates[:, 1] - rect[1]
        self.contours.append(coordinates)
        self.bounds.append(rect)
        mask = open_cv.drawContours(
            np.zeros((rect[3], rect[2]), dtype=np.uint8),
            [new_coordinates],
            contourIdx=-1,
            color=255,
            thickness=-1,
            lineType=open_cv.LINE_8)

        mask = mask == 255
        self.mask.append(mask)

    def add_slot(self, _point):
        point = {'id': len(self.coordinates_data), 'coordinates': []}
        for coordinate in _point:
            point['coordinates'].append([int(self.__width * coordinate['x']), int(self.__height * coordinate['y'])])
        self.coordinates_data.append(point)
        self.__add_slot(point)

    def delete_slot(self, _point):
        point = [int(self.__width * _point['x']), int(self.__height * _point['y'])]
        for i, coordinates in enumerate(self.coordinates_data):
            coordinates = coordinates['coordinates']
            if is_inside(*coordinates[0], *coordinates[1], *coordinates[2], *point) or \
                    is_inside(*coordinates[1], *coordinates[2], *coordinates[3], *point):
                del self.coordinates_data[i]
                del self.contours[i]
                del self.bounds[i]
                del self.mask[i]
                del self.statuses[i]
                del self.laplacian[i]
                del self.times[i]
                break


class CaptureReadError(Exception):
    pass


def area(x1, y1, x2, y2, x3, y3):
    return abs((x1 * (y2 - y3) + x2 * (y3 - y1)
                + x3 * (y1 - y2)) / 2.0)


def is_inside(x1, y1, x2, y2, x3, y3, x, y):
    a = area(x1, y1, x2, y2, x3, y3)
    a1 = area(x, y, x2, y2, x3, y3)
    a2 = area(x1, y1, x, y, x3, y3)
    a3 = area(x1, y1, x2, y2, x, y)
    if a == a1 + a2 + a3:
        return True
    else:
        return False

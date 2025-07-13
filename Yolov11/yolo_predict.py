from ultralytics import YOLO
import random
import cv2
import numpy as np
import os

#model = YOLO("/work/dev/osw-ai-server/yolo/runs/detect/train3_building/weights/best.pt")
base_dir = os.path.dirname(os.path.abspath(__file__))
weights_path = os.path.join(base_dir, "yolo", "runs", "detect", "train1", "weights", "best.pt")

model = YOLO(weights_path)


def box_coord_calculate(detect_boxs, envelope):
    min_x, min_y, max_x, max_y = envelope.bounds
    top_y = max_y
    bottom_y = min_y
    left_x = min_x
    right_x = max_x
    x_per_pixel = (right_x - left_x) / 640
    y_per_pixel = (top_y - bottom_y) / 640
    lines_wgs84 = []
    for box in detect_boxs:
        x1, y1 = box[0][0].item(), box[0][1].item()
        x2, y2 = box[1][0].item(), box[1][1].item()
        x1 = left_x + x1 * x_per_pixel
        y1 = top_y - y1 * y_per_pixel
        x2 = left_x + x2 * x_per_pixel
        y2 = top_y - y2 * y_per_pixel

        lines_wgs84.append([[y1, x1], [y2, x2]])

    return np.array(lines_wgs84)


def predict(image, epsg_4326_envelope):
    results = model.predict(image, conf=0.2)
    detect_boxs = []
    nscores = []
    for result in results:
        for box in result.boxes:
            if box.conf[0] > 0.2:
                detect_boxs.append([[box.xyxy[0][0], box.xyxy[0][1]], [box.xyxy[0][2], box.xyxy[0][3]]])
                nscores.append(box.conf[0].item())
    detect_boxs = box_coord_calculate(detect_boxs, envelope=epsg_4326_envelope)
    return np.array(nscores), detect_boxs

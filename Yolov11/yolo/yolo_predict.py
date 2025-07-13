from ultralytics import YOLO
import random
import cv2
import numpy as np
model = YOLO("/work/dev/osw-ai-server/yolo/runs/segment/train3/weights/best.pt")
img = cv2.imread("/work/dev/osw-ai-server/yolo/solar_panel/train/images/point_1026_jpg.rf.42c121b6c32293f0b32df4bce4378693.jpg")

# if you want all classes
yolo_classes = list(model.names.values())
print(yolo_classes)
conf = 0.2
results = model.predict(img, conf=conf)
colors = [random.choices(range(256), k=3) for _ in range(100)]
print(results)
for result in results:
    for mask, box in zip(result.masks.xy, result.boxes):
        points = np.int32([mask])
        color = random.choice(colors)
        
        # Fill the polygon with the random color
        cv2.fillPoly(img, points, color)
cv2.imwrite("test1112.jpg", img)

# yolo predict model=runs/detect/train5/weights/best.pt source=/work/dev/osw-ai-server/img/100.jpg
# yolo predict model=/work/dev/osw-ai-server/yolo/runs/segment/train2/weights/best.pt source=/work/dev/osw-ai-server/yolo/test.jpg
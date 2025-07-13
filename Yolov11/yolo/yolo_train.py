

from ultralytics import YOLO

# # Load a COCO-pretrained YOLOv8n model
# model = YOLO("yolo11n-seg.pt")

# # Train the model on the COCO8 example dataset for 100 epochs
# results = model.train(data="yolo.yaml", patience=0, epochs=500, imgsz=640,batch=8,hsv_h= 0.02 ,hsv_s= 0.7 , hsv_v= 0.4 , degrees= 90 , translate= 0.2 , scale= 0.5 , shear= 15 , flipud= 0.5 , fliplr= 0.5 , mosaic= 1.0 , mixup= 0.1 , copy_paste=0.3)
model = YOLO("yolo11n-seg.pt")
# Train the model on the COCO8 example dataset for 100 epochs
results = model.train(data="/work/dev/osw-ai-server/datasets/whu/yolo.yaml", epochs=500, imgsz=640, batch=16)
import os
import numpy as np
import cv2
from flask import Flask, request, jsonify, send_file 
from qwen_llm.inference import run_inference
from datetime import datetime
from io import BytesIO
from ultralytics import YOLO 
import logging

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)
# Set up logging to both file and console
log_filename = f"logs/server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode="a", encoding="utf-8"),
        logging.StreamHandler()  # Still print to console
    ]
)

print("[DEBUG] Starting service_controller.py")
logging.info("[DEBUG] Starting service_controller.py")

# Path to the YOLO model weights
base_dir = os.path.dirname(os.path.abspath(__file__))
weights_path = os.path.join(base_dir, "yolov11_llm", "yolo", "runs", "detect", "train1", "weights", "best.pt")
print(f"[DEBUG] YOLO weights path: {weights_path}")
logging.info(f"[DEBUG] YOLO weights path: {weights_path}")


try:
    model = YOLO(weights_path)
    print("[DEBUG] YOLO model loaded successfully")
    logging.info("[DEBUG] YOLO model loaded successfully")
except Exception as e:
    print(f"[ERROR] Failed to load YOLO model: {e}")
    logging.error(f"[ERROR] Failed to load YOLO model: {e}")
    raise

def process_image(image):
    print("[DEBUG] Entered process_image()")
    try:
        results = model.predict(image, conf=0.2)
        print("[DEBUG] YOLO model prediction complete")
        logging.info("[DEBUG] YOLO model prediction complete")
    except Exception as e:
        print(f"[ERROR] During YOLO prediction: {e}")
        logging.error(f"[ERROR] During YOLO prediction: {e}")
        raise

    nscores = []
    for result in results:
        for box in result.boxes:
            if box.conf[0] > 0.2:
                nscores.append(box.conf[0].item())
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

    detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    is_solar_panel_detected = len(nscores) > 0

    print(f"[DEBUG] Detection done. Count: {len(nscores)}")
    logging.info(f"[DEBUG] Detection done. Count: {len(nscores)}")

    return {
        "solar_panel_detected": is_solar_panel_detected,
        "confidence_scores": nscores,
        "timestamp": detection_time,
        "image": image
    }

app = Flask(__name__)
print("[DEBUG] Flask app initialized")
logging.info("[DEBUG] Flask app initialized")

@app.route('/predict', methods=['POST'])
def predict():
    print("[DEBUG] /predict endpoint hit")
    logging.info("[DEBUG] /predict endpoint hit")
    if request.is_json:
        print("[DEBUG] JSON request detected")
        logging.info("[DEBUG] JSON request detected")
        data = request.get_json()
        if not data or 'question' not in data:
            print("[ERROR] JSON missing 'question'")
            logging.error("[ERROR] JSON missing 'question'")
            return jsonify({"error": "Missing 'question' field in JSON"}), 400

        question = data['question']
        print(f"[DEBUG] Received question: {question}")
        logging.info(f"[DEBUG] Received question: {question}")
        try:
            answer = run_inference(question)
            print("[DEBUG] Inference complete")
            logging.info("[DEBUG] Inference complete")
            return jsonify({
                "type": "llm",
                "question": question,
                "answer": answer
            })
        except Exception as e:
            print(f"[ERROR] Inference failed: {e}")
            logging.error(f"[ERROR] Inference failed: {e}")
            return jsonify({"error": str(e)}), 500

    elif 'image' in request.files:
        print("[DEBUG] Image file received in request")
        logging.info("[DEBUG] Image file received in request")
        file = request.files['image']
        if file.filename == '':
            print("[ERROR] Empty filename in image upload")
            logging.error("[ERROR] Empty filename in image upload")
            return jsonify({"error": "No selected file"}), 400

        try:
            print("[DEBUG] Reading image...")
            logging.info("[DEBUG] Reading image...")
            in_memory_file = np.frombuffer(file.read(), np.uint8)
            img = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)
            print("[DEBUG] Image decoded")
            logging.info("[DEBUG] Image decoded")
            results = process_image(img)
            print("[DEBUG] Image processed")

            return jsonify({
                "type": "vision",
                "solar_panel_detected": results["solar_panel_detected"],
                "confidence_scores": results["confidence_scores"],
                "timestamp": results["timestamp"]
            })

        except Exception as e:
            print(f"[ERROR] Image processing failed: {e}")
            logging.error(f"[ERROR] Image processing failed: {e}")
            return jsonify({"error": str(e)}), 500

    else:
        print("[ERROR] Unsupported request format")
        logging.error("[ERROR] Unsupported request format")
        return jsonify({"error": "Unsupported request format. Use JSON for LLM or image for YOLO"}), 400

@app.route('/image', methods=['POST'])
def download_annotated_image():
    print("[DEBUG] /image endpoint hit")
    logging.info("[DEBUG] /image endpoint hit")
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        print("[DEBUG] Reading image...")
        logging.info("[DEBUG] Reading image...")
        in_memory_file = np.frombuffer(file.read(), np.uint8)
        img = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)
        print("[DEBUG] Image decoded")
        logging.info("[DEBUG] Image decoded")
        results = process_image(img)
        print("[DEBUG] Image processed")
        logging.info("[DEBUG] Image processed")
        _, img_encoded = cv2.imencode('.jpg', results["image"])
        img_bytes = img_encoded.tobytes()
        image_stream = BytesIO(img_bytes)
        image_stream.seek(0)

        return send_file(
            image_stream,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='annotated_result.jpg'
        )

    except Exception as e:
        print(f"[ERROR] Image processing failed: {e}")
        logging.error(f"[ERROR] Image processing failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("[DEBUG] Starting Flask server on 0.0.0.0:5000")
    logging.info("[DEBUG] Starting Flask server on 0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000)

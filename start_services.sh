#!/bin/bash


# If no argument is provided, show helpful usage
if [[ -z "$1" ]]; then
    echo "🧠 No command provided. The container is ready."
    echo "I guess you ran: docker run -p 5000:5000 -v /host/weights:/app/qwen_llm/qwen3_lora_merged my-ai-container"
    echo "You can run: docker run -it <container_id_or_name> dispatch"
    exit 0
fi

if [[ "$1" == "llm" ]]; then
    cmd="${2,,}"  # convert to lowercase

    case "$cmd" in
        model_setup)
            echo "▶️ Running model_setup.py..."
            python3 /app/qwen_llm/model_setup.py
            ;;
        data_prep)
            echo "▶️ Running data_prep.py..."
            python3 /app/qwen_llm/data_prep.py
            ;;
        train)
            echo "▶️ Running train.py..."
            python3 /app/qwen_llm/train.py
            ;;
        inference)
            echo "▶️ Running inference.py..."
            python3 /app/qwen_llm/inference.py
            ;;
        *)
            echo "[ERROR] Unknown llm command: $cmd"
            echo "Usage: docker run <image> llm [model_setup | data_prep | train | inference]"
            exit 1
            ;;
    esac

elif [[ "$1" == "yolo" ]]; then
    echo "[INFO] Running YOLOv11 pipeline..."

    shift  # remove "yolo" from args
    gpu_id=""

    # Detect and extract optional --gpu=X flag
    if [[ "$1" == --gpu=* ]]; then
        gpu_id="${1#--gpu=}"  # extract just the number (e.g., 0, 1, 2)
        echo "[INFO] GPU mode enabled: CUDA_VISIBLE_DEVICES=$gpu_id"
        shift  # remove --gpu=... from arguments
    fi

    if [[ -n "$gpu_id" ]]; then
        CUDA_VISIBLE_DEVICES="$gpu_id" python3 /app/yolov11_llm/download_solarpanel.py "$@"
    else
        python3 /app/yolov11_llm/download_solarpanel.py "$@"
    fi

elif [[ "$1" == "download_solarpanel" ]]; then
    echo "[INFO] Running download_solarpanel.py with the provided arguments..."
    
    shift  # remove "download_solarpanel" from args
    python3 /app/yolov11_llm/download_solarpanel.py "$@"

elif [[ "$1" == "dispatch" ]]; then
    echo "[INFO] Starting unified service_controller.py (Qwen + YOLO API)..."
    python3 /app/service_controller.py

else
    echo "[ERROR] Unknown command: $1"
    echo "Usage: docker run <image> {yolo | download_solarpanel | dispatch | mount_info}"
    exit 1
fi


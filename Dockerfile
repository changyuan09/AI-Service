# ----------------------------------------
# Base image with CUDA 12.6 for GPU inference
# ----------------------------------------
FROM nvidia/cuda:12.6.0-runtime-ubuntu22.04

# ----------------------------------------
# Step 0: Avoid tzdata prompt
# ----------------------------------------
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# ----------------------------------------
# Step 1: Install core system packages
# Use Python 3.10 and upgrade pip cleanly
# ----------------------------------------
RUN apt-get update && apt-get install -y \
    tzdata \
    python3.10 \
    python3.10-dev \
    python3-pip \
    curl \
    git \
    wget \
    build-essential \
    && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
    && python3 -m pip install --upgrade pip==25.0.1 \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata

# ----------------------------------------
# Step 2: Install latest geospatial libraries
# ----------------------------------------
RUN apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    libpq-dev \
    libgl1

# ----------------------------------------
# GDAL includes for rasterio and pyproj
# ----------------------------------------
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# ----------------------------------------
# Step 3: Set working directory
# ----------------------------------------
WORKDIR /app

# ----------------------------------------
# Step 4: Install Python dependencies
# ----------------------------------------
# RUN pip install --default-timeout=100 -r /app/requirements_llm.txt && \
#     pip install --default-timeout=100 -r /app/requirements_yolo.txt
COPY requirements.txt /app/requirements.txt
RUN pip install --default-timeout=100 -r /app/requirements.txt

# ----------------------------------------
# Step 5: Copy project files
# ----------------------------------------
COPY Qwen3.0/ /app/qwen_llm/
COPY Yolov11/ /app/yolov11_llm/
COPY start_services.sh /app/start_services.sh
COPY service_controller.py  /app/service_controller.py

# ----------------------------------------
# Step 6: Make entry script executable
# ----------------------------------------
RUN chmod +x /app/start_services.sh
RUN mkdir -p /app/logs && chmod -R 777 /app/logs
COPY Configs/Config_qwen.yaml /app/Configs/Config_qwen.yaml
# ----------------------------------------
# Step 7: Set entrypoint
# ----------------------------------------
ENTRYPOINT ["/app/start_services.sh"]
    
    

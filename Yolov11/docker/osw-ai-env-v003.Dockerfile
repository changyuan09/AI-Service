FROM ubuntu-dev-base:v0.2.0

ARG nproc
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /work

COPY ./lib/* /work


ENV ANACONDA_DIR=/root/anaconda3
RUN apt update &&\
    # 1.install anaconda
    cd /tmp && wget -c -P /tmp https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh  && bash Anaconda3-2024.10-1-Linux-x86_64.sh -b && \
    ${ANACONDA_DIR}/bin/conda create -n pytorch python=3.10 -y &&  \
    # 2.install pytorch
    # 12.6
    ${ANACONDA_DIR}/envs/pytorch/bin/pip3 install torch torchvision torchaudio  && \ 
    # 3.install cuda toolkit
    wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.1-1_all.deb &&  dpkg -i cuda-keyring_1.1-1_all.deb && apt-get update &&  apt-get -y install cuda-toolkit-12-6 && \
    # 0.install third-party lib
    apt-get -y install libpq-dev postgresql-client &&\
    ${ANACONDA_DIR}/envs/pytorch/bin/pip3 install pycocotools opencv-python lxml tqdm  matplotlib scipy tensorboard && \
    # time
    cp /work/Shanghai /etc/localtime && \
    # clean
    apt-get clean && rm -rf /work/* /var/lib/apt/lists/* /tmp/* /var/tmp/*
ENV PATH=${ANACONDA_DIR}/envs/pytorch/bin:${ANACONDA_DIR}/bin:$PATH

# @todo
# pip install geopandas shapely pyproj mercantile pillow rasterio requests
# conda install libffi==3.3
# pip install psycopg2 sqlalchemy geoalchemy2 

# docker build -t oyoyogg/osw-ai-env:tag --build-arg nproc=8 -f ./osw-ai-env.Dockerfile .

# oyoyogg/osw-ai-env:v0.0.1
# oyoyogg/osw-ai-env:v0.0.2 
    # version:
        # python: 3.9
        # pytorch: 2.7.0 by  cuda11.8
# oyoyogg/osw-ai-env:v0.0.3
    # version:
        # python: 3.10.0
        # pytorch: 2.7.0 by cuda12.6

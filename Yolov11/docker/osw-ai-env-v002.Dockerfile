FROM ubuntu-dev-base:v0.2.0

ARG nproc
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /work

COPY ./lib/* /work

# ENV ANT_HOME=/usr/share/ant
# ENV PATH=$PATH:$ANT_HOME/bin
# ENV LD_LIBRARY_PATH=/usr/lib64
ENV ANACONDA_DIR=/root/anaconda3
RUN apt update &&\
    # 0.install third-party lib
    # 1.install anaconda
    cd /tmp && wget -c -P /tmp https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh  && bash Anaconda3-2024.10-1-Linux-x86_64.sh -b && \
    ${ANACONDA_DIR}/bin/conda create -n pytorch python=3.9 -y &&  \
    # 2.install pytorch
    # 12.6
    ${ANACONDA_DIR}/envs/pytorch/bin/pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 && \ 
    # 12.4
    # ${ANACONDA_DIR}/envs/pytorch/bin/pip3 install torch torchvision torchaudio  && \  
    # ${ANACONDA_DIR}/bin/conda install nb_conda -y && \ #jupyter notebook
    ${ANACONDA_DIR}/envs/pytorch/bin/pip3 install pycocotools opencv-python lxml tqdm  matplotlib scipy tensorboard && \
    # time
    cp /work/Shanghai /etc/localtime && \
    # clean
    apt-get clean && rm -rf /work/* /var/lib/apt/lists/* /tmp/* /var/tmp/*
# @todo
# pip install geopandas shapely pyproj mercantile pillow rasterio requests
# apt-get install libpq-dev postgresql-client  
# conda install libffi==3.3
# pip install psycopg2 sqlalchemy geoalchemy2 shapely
# install cuda toolkit

ENV PATH=${ANACONDA_DIR}/envs/pytorch/bin:${ANACONDA_DIR}/bin:$PATH


# docker build -t oyoyogg/osw-ai-env:tag --build-arg nproc=8 -f ./osw-ai-env.Dockerfile .

# oyoyogg/osw-ai-env:v0.0.1
# oyoyogg/osw-ai-env:v0.0.2
# oyoyogg/osw-ai-env:v0.0.21 for 12.4

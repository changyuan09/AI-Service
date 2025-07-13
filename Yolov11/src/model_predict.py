import os
from pathlib import Path
from arcgis.learn import prepare_data, MaskRCNN, Model
import skimage.draw
import skimage.io
import matplotlib.pyplot as plt


class MaskCNNModel:
    """maskcnn类"""

    def __init__(self, modelPath, dataPath):
        self.modelPath = modelPath
        data_path = Path(dataPath)
        data = prepare_data(data_path, batch_size=4, imagery_type="ms", pin_memory=True)
        # modelTmp = Model()# @todo
        modelTmp = MaskRCNN(data)
        self.model = modelTmp.from_model(modelPath)

    def predict(self, imagePath, threshold=0.9, visualize=False, batch_size=4):
        return self.model.predict(imagePath, threshold, visualize, batch_size)

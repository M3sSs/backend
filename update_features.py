# backend/update_features.py
import os
import numpy as np
from PIL import Image
from pymongo import MongoClient
from tqdm import tqdm

def extract_features(image_path):
    try:
        img = Image.open(image_path).convert('RGB')
        img = img.resize((64, 64))
        return np.array(img).flatten().astype(float).tolist()
    except:
        return None

client = MongoClient("mongodb://localhost:27017/")
db = client["image_gallery"]
collection = db["images"]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

for image in tqdm(collection.find()):
    path = os.path.join(BASE_DIR, image["file_path"])
    features = extract_features(path)
    if features:
        collection.update_one({"_id": image["_id"]}, {"$set": {"features": features}})

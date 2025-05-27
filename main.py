import os
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pymongo import MongoClient
from typing import List
import shutil
from pathlib import Path
from fastapi import Form
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from PIL import Image
# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_FOLDER = os.path.join(BASE_DIR, 'downloaded_images')

# Ensure the 'downloaded_images' folder exists
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# FastAPI app initialization
app = FastAPI()

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["image_gallery"]
collection = db["images"]

# Function to generate a unique ID
def generate_unique_id():
    return str(uuid.uuid4())

# Endpoint to upload an image
@app.post("/upload_image/")
async def upload_image(file: UploadFile = File(...), category: str = Form(...)):
    # Generate a unique ID
    unique_id = generate_unique_id()
    
    # Construct the file path where the image will be stored
    file_path = f"downloaded_images/{file.filename}"
    full_file_path = os.path.join(DOWNLOAD_FOLDER, file.filename)

    # Save the uploaded image to the local file system
    with open(full_file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Store image metadata in MongoDB
    image_data = {
        "_id": unique_id,
        "file_path": file_path,
        "category": category
    }
    collection.insert_one(image_data)

    return {"message": "Image uploaded successfully", "unique_id": unique_id}

# Endpoint to list all images in the gallery
@app.get("/images/", response_model=List[dict])
def list_all_images():
    images = []
    for image in collection.find():
        images.append({
            "id": str(image["_id"]),
            "file_path": image["file_path"],
            "category": image["category"]
        })
    return images

#Endpoint for listing 100 random images
@app.get("/list_random_images/")
async def list_random_images():
    try:
        # Sample 100 random documents
        random_images_cursor = collection.aggregate([{"$sample": {"size": 100}}])
        images = []
        for image in random_images_cursor:
            image_data = {
                "unique_id": image.get("_id"),
                "category": image.get("category", "Unknown"),
                "file_path": image.get("file_path", "Not Available")
            }
            images.append(image_data)
        return images
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching random images: {str(e)}")

# Endpoint to search images by category
@app.get("/search_images_by_category/{category}")
async def search_images_by_category(category: str):
    images = []
    for image in collection.find({"category": category}):
        image_data = {
            "unique_id": image["_id"],
            "category": image["category"],
            "file_path": image["file_path"]
        }
        images.append(image_data)
    return images

# Endpoint to get image by unique ID
@app.get("/get_image/{image_id}")
async def get_image(image_id: str):
    image = collection.find_one({"_id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Retrieve the file path of the image from the database
    image_path = os.path.join(BASE_DIR, image["file_path"])

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found on server")
    
    return FileResponse(image_path)

# Endpoint to preview image by unique ID (thumbnail or full size preview)
@app.get("/preview_image/{image_id}")
async def preview_image(image_id: str):
    image = collection.find_one({"_id": image_id})
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Retrieve the file path of the image from the database
    image_path = os.path.join(BASE_DIR, image["file_path"])

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found on server")
    
    return FileResponse(image_path, headers={"Content-Type": "image/jpeg"})

@app.post("/search_similar_images/")
async def search_similar_images(file: UploadFile = File(...), top_k: int = 10):
    # Read and extract features from the uploaded image
    try:
        img = Image.open(file.file).convert("RGB").resize((64, 64))
        input_vector = np.array(img).flatten().astype(float).reshape(1, -1)
    except:
        raise HTTPException(status_code=400, detail="Invalid image uploaded.")

    # Fetch all image features from DB
    image_data = list(collection.find({"features": {"$exists": True}}))
    if not image_data:
        raise HTTPException(status_code=500, detail="No feature data available in DB.")

    features_list = [doc["features"] for doc in image_data]
    feature_matrix = np.array(features_list)

    # Compute cosine similarity
    similarities = cosine_similarity(input_vector, feature_matrix)[0]
    
    # Get top K indices
    top_indices = similarities.argsort()[-top_k:][::-1]
    
    similar_images = []
    for idx in top_indices:
        doc = image_data[idx]
        similar_images.append({
            "unique_id": doc["_id"],
            "category": doc.get("category", "Unknown"),
            "file_path": doc["file_path"],
            "similarity": float(similarities[idx])
        })

    return similar_images
# Add more routes as necessary (e.g., deleting images, etc.)

# Running FastAPI:
# If you're using `uvicorn`, run the server using the following:
# uvicorn main:app --reload

from fastapi import APIRouter, UploadFile, File
import zipfile
import os
import csv
from pathlib import Path
import re
from fastapi.responses import FileResponse
import shutil

router = APIRouter()

PROCESSED_DIR = "processed"
DOWNLOAD_URL = "https://hbapi.leeseaver.com/processed"  # Replace with your base URL

# Helper function to generate a slug from a filename
def generate_slug(filename: str) -> str:
    slug = Path(filename).stem.replace("_", " ").replace(" ", "-").lower()
    slug = re.sub(r'[^a-z0-9\-]', '', slug)
    return slug

# Helper function to generate alt text from a filename
def generate_alt_text(filename: str) -> str:
    alt_text = Path(filename).stem.replace("_", " ")
    return alt_text.title()

# Overwrite directory if it exists by deleting and recreating it
def ensure_clean_directory(path: Path):
    if path.exists():
        shutil.rmtree(path)  # Delete the directory and its contents
    path.mkdir(parents=True, exist_ok=True)

# Route to handle zip file upload and process contents
@router.post("/upload-zip")
async def upload_zip(file: UploadFile = File(...)):
    processed_dir = Path(PROCESSED_DIR)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    zip_path = processed_dir / file.filename
    with open(zip_path, "wb") as buffer:
        buffer.write(await file.read())

    # Extract ZIP file into the processed directory
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(processed_dir)

    os.remove(zip_path)  # Remove the original ZIP file after extraction

    main_folder_name = None
    folder_file_data = []

    # Walk through the processed directory and clean file/folder names
    for root, dirs, files in os.walk(processed_dir):
        if main_folder_name is None and dirs:
            original_folder_name = dirs[0]
            cleaned_folder_name = original_folder_name.replace(" ", "_")
            main_folder_name = cleaned_folder_name

            # Ensure the directory is clean (overwrite if it exists)
            folder_path = Path(root) / cleaned_folder_name
            ensure_clean_directory(folder_path)

        original_folder_name = Path(root).name
        cleaned_folder_name = original_folder_name.replace(" ", "_")

        # Rename the folder if necessary and overwrite if exists
        if original_folder_name != cleaned_folder_name:
            cleaned_folder_path = Path(root).parent / cleaned_folder_name
            if Path(cleaned_folder_path).exists():
                shutil.rmtree(cleaned_folder_path)  # Remove existing folder
            os.rename(root, cleaned_folder_path)
            root = str(cleaned_folder_path)

        for file_name in files:
            if file_name.endswith(".csv"):
                continue

            original_file_name = file_name
            cleaned_file_name = original_file_name.replace(" ", "_")

            # Overwrite the file if it already exists
            cleaned_file_path = os.path.join(root, cleaned_file_name)
            if original_file_name != cleaned_file_name and os.path.exists(cleaned_file_path):
                os.remove(cleaned_file_path)  # Remove existing file with the cleaned name

            if original_file_name != cleaned_file_name:
                os.rename(os.path.join(root, original_file_name), cleaned_file_path)

            slug = generate_slug(cleaned_file_name)
            alt_text = generate_alt_text(cleaned_file_name)

            folder_file_data.append({
                "original_folder_name": original_folder_name,
                "cleaned_folder_name": cleaned_folder_name,
                "original_file_name": original_file_name,
                "cleaned_file_name": cleaned_file_name,
                "relative_root": root,
                "slug": slug,
                "alt_text": alt_text
            })

    if main_folder_name is None:
        main_folder_name = file.filename.replace(".zip", "").replace(" ", "_")

    # Prepare the CSV file
    csv_file_path = processed_dir / f"{main_folder_name}_webflow.csv"
    with open(csv_file_path, mode="w", newline="") as csv_file:
        fieldnames = [
            "original_folder_name", "cleaned_folder_name", 
            "original_file_name", "cleaned_file_name", 
            "slug", "alt_text", "download_link"
        ]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for data in folder_file_data:
            relative_path = os.path.relpath(os.path.join(data["relative_root"], data["cleaned_file_name"]), PROCESSED_DIR)
            download_link = f"{DOWNLOAD_URL}/{relative_path}"

            writer.writerow({
                "original_folder_name": data["original_folder_name"],
                "cleaned_folder_name": data["cleaned_folder_name"],
                "original_file_name": data["original_file_name"],
                "cleaned_file_name": data["cleaned_file_name"],
                "slug": data["slug"],
                "alt_text": data["alt_text"],
                "download_link": download_link
            })

    # Return the CSV file as a downloadable response
    return FileResponse(csv_file_path, media_type='text/csv', filename=f"{main_folder_name}_webflow.csv")

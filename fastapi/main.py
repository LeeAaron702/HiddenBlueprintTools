from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from WebflowCSV import router as webflow_router
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
PROCESSED_DIR = "processed"

# Ensure the processed directory exists before the app is mounted
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

# Mount the static files directory
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

# Include the Webflow router
app.include_router(webflow_router)

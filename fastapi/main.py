from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from WebflowCSV import router as webflow_router
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://192.168.0.243:3000",
    "http://192.168.0.175:3000",
    "https://hbtools.leeseaver.com",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],

)
PROCESSED_DIR = "processed"

# Ensure the processed directory exists before the app is mounted
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

# Mount the static files directory
app.mount("/processed", StaticFiles(directory=PROCESSED_DIR), name="processed")

# Include the Webflow router
app.include_router(webflow_router)

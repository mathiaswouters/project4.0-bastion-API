from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import boto3
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
AWS_REGION = os.environ.get("AWS_REGION")
BUCKET_NAME = os.environ.get("BUCKET_NAME")
DATABASE_URL = os.environ.get("DATABASE_URL")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION,
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class PhotoInfo:
    pass


@app.post("/uploadfile/")
async def create_upload_file(
    file: UploadFile = File(...),
    location: str = Form(...),
    timestamp: datetime = Form(...),
):
    try:
        # Save the file temporarily or process it as needed
        secure_filename = file.filename.replace(" ", "_")

        # Upload the file to S3
        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            secure_filename,
        )

        # Generate the S3 URL
        s3_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{secure_filename}"

        # Save data to RDS
        db = SessionLocal()

        # Use the data model without the table definition
        photo_info = PhotoInfo()
        photo_info.timestamp = timestamp
        photo_info.location = location
        photo_info.s3_url = s3_url
        db.add(photo_info)
        db.commit()
        db.refresh(photo_info)

        return JSONResponse(
            content={
                "message": "File uploaded successfully",
                "s3_url": s3_url,
                "timestamp": timestamp,
                "location": location,
            },
            status_code=200,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

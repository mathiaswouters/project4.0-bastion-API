from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Security, status, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from sqlalchemy import create_engine, Column, Integer, String, DateTime, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import boto3
import os
import ssl
from botocore.exceptions import NoCredentialsError

app = FastAPI()

# CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

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

secrets_manager = boto3.client("secretsmanager")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class PhotoInfo:
    pass

# Load SSL context with your certificate and private key
ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
ssl_context.load_cert_chain('cert.pem', keyfile='key.pem')

# Function to get the API key from Secrets Manager
def get_api_key() -> str:
    try:
        secret_name = "bastion_api_key"
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        secret_string = response["SecretString"]
        return secret_string
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve API key from Secrets Manager. Check your AWS credentials.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving API key: {str(e)}",
        )

# Function to get the password from Secrets Manager
def get_password() -> str:
    try:
        secret_name = "bastion_api_password"
        response = secrets_manager.get_secret_value(SecretId=secret_name)
        secret_string = response["SecretString"]
        return secret_string
    except NoCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve password from Secrets Manager. Check your AWS credentials.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving password: {str(e)}",
        )

# Dependency to get the password
def get_password_dependency(password: str = Depends(get_password)):
    return password

# GET request to get the API key
@app.get("/apikey")
def get_api_key_route(password: str = Depends(get_password_dependency)):
    api_key = get_api_key()
    return {"api_key": api_key}

# Test API Key
@app.get("/protected")
def protected_route(api_key: str = Security(get_api_key)):
    return {"message": "Access granted!"}

# POST request
@app.post("/uploadfile/")
async def create_upload_file(
    file: UploadFile = File(...),
    location: str = Form(...),
    timestamp: datetime = Form(...),
    api_key: str = Security(get_api_key)
):
    try:
        secure_filename = file.filename.replace(" ", "_")

        s3_client.upload_fileobj(
            file.file,
            BUCKET_NAME,
            secure_filename,
        )

        s3_url = f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{secure_filename}"

        db = SessionLocal()

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


# Include ssl_context in the app creation
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile="key.pem", ssl_certfile="cert.pem", ssl_version=ssl.PROTOCOL_TLS)
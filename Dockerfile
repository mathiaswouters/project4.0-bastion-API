FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

ENV AWS_ACCESS_KEY="your_access_key"
ENV AWS_SECRET_KEY="your_secret_key"
ENV AWS_REGION="your_s3_region"
ENV BUCKET_NAME="your_bucket_name"
ENV DATABASE_URL="postgresql://user:password@host:port/dbname"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]

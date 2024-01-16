## Virtual Environment
### MacOS or Linux

1. `python3 -m venv venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`

### Windows - recommendation to use git-bash terminal

1. `py -3 -m venv venv`
2. `source venv/Scripts/activate`
3. `pip install -r requirements.txt`


## Docker
### Build and Run docker image
1. docker build -t your-image-name .
2. docker run -p 8080:80 -e AWS_ACCESS_KEY -e AWS_SECRET_KEY -e AWS_REGION -e BUCKET_NAME -e DATABASE_URL your-image-name

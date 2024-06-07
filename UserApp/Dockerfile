# base image
FROM python:3.9-slim

# set working dir
WORKDIR /app

# copy package 
COPY . /app

# install dependencies
RUN pip install -r requirements.txt

# expose port
EXPOSE 5006

# run app
CMD ["python", "userapp.py"]
FROM python:3.10-bullseye

WORKDIR /usr/src/app

COPY . .

RUN pip3 install pydantic==1.9.0 requests==2.27.1 pymongo==4.1.0 imageio==2.13.3 Pillow==8.4.0

CMD ["python3", "run.py"]

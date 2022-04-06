FROM python:3.10-alpine

WORKDIR /usr/src/app

COPY . .

RUN pip3 install requests==2.27.1 imageio==2.13.3 Pillow==8.4.0

CMD ["python3", "run.py"]
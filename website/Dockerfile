FROM python:3.10-alpine

WORKDIR /usr/src/app

COPY . .

RUN pip3 install Flask==2.1.0 gunicorn==20.1.0 python-dateutil==2.8.2 requests==2.27.1

CMD ["sh", "run.sh"]

FROM python:3.10-alpine

WORKDIR /usr/src/app

COPY . .

RUN pip3 install pydantic==1.9.0 requests==2.27.1 fastapi==0.75.1 pymongo==4.1.0 uvicorn==0.17.6

CMD python3 -m uvicorn app:app --port 8000 --host 0.0.0.0

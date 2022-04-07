from datetime import tzinfo
from flask import render_template
from gxrvprw import app
import requests
from datetime import datetime
from dateutil import parser as dateparser


@app.route("/")
@app.route("/index.html")
def main_root():
    response = requests.get(
        url="http://api:8000/timelapse/latest",
        params={
            "interval_time": "60",
        },
    ).json()
    tl_url_1 = response["result"]["timelapse"]["downloadURLs"]["h264"]
    tl_time_1 = dateparser.parse(response["result"]["timelapse"]["date"]).strftime("%Y/%m/%d %H:%M:%S")
    response = requests.get(
        url="http://127.0.0.1:8000/timelapse/latest",
        params={
            "interval_time": "15",
        },
    ).json()
    tl_url_2 = response["result"]["timelapse"]["downloadURLs"]["h264"]
    tl_time_2 = dateparser.parse(response["result"]["timelapse"]["date"]).strftime("%Y/%m/%d %H:%M:%S")
    currentTime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    return render_template("index.html", tl_url_1=tl_url_1, tl_time_1=tl_time_1, tl_url_2=tl_url_2, tl_time_2=tl_time_2, currentTime=currentTime)

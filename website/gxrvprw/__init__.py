from flask import Flask
import logging

app = Flask("web-geoxorplacevapronvapw", template_folder="gxrvprw/templates")

from gxrvprw import views

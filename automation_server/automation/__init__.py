from flask import Blueprint

automation = Blueprint('automation', __name__)

from .views import *
from .api import *
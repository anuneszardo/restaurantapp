# Conteudo do arquivo `wsgi.py`
#
import sys

sys.path.insert(0, "/home/ubuntu/flaskapp/restaurantapp")

from restaurantapp import app as application

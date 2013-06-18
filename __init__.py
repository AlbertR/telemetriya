# -*- coding: utf-8 -*-

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask_mail import Mail

app = Flask(__name__, static_folder='static',
	    template_folder='templates')

app.config.from_pyfile('../config.py')

app.config['SECURITY_LOGIN_URL']='/log'
app.config['LOGIN_URL']='/log'
app.config['SECURITY_LOGIN_USER_TEMPLATE']='login.html'
db = SQLAlchemy(app)

mail = Mail(app)

import views
#from views import resources

# -*- coding: utf-8 -*-

from flask import session, request, redirect
from flask.ext.security import current_user
from functools import wraps

def login_required(fn):

    @wraps(fn)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated():
            try:
                if request.environ['PATH_INFO']: # or request.environ['HTTP_REFERER']:
                    session['referer'] = str(request.environ['PATH_INFO'])
            except:
                session['referer'] = ''
            return redirect("/login")
        return fn(*args, **kwargs)
    return decorated_view

def role_required(fn):

    @wraps(fn)
    def decorated_view(*args, **kwargs):
        print "current_user.is_roled"

        return fn(*args, **kwargs)
    return decorated_view

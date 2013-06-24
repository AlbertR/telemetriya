# -*- coding: utf-8 -*-

from flask import g
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, UserMixin, RoleMixin
from telemetriya import app, db
from datetime import datetime


roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    user_tag = db.Column(db.Unicode(255), nullable=True, unique=False, default=u'')
    user_phone = db.Column(db.Unicode(255), nullable=False, unique=True, default=u'')
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    user_info = db.Column(db.Integer, db.ForeignKey('user_info.id'))
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def json_dump(self):
        return dict(id=self.id, email=self.email, password=self.password, user_tag=self.user_tag, user_phone=self.user_phone, active=self.active, confirmed_at=self.confirmed_at, user_info=self.user_info)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

class Status(db.Model):
    '''
        из шаблона admin_02_01_01_user_edit
        поле - Состояние
    '''
    __tablename__ = 'status'

    id = db.Column(db.Integer, db.Sequence('status_id', optional=True), primary_key=True)
    value = db.Column(db.Unicode(255), nullable=False, unique=True, default=u'')
    #userinfo = db.relationship('UserInfo', backref='status', lazy='dynamic')

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '<value: %s>' % (self.value)

class UserInfo(db.Model):

    __tablename__ = 'user_info'

    __table_args__ = {
        'mysql_charset':'utf8'
    }

    id = db.Column(db.Integer, db.Sequence('user_id', optional=True), primary_key=True)
    #user = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', uselist=False, backref='users_info', cascade_backrefs=True)
    user_lname = db.Column(db.Unicode(255), nullable=False, unique=False, default=u'')
    user_fname = db.Column(db.Unicode(255), nullable=False, unique=False, default=u'')
    user_patronymic = db.Column(db.Unicode(255), nullable=True, unique=False, default=u'')
    user_nickname = db.Column(db.Unicode(255), nullable=True, unique=True, default=u'')
    #user_status = db.Column(db.Integer, db.ForeignKey('status.id'))
    #user_status = db.Column(db.Integer)
    user_status = db.Column(db.Integer, db.ForeignKey('status.id'))
    user_why = db.Column(db.Unicode(255), nullable=True, unique=False, default=u'')
    #user_right = db.Column(db.Integer)
    mysql_charset='utf-8'

    def __init__ (self, user, user_lname, user_fname, user_patronymic, user_nickname, user_status, user_why):
        self.user = user
        self.user_lname = user_lname
        self.user_fname = user_fname
        self.user_patronymic = user_patronymic
        self.user_nickname = user_nickname
        self.user_status = user_status
        self.user_why = user_why
        #self.user_right = user_right

    def json_dump(self):
        return dict(id=self.id, user=self.user, user_lname=self.user_lname, user_fname=self.user_fname, user_patronymic=self.user_patronymic, user_nickname=self.user_nickname, user_status=self.user_status, user_why=self.user_why)

    def __repr__ (self):
        return '<user: %s, user_lname: %s, user_fname: %s, user_patronymic: %s, user_nickname: %s, user_status: %s, user_why: %s>' % (self.user, self.user_lname, self.user_fname, self.user_patronymic, self.user_nickname, self.user_status, self.user_why)

class Label(db.Model):

    __tablename__ = 'label'
    __table_args__ = {
        'mysql_charset':'utf8'
    }

    id = db.Column(db.Integer, db.Sequence('label_id', optional=True), primary_key=True)
    label_id = db.Column(db.Integer, unique=True)
    user_id = db.Column(db.Integer)
    status = db.Column(db.Integer)

    def __init__ (self, label_id, user_id, status):
        self.label_id = label_id
        self.user_id = user_id
        self.status = status

    def json_dump(self):
        return dict(label_id=self.label_id, user_id=self.user_id, status=self.status)

    def __repr__(self):
        return '<label_id: %s, user_id: %s, status: %s>' % (self.label_id, self.user_id, self.status)

#class Rights(db.Model):
#
#    __tablename__ = 'rights'
#
#    def __init__(self):
#        pass
#
#    def __repr__(self):
#        pass
#
#
class Track(db.Model):

    __tablename__ = 'track'
    __table_args__ = {
        'mysql_charset':'utf8'
    }

    id = db.Column(db.Integer, db.Sequence('track_id', optional=True), primary_key=True)
    name = db.Column(db.Unicode(255), nullable=False, unique=False, default=u'')
    length = db.Column(db.Integer)
    address = db.Column(db.Unicode(255), nullable=True, unique=False, default=u'')
    gps = db.Column(db.Unicode(255), nullable=True, unique=False, default=u'')
    mintime = db.Column(db.Time, default=0)
    maxtime = db.Column(db.Time, default=0)
    active = db.Column(db.Boolean, default=False)

    def __init__(self, name, length, address, gps, mintime, maxtime, active):
        self.name = name
        self.length = length
        self.address = address
        self.gps = gps
        self.mintime = mintime
        self.maxtime = maxtime
        self.active = active

    def json_dump(self):
        return dict(name=self.name, length=self.length, address=self.address, gps=self.gps, mintime="%s" % self.mintime, maxtime="%s" % self.maxtime, active=self.active)

    def __repr__(self):
        return '<name: %s,\nlength: %s,\naddress: %s,\ngps: %s,\nmintime: %s,\nmaxtime: %s,\nactive: %s>' % (self.name, self.length, self.address, self.gps, self.mintime, self.maxtime, self.active)

class Training(db.Model):

    __trablename__ = 'training'
    __table_args__ = {
        'mysql_charset':'utf8'
    }

    id = db.Column(db.Integer, db.Sequence('training_id', optional=True), primary_key=True)
    temperature = db.Column(db.Integer)
    relative_humidity = db.Column(db.Integer)
    cloudiness = db.Column(db.Integer)
    precipitation = db.Column(db.Integer)
    tcoating = db.Column(db.Integer)
    ccoverage = db.Column(db.Integer)
    #track = db.Column(db.Integer)
    track = db.Column(db.Integer, db.ForeignKey('track.id'))
    date = db.Column(db.Date, default=datetime.now())
    start = db.Column(db.Time, default=datetime.now())
    stop = db.Column(db.Time, default=0)
    duration = db.Column(db.Time, default=0)
    session = db.Column(db.Integer)
    active = db.Column(db.Boolean)

    def __init__(self, temperature, relative_humidity, cloudiness, precipitation, tcoating, ccoverage, track, start, stop, duration, session, active):

        self.temperature = temperature
        self.relative_humidity = relative_humidity
        self.cloudiness = cloudiness
        self.precipitation = precipitation
        self.tcoating = tcoating
        self.ccoverage = ccoverage
        self.track = track
        self.start = start
        self.stop = stop
        self.duration = duration
        self.session = session
        self.active = active

    def json_dump(self):
        return dict(temperature=self.temperature, relative_humidity=self.relative_humidity, cloudiness=self.cloudiness, precipitation=self.precipitation, tcoating=self.tcoating, ccoverage=self.ccoverage, track=self.track, start=self.start, stop=self.stop, duration=self.duration, session=self.session, active=self.active)

    def __rept__(self):
       return '<temperature: %s, relative_humidity: %s, cloudiness: %s, precipitation: %s, tcoating: %s, ccoverage: %s, track: %s, start: %s, stop: %s, duration: %s, session: %s, active: %s>' % (self.temperature, self.relative_humidity, self.cloudiness, self.precipitation, self.tcoating, self.ccoverage, self.track, self.start, self.stop, self.duration, self.session, self.active)

class Statistics(db.Model):

    __tablename__ = "statistics"
    __table_args__ = {
        "mysql_charset":"utf8"
        }

    id = db.Column(db.Integer, db.Sequence('statistics_id', optional=True), primary_key=True)
    date = db.Column(db.DateTime, default = datetime.now())
    label_id = db.Column(db.Integer, default =0)
    user_id = db.Column(db.Integer, default =0)
    ringtime = db.Column(db.Float, default =0)
    track_id = db.Column(db.Integer)
    session = db.Column(db.Integer)

    def __init__ (self, date, label_id, user_id, ringtime, track_id, session):

        self.date = date
        self.label_id = label_id
        self.user_id = user_id
        self.ringtime = ringtime
        self.track_id = track_id
        self.session = session

    def __repr__(self):
       return '<date: %s, label_id: %s, user_id: %s, ringtime: %s, track_id: %s, sesssion: %s>' % (self.date, self.label_id, self.user_id, self.ringtime, self.track_id, self.session)

    def json_dump(self):
        return dict(date=self.date, label_id=self.label_id, user_id=self.user_id, ringtime=self.ringtime, track_id=self.track_id, session=self.session)

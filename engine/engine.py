#!/usr/bin/env python
# -*- coding: utf-8

from __future__ import with_statement
import sys

def check(requires):
    '''
        Checking whether all the module are installed
    '''
    import warnings
    import pkg_resources as pkgr

    #Checking to intall SQLAlchemy module
    try:
        pkgr.require(requires[0])
    except pkgr.DistributionNotFound:
        warnings.warn('Install SQLAlchemy')
        sys.exit(0)

    #Checkin to intall PySerial module
    try:
        pkgr.require(requires[1])
    except pkgr.DistributionNotFound:
        warnings.warn('Install PySerial')
        sys.exit(0)


check(['sqlalchemy', 'pyserial'])

import os
import re
import serial
from struct import *
from array import *
import datetime as dt
from struct import *
from sqlalchemy import orm, schema, types, create_engine
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Inspectable(object):

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, dict([(x,y) for (x,y) in self.__dict__.items() if not x.startswith('_')]))

def now():
    return dt.datetime.now()

def initdb(engine):

    #connection = engine.connect()

    #queries = ('CREATE DATABASE IF NOT EXISTS _telemetriya',
    #           'USE _telemetriya')
    #queries = ('USE _telemetriya')

    #map(connection.execute, queries)
    #connection.execute('CREATE DATABASE IF NOT EXISTS _telemetriya')
    #connection.execute('USE _telemetriya')

    class TUser(Inspectable, Base):
        __tablename__ = 'user'

        id = schema.Column(types.Integer, schema.Sequence('user_id', optional=True), primary_key=True)
        login = schema.Column(types.Unicode(255), nullable=False, unique=True, default=u'')
        password = schema.Column(types.String(255))
        user_tag = schema.Column(types.Unicode(255), nullable=True, unique=False, default=u'')
        user_phone = schema.Column(types.Unicode(255), nullable=False, unique=True, default=u'')
        active = schema.Column(types.Boolean())
        confirmed_at = schema.Column(types.DateTime())
        user_info = schema.Column(types.Integer, schema.ForeignKey('user_info.id'))
        # roles = relationship('Role', secondary=roles_users, backref=backref('users', lazy='dynamic'))

        def __init__(self, login, password, user_tag, user_phone, active, confirmed_at, user_info, roles):
            self.login = login
            self.password = password
            self.user_tag = user_tag
            self.user_phone = user_phone
            self.active = acitve
            self.confirmed_at = confirmed_at
            self.user_info = user_info
        #    self.roles = roles

    class TBase(Inspectable, Base):
        __tablename__ = 'statistics'
        __table_args__ = {
            "mysql_charset":"utf8"
        }

        id = schema.Column(types.Integer, schema.Sequence('statistics_id', optional=True), primary_key=True)
        date = schema.Column(types.DateTime(), default=now())
        label = schema.Column(types.Integer, default = 0)
        user_id = schema.Column(types.Integer, default = 0)
        ringtime = schema.Column(types.Time, default = 0)
        track_id = schema.Column(types.Integer)
        session = schema.Column(types.Integer)

        def __init__(self, date, label, user_id, ringtime, track_id, session):
            self.date = date
            self.label = label
            self.user_id = user_id
            self.ringtime = ringtime
            self.track_id = track_id
            self.session = session

    # class TLabel(Inspectable, Base):
    #     __tablename__ = 'labels'

    #     id = schema.Column(types.Integer, schema.Sequence('label_id', optional=True), primary_key=True)
    #     status = schema.Column(types.Unicode(255), nullable=True, default=u'')

    #     def __init__(self, status):
    #         self.status = status

    # class TLabelStatus(Inspectable, Base):
    #     __tablename__ = 'lstatus'

    #     id = schema.Column(types.INTEGER, schema.Sequence('lstatus_id', optional=True), primary_key=True)
    #     name = schema.Column(types.Unicode(255), nullable=False, default=u'')

    #     def __init__(self, name):
    #         self.name = name


    class TTrack(Inspectable, Base):
        __tablename__ = 'track'
        __table_args__ = {
            'mysql_charset':'utf8'
        }

        id = schema.Column(types.Integer, schema.Sequence('track_id', optional=True), primary_key=True)
        name = schema.Column(types.Unicode(255), nullable=False, unique=False, default=u'')
        lenght = schema.Column(types.Integer)
        address = schema.Column(types.Unicode(255),nullable=True, unique=False, default=u'')
        gps = schema.Column(types.Unicode(255), nullable=True, unique=False, default=u'')
        mintime = schema.Column(types.Time, default=0)
        maxtime = schema.Column(types.Time, default=0)
        active = schema.Column(types.Boolean, default=False)

        def __init__(self, name, lenght, address, gps, mintime, maxtime, active):
            self.name = name
            self.lenght = lenght
            self.address = address
            self.gps = gps
            self.mintime = mintime
            self.maxtime = maxtime
            self.active = active

    #Base.metadata.create_all(engine)

    return TUser, TBase, TTrack

def fillDB(engine, TBase, date, label, ringtime):

    Session = sessionmaker(bind=engine)
    session = Session()

    baseData = TBase(date, label, ringtime)
    session.add(baseData)
    session.commit()

def time2str(time):
    ftime = time/1000.0
    return '%.3f' % ftime

def get_data(engine, TBase, port, baudrate=115200, timeout=1):
    '''
    '''
    ser = serial.serial_for_url('COM12', baudrate=baudrate, timeout=timeout) # Open com port
    t1old = 0                   # Initialization
    t2old = 0                   # Initialization
    while 1:                    # While TRUE read a com port
        data = ser.read(14)     # Read 14 bytes
        if (data != '') and (data != []): # Check for data
            #print 'data: ',repr(data)
            try:
                # Unpack readed data
                c=unpack('>h',str(bytearray(data)[4:-8]))
                t0=unpack('>l',str(bytearray(data)[6:-4]))
                t1new=unpack('>h',str(bytearray(data)[10:-2]))
                t2new=unpack('>h',str(bytearray(data)[12:]))
            except:
                continue

            delta = int(t2new[0])-int(t1new[0])
            now = dt.datetime.now() # Current date and time
            print now.strftime('%Y-%m-%d %H:%M:%S'), 'dT1='+time2str(t1new[0]+t0[0]-t1old)+',', \
            'dT1='+time2str(t1new[0]+t0[0]-t1old)+',', 'Label='+str(c[0])+',', 'T0='+str(t0[0])+',', \
            'T1+='+str(t1new[0])+',', 'T2+='+str(t2new[0])+',', 'dlt='+str(delta)

            #send data to base
            fillDB(engine, TBase, now.strftime('%Y-%m-%d %H:%M:%S'), str(c[0]), time2str(t1new[0]+t0[0]-t1old)) # или t2new в зависимости от выбора. выбор дописать

            t1old = t1new[0]+t0[0] # Time1 on last lap
            t2old = t2new[0]+t0[0] # Time2 on last lap


    ser.close()                 # Close com port

def main():
    '''
    '''

    # Options to access the database
    #dbparam = 'mysql://root:ar1m2312@192.168.0.88:3306/_telemetriya?charset=utf8&use_unicode=1'
    #dbparam = 'mysql://root:1234@127.0.0.1:3306/_telemetriya?charset=utf8&use_unicode=1'
    dbparam = 'mysql://root:30v11aiR@178.132.203.168:3306/_telemetriya?charset=utf8&use_unicode=1'
    engine = create_engine(dbparam, echo=False)
    TUser, TBase, TTrack = initdb(engine)

    print TUser, TBase, TTrack

    #
    get_data(engine, TBase, 'COM12', 115200, 1)
    #print TBase

# ''' when run from the IDE to comment out the following two lines and uncomment the third '''
if __name__ == "__main__":
    main()


# ''' when run from the console, you need to uncomment the two previous lines and comment out the next line '''
#main()

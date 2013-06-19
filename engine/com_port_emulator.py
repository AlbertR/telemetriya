#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Эмуляция потока данных из COM порта
'''

import sys, random
import datetime as dt
from sqlalchemy import orm, schema, types, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def initdb(engine):

    connection = engine.connect()

    class TStatistics(Base):
        __tablename__ = 'statistics'
        __table_args__ = {
            'mysql_charset':'utf8'
        }

        id = schema.Column(types.Integer, schema.Sequence('statistics_id', optional=True), primary_key=True)
        date = schema.Column(types.DateTime(), default=dt.datetime.now())
        label_id = schema.Column(types.Integer, default = 0)
        user_id = schema.Column(types.Integer, default = 0)
        ringtime = schema.Column(types.Float, default = 0)
        track_id = schema.Column(types.Integer)
        session = schema.Column(types.Integer)

        def __init__(self, date, label_id, user_id, ringtime, track_id, session):
            self.date = date
            self.label_id = label_id
            self.user_id = user_id
            self.ringtime = ringtime
            self.track_id = track_id
            self.session = session

    Base.metadata.create_all(engine)

    return TStatistics

def filldb(engine, TStatistics, user, label, ringtime, sessions):

    Session = sessionmaker(bind=engine)
    session = Session()

    date_now = dt.datetime.now()
    basedata = TStatistics(date=date_now.strftime('%Y-%m-%d %H:%M:%S'), label_id=label, user_id=user, ringtime=ringtime, track_id=1,  session=sessions)

    session.add(basedata)
    session.commit()

def main():

    # список пользователей
    users = ['9', '25', '32']
    # список меток
    labels = ['1', '10', '11']
    #
    dbparam = 'mysql://root:30v11aiR@178.132.203.168:3306/_telemetriya?charset=utf8&use_unicode=1'
    engine = create_engine(dbparam, echo=False)
    TStatistics = initdb(engine)

    for sessions in range(1,4):
        # сколько кругов в сессии
        rounds = random.randrange(1,11,1)
        i = 1
        while i <= rounds:
            for j in range(0,3):
                ringtime = random.uniform(45.0, 70.0)
                print "%s %s %.3f %s" % (users[j], labels[j], ringtime, sessions)
                filldb(engine, TStatistics, users[j], labels[j], ringtime, sessions)
            i += 1

#if __name__ == "__main__":
#    main()

main()

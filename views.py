from django.shortcuts import render
from django.shortcuts import render_to_response
from polls.models import Poll
import urllib2
import json
import ConfigParser
import MySQLdb
import time
from datetime import datetime, timedelta, date, time as dt_time
import sys
import collections

def index(request):
    config = ConfigParser.RawConfigParser()
    config.read('congigsDj.ini')


    db = MySQLdb.connect(host='localhost', user='djangouser', passwd = 'meteo',
                         db = 'djangodb')

    cursor = db.cursor()

    sql = """SELECT day(max(date)) from prognoz 
    """
    cursor.execute(sql)
    data = cursor.fetchall()
    
    if data[0][0] < int(time.strftime("%d")) + 6:
        response = urllib2.urlopen('http://api.openweathermap.org/data/2.5/forecast/daily?id=524901&appid=bd82977b86bf27fb59a04b61b657fb6f')
        data = response.read()
        a = json.loads(data)
        i = 0
        while i < 7:
            print (i)
            sql = """INSERT INTO prognoz(date, temperature, pressure, nebulosity, humidity, city, forecast)
            VALUES (CAST(FROM_UNIXTIME('%(date)s') AS DATE), '%(temperature)s', '%(pressure)s', '%(nebulosity)s', '%(humidity)s', '%(city)s', '%(forecast)s')
            """%{"date":a['list'][i]['dt'],"temperature":a['list'][i]['temp']['day']-273.15 , "pressure":a['list'][i]['pressure'], "nebulosity":a['list'][i]['clouds'],
                 "humidity":a['list'][i]['humidity'], "city":a['city']['name'], "forecast":i}
            cursor.execute(sql)
            db.commit()
            i = i + 1



    sql5 = """SELECT * from prognoz"""
    cursor.execute(sql5)
    mydata = []

    data = cursor.fetchall()
    for rec in data:
        d = rec[0]
        t = rec[1]
        pr = rec[2]
        n = rec[3]
        h = rec[4]
        f = rec[6]
        mydata.append( "date  %(date)s, temperature  %(temperature)s, pressure  %(pressure)s, nebulosity  %(nebulosity)s, humidity  %(humidity)s, forecast  %(forecast)s"%{"date":d, "temperature":t, "pressure":pr, "nebulosity":n, "humidity":h, "forecast":f})

    sql = """select date, temperature from prognoz where forecast=0 group by date"""
    cursor.execute(sql)
    data0 = cursor.fetchall()

    er = [0]*6
    for x in range(1,6):
        sql = """select date, temperature from prognoz where forecast=%(x)s group by date"""%{"x":x}
        cursor.execute(sql)
        data = cursor.fetchall()
        inac = 0
        i = 0
        for rec in data:
            for rec0 in data0:
                if rec[0] in rec0:
                    i = i + 1
                    inac = inac + abs(float(rec0[1]) - float(rec[1]))
        if inac > 0:
            er[x-1] = round(inac/i,2)
    L = [["empty","empty","empty","empty","empty","empty","empty"]for x in range(7)]
    forcasts = [0,1,2,3,4,5,6]
    now_date = datetime.today()
    dates = [str(now_date.date()+timedelta(days=-6)),str(now_date.date()+timedelta(days=-5)),str(now_date.date()+timedelta(days=-4)),str(now_date.date()+timedelta(days=-3)),
         str(now_date.date()+timedelta(days=-2)),str(now_date.date()+timedelta(days=-1)),str(now_date.date())]

    for x in range(0,7):
        sql = """select date, temperature, forecast from prognoz where date=DATE_sub(CURDATE(),Interval %(x)s DAY) group by forecast"""%{"x":6-x}
        cursor.execute(sql)
        data = cursor.fetchall()
        if int(data[0][2]) == 0:
            rec0 = data[0][1]
            for rec in data:
                k = int(rec[2])
                L[k][x] = round(abs(float(rec0) - float(rec[1])),2)
    i = 0
    while i < 7:
        L[i]=collections.OrderedDict(zip(dates,L[i]))
        i = i + 1

    e = collections.OrderedDict(zip(forcasts,L))
    dates = (" ",str(now_date.date()+timedelta(days=-6)),str(now_date.date()+timedelta(days=-5)),str(now_date.date()+timedelta(days=-4)),str(now_date.date()+timedelta(days=-3)),
         str(now_date.date()+timedelta(days=-2)),str(now_date.date()+timedelta(days=-1)),str(now_date.date()))
    return render_to_response('polls/index.html', {'mydata': mydata,'er': er,'e':e,'dates':dates})

def detail(request, poll_id):
    return HttpResponse("You're looking at poll %s." % poll_id)

def results(request, poll_id):
    return HttpResponse("You're looking at the results of poll %s." % poll_id)

def vote(request, poll_id):
    return HttpResponse("You're voting on poll %s." % poll_id)


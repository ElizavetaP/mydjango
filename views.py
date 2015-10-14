from django.shortcuts import render
from django.shortcuts import render_to_response
from polls.models import Poll
import urllib2
import json
import ConfigParser
import MySQLdb
import time
from datetime import datetime
import sys

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
            er[x-1] = round(inac,2)/i
    return render_to_response('polls/index.html', {'mydata': mydata,'er': er})

def detail(request, poll_id):
    return HttpResponse("You're looking at poll %s." % poll_id)

def results(request, poll_id):
    return HttpResponse("You're looking at the results of poll %s." % poll_id)

def vote(request, poll_id):
    return HttpResponse("You're voting on poll %s." % poll_id)


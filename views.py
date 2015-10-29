from django.shortcuts import render
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.template import RequestContext
from polls.models import Choice, Poll
from polls.models import Poll
from django.http import HttpResponse
from django.http import Http404

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

    sql = """SELECT max(date) from prognoz 
    """
    cursor.execute(sql)
    data = cursor.fetchall()

    def writeforecast(url):
        response = urllib2.urlopen(url)
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
    d = datetime.today()
    if data[0][0] < d.date()+timedelta(days=6):
        writeforecast('http://api.openweathermap.org/data/2.5/forecast/daily?id=524901&appid=bd82977b86bf27fb59a04b61b657fb6f')
        writeforecast('http://api.openweathermap.org/data/2.5/forecast/daily?q=London,uk&appid=bd82977b86bf27fb59a04b61b657fb6f')

                    
    latest_poll_list = Poll.objects.all().order_by('-pub_date')[:5]
    
    return render_to_response('polls/index.html', {'latest_poll_list': latest_poll_list})

def detail(request, poll_id):
    config = ConfigParser.RawConfigParser()
    config.read('congigsDj.ini')


    db = MySQLdb.connect(host='localhost', user='djangouser', passwd = 'meteo',
                         db = 'djangodb')

    cursor = db.cursor()
    def selectcity(city):
        
        sql5 = """SELECT * from prognoz where city = '%(city)s'"""%{"city":city}
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
        sql = """select date, temperature from prognoz where city = '%(city)s' and forecast=0 group by date"""%{"city":city}
        cursor.execute(sql)
        data0 = cursor.fetchall()

        er = [0]*6
        for x in range(1,7):
            sql = """select date, temperature from prognoz where city = '%(city)s' and forecast=%(x)s group by date"""%{"x":x, "city":city}
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
        L = [[["empty"],["empty"],["empty"],["empty"],["empty"],["empty"],["empty"]]for x in range(7)]
        forcasts = [0,1,2,3,4,5,6]
        now_date = datetime.today()
        dates = [str(now_date.date()+timedelta(days=-6)),str(now_date.date()+timedelta(days=-5)),str(now_date.date()+timedelta(days=-4)),str(now_date.date()+timedelta(days=-3)),
             str(now_date.date()+timedelta(days=-2)),str(now_date.date()+timedelta(days=-1)),str(now_date.date())]

        sql = """SELECT max(date) from prognoz 
        """
        if len(mydata) > 49:
            for x in range(0,7):
                sql = """select date, temperature, forecast from prognoz where city = '%(city)s' and date=DATE_sub(CURDATE(),Interval %(x)s DAY) group by forecast"""%{"x":6-x, "city":city}
                cursor.execute(sql)
                data = cursor.fetchall()
                if int(data[0][2]) == 0:
                    rec0 = data[0][1]
                    for rec in data:
                        k = int(rec[2])
                        L[k][x] = ('''%(temp)sC'''%{'temp':round(float(rec[1]),2)}, round(float(rec[1])-float(rec0),2))
            i = 0
            while i < 7:
                L[i]=collections.OrderedDict(zip(dates,L[i]))
                i = i + 1

            e = collections.OrderedDict(zip(forcasts,L))
        else:
            e = 0
        dates = (" ",str(now_date.date()+timedelta(days=-6)),str(now_date.date()+timedelta(days=-5)),str(now_date.date()+timedelta(days=-4)),str(now_date.date()+timedelta(days=-3)),
            str(now_date.date()+timedelta(days=-2)),str(now_date.date()+timedelta(days=-1)),str(now_date.date()))
        
        return (mydata, er, e, dates)
    p = get_object_or_404(Poll, pk=poll_id)
    if p.id==4:
        s = selectcity('Moscow')
    if p.id==5:
        s = selectcity('London')
        
    mydata = s[0]
    er = s[1]
    e = s[2]
    dates = s[3]

    return render_to_response('polls/detail.html', {'mydata': mydata,'er': er,'e':e,'dates':dates},
                               context_instance=RequestContext(request))

def results(request, poll_id):
    return HttpResponse("You're looking at the results of poll %s." % poll_id)

def vote(request, poll_id):

    p = get_object_or_404(Poll, pk=poll_id)
    try:
        selected_choice = p.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the poll voting form.
        return render_to_response('polls/detail.html', {
            'poll': p,
            'error_message': "You didn't select a choice.",
        }, context_instance=RequestContext(request))
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('polls.views.results', args=(p.id,)))

# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals 
from kodi_six import xbmcaddon
import datetime,time
import requests
from resources.lib import xmltodict, client

__addon__ = xbmcaddon.Addon()
gmt_offset = int(__addon__.getSetting('gmt.offset'))
local_time = datetime.datetime.now()
local_time = local_time + datetime.timedelta(hours=gmt_offset)
current_time = local_time.strftime("%H:%M")
current_date = local_time.strftime("%Y-%m-%d")


def get_list(channel, id):

    r = client.request('http://www.mediaklikk.hu/iface/broadcast/{0}/broadcast_{1}.xml'.format(current_date, id), cache=True)
    if r.status_code != 200:
        return
    r.encoding = 'utf-8'
    items = xmltodict.parse(r.text)['Items']['Item']
    
    list = []

    for i in items:
        start = i['Date']
        try: 
            dstart = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        except TypeError:
            dstart = datetime.datetime(*(time.strptime(start, "%Y-%m-%d %H:%M:%S")[0:6]))
        start = datetime.datetime.strftime(dstart, "%H:%M")
        stop = i['Length']
        stop = stop.split(':')
        stop = dstart + datetime.timedelta(0,int(stop[2]),0,0,int(stop[1]),int(stop[0]))
        stop = datetime.datetime.strftime(stop, "%H:%M")
        try:
            title2 = i['Title']
            if not title2: title2 = '0'
        except:
            title2 = '0'
        try:
            title1 = i['SeriesTitle']
            if not title1: title1 = '0'
        except:
            title1 = '0'
        if not title2 == '0' and not title1 == '0': title = '{0} - {1}'.format(title1, title2)
        elif title2 == '0' and not title1 == '0': title = title1
        elif title1 == '0' and not title2 == '0': title = title2
        else: title = ''
        list.append({'channel': channel, 'title': title, 'start': start, 'stop': stop})
  
    return list


def get_epg(channel, id, active=None):
    
    items = get_list(channel, id)
    
    if not active == True:
        return items
    
    item = [i for i in items if i['start'] < current_time < i['stop']]
    if len(item) == 1:
        item = item[0]
    else:
        item = [i for i in items if i['start'] < current_time]
        item = item[-1]
    return '{0}  |  {1}'.format(item['channel'], item['title'])

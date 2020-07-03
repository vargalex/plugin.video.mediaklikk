# -*- coding: utf-8 -*-

import os,xbmc,re,datetime,time
from resources.lib import client, control, cache

gmt_offset = int(control.setting('gmt.offset'))
local_time = datetime.datetime.now()
local_time = local_time + datetime.timedelta(hours=gmt_offset)
current_time = local_time.strftime("%H:%M")
current_date = local_time.strftime("%Y-%m-%d")
broadcast = {'m1': '1', 'm2': '2', 'm4 sport': '30', 'm5': '33', 'duna': '3', 'duna world': '4'}

def list_cache(channel):
    r = client.request('http://www.mediaklikk.hu/iface/broadcast/%s/broadcast_%s.xml' % (current_date, broadcast[channel.lower()]))
    items = client.parseDOM(r, 'Item')
    return items

def get_list(channel):
    try:
        items = cache.get(list_cache, 15, channel)
        if len(items) == 0: raise Exception()
        list = []
        for i in items:
            try:
                start = client.parseDOM(i, 'Date')[0]
                try: 
                    dstart = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
                except TypeError:
                    dstart = datetime.datetime(*(time.strptime(start, "%Y-%m-%d %H:%M:%S")[0:6]))
                start = datetime.datetime.strftime(dstart, "%H:%M")
                stop = client.parseDOM(i, 'Length')[0]
                stop = stop.split(':')
                stop = dstart + datetime.timedelta(0,int(stop[2]),0,0,int(stop[1]),int(stop[0]))
                stop = datetime.datetime.strftime(stop, "%H:%M")
                try: title2 = client.parseDOM(i, 'Title')[0]
                except: title2 = '0'
                title2 = title2.encode('utf-8')
                try: title1 = client.parseDOM(i, 'SeriesTitle')[0]
                except: title1 = '0'
                title1 = title1.encode('utf-8')
                channel = channel.encode('utf-8')
                if not title2 == '0' and not title1 == '0': title = '%s - %s' % (title1, title2)
                elif title2 == '0' and not title1 == '0': title = title1
                elif title1 == '0' and not title2 == '0': title = title2
                else: title = ''
                list.append({'channel': channel, 'title': title, 'start': start, 'stop': stop})
            except:
                pass
        return list
    except:
        return list

def get_epg(channel, active=None):
    
    items = get_list(channel)
    
    if not active == True: return items
    
    else:
        try:
            item = [i for i in items if i['start'] < current_time < i['stop']]
            if not len(item) == 0: item = item[0]
            else:
                item = [i for i in items if i['start'] < current_time]
                if len(item) == 0: raise Exception()
                item = item[-1]
            title = client.replaceHTMLCodes(item['title'].decode('utf-8'))
            return '%s  ->  %s' % (item['channel'], title.encode('utf-8'))
        except:
            return channel.encode('utf-8')

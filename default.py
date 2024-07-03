# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from kodi_six import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import re, os, json, sys
import requests
from resources.lib import client

try:
    from urlparse import parse_qsl
    from urllib import quote_plus
    from xbmc import translatePath
except:
    from urllib.parse import quote_plus, parse_qsl
    from xbmcvfs import translatePath

_url = sys.argv[0]
_handle = int(sys.argv[1])
__addon__ = xbmcaddon.Addon()
MediaDir = translatePath(os.path.join(__addon__.getAddonInfo('path'), 'resources', 'media'))
_addonFanart = __addon__.getAddonInfo('fanart')
_addonIcon = __addon__.getAddonInfo('icon')
__addon__.setSetting('ver', __addon__.getAddonInfo('version'))

BASE_URL = 'https://mediaklikk.hu'
API_URL = BASE_URL + '/wp-content/plugins/hms-mediaklikk/interfaces/mediaStoreData.php?action={}'


def main_folders():

    addDirectoryItem(u'ÉLŐ', 'live')
    addDirectoryItem(u'TV műsorok A-Z', 'media_list&url=tvchannels')
    addDirectoryItem(u'Rádió műsorok A-Z', 'media_list&url=radiochannels')

    #xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)


def media_list(url):

    headers = {'X-Requested-With': 'XMLHttpRequest'}
    ch = client.request(API_URL.format(url), headers=headers)
    channelCodes = [i['ShortCode'] for i in ch.json()]
    result = client.request(API_URL.format('programs'), headers=headers)
    u = 'videos' if url == 'tvchannels' else 'audios'
    for item in result.json():
        if item['Channel'] in channelCodes:
            addDirectoryItem(item['Title'], 'episode_list&url={0}&id={1}'.format(u, item['Id']))

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)


def episode_list(url, id, page=0):

    r = client.request(API_URL.format(url + '&id={0}&page={1}&count=12'.format(id, str(page))))
    items = r.json()['Items']
    for item in items:
        if url == 'videos':
            title = item['Title']
            icon = item['Image']
            query = 'resolve&url={0}&mediatype={1}'.format(item['Token'], 'tv')
        else:
            title = item['Title'] + ' - ' + item['Date']
            icon = None
            dataDate = re.sub(r'[\W_]+', '', item['DataDate'])
            dataEndDate = re.sub(r'[\W_]+', '', item['DataDateEnd'])
            date = item['BeginDate']
            u = 'https://hangtar-cdn.connectmedia.hu/' + dataDate + '/' + dataEndDate + '/' + item['DataCh'] + '.mp3'
            query = 'resolve&url={0}&mediatype={1}'.format(u, 'radio')
        addDirectoryItem(title, query, icon=icon, meta={'Title': title}, isFolder=False)
    
    if len(items) != 0:
        addDirectoryItem(u'>> KÖVETKEZŐ OLDAL >>', 'episode_list&url={0}&id={1}&page={2}'.format(url, id, str(page+1)))
    
    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)


def live_channels():
    
    from resources.lib import epglist
    channels = [
                {'title': u'M1', 'url': 'mtv1live', 'icon': 'm1.png', 'type': 'tv', 'epg': '1'},
                {'title': u'M2', 'url': 'mtv2live', 'icon': 'm2.png', 'type': 'tv', 'epg': '2'},
                {'title': u'M3', 'url': '', 'icon': 'm3.png', 'type': 'tv'},
                {'title': u'M4 Sport', 'url': 'mtv4live', 'icon': 'm4.png', 'type': 'tv', 'epg': '30'},
                {'title': u'M4 Sport +', 'url': 'mtv4plus', 'icon': 'm4.png', 'type': 'tv', 'epg': '34'},
                {'title': u'M5', 'url': 'mtv5live', 'icon': 'm5.png', 'type': 'tv', 'epg': '33'},
                {'title': u'Duna', 'url': 'dunalive', 'icon': 'duna.png', 'type': 'tv', 'epg': '3'},
                {'title': u'Duna World', 'url': 'dunaworldlive', 'icon': 'dunaworld.png', 'type': 'tv', 'epg': '4'},
                
                {'title': u'Kossuth Rádió', 'url': '/kossuth-radio-elo/', 'icon': 'kossuth.png', 'type': 'radio'},
                {'title': u'Petőfi Rádió', 'url': '/petofi-radio-elo', 'icon': 'petofi.png', 'type': 'radio'},
                {'title': u'Bartók Rádió', 'url': '/bartok-radio-elo/', 'icon': 'bartok.png', 'type': 'radio'},
                {'title': u'Dankó Rádió', 'url': '/danko-radio-elo', 'icon': 'danko.png', 'type': 'radio'},
                {'title': u'Nemzetiségi Rádió', 'url': '/nemzetisegi-adasok-elo/', 'icon': 'nemzetisegi.png', 'type': 'radio'},
                {'title': u'Parlamenti Rádió', 'url': '/parlamenti-adasok-elo', 'icon': 'parlamenti.png', 'type': 'radio'},
                {'title': u'Duna World Rádió', 'url': '/duna-world-radio-elo/', 'icon': 'dunaworld.png', 'type': 'radio'}
                ]

    for channel in channels:
        if 'epg' in channel and __addon__.getSetting('showepg') == 'true':
            try: title = epglist.get_epg(channel['title'], channel['epg'], active=True)
            except: title = channel['title']
        else:
            title = channel['title']
        addDirectoryItem(title, 'resolve&url={0}&mediatype={1}&title={2}'.format(channel['url'], channel['type'], channel['title']), icon=os.path.join(MediaDir, channel['icon']), meta={'Title': channel['title']}, isFolder=False)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)


def resolve(title, url, media):

    play_item = xbmcgui.ListItem()
    if media == 'radio':
        type = 'video'
        if url.startswith('http'):
            streamURL = url

        else:
            r = client.request(BASE_URL + url)
            streamURL = re.search("""radioStreamUrl\s*=\s*['"]([^'"]+)""", r.text).group(1)

    elif media == 'tv':
        type = 'video'
        if title == 'M3':
            r = client.request('https://archivum.mtva.hu/m3/stream?no_lb=1&target=live')
            streamURL = r.json()['url']

        else:
            resp = client.request('https://player.mediaklikk.hu/playernew/player.php?noflash=yes&video=' + quote_plus(url)).text

            json_regex_patt = r"setup\((.*?)\);"
            json_text = re.search(json_regex_patt, resp, re.DOTALL).group(1)
            norm_json = json.loads(json_text)

            hls_entry = None
            streamURL = None
            if norm_json:
                for item_x in norm_json['playlist']:
                    if title == 'M4 Sport':
                        if item_x["type"] == "hls" and "Seconds" not in item_x["file"]:
                            hls_entry = item_x
                    if hls_entry:
                        streamURL = hls_entry['file']
                    elif 'index.m3u8' in item_x['file']:
                        streamURL = item_x['file']
                    else:
                        streamURL = norm_json['playlist'][0]['file']
            else:
                streamURL = None

    if not streamURL:
        return xbmcplugin.setResolvedUrl(_handle, False, listitem=play_item)

    if streamURL.startswith('//'): streamURL = 'https:' + streamURL

    play_item.setPath(path=streamURL)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)


def addDirectoryItem(name, query, icon=None, context=None, queue=False, isFolder=True, meta=None):

    url = '%s?action=%s' % (_url, query)
    icon = icon if icon else _addonIcon
    isPlayable = 'true' if isFolder == False else 'false'
    cm = []
    if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % _url))
    if not context == None: cm.append((context[0], 'RunPlugin(%s?action=%s)' % (_url, context[1])))
    item = xbmcgui.ListItem(label=name)
    item.addContextMenuItems(cm)
    item.setArt({'icon': icon, 'poster': icon})
    item.setProperty('Fanart_Image', _addonFanart)
    item.setProperty('IsPlayable', isPlayable)
    if meta:
        item.setInfo(type='video', infoLabels = meta)
    xbmcplugin.addDirectoryItem(handle=_handle, url=url, listitem=item, isFolder=isFolder)


params = dict(parse_qsl(sys.argv[2][1:]))
action = params.get('action')
url = params.get('url')
title = params.get('title', '')
page = int(params.get('page', 0))
id = params.get('id')
mediatype = params.get('mediatype')

if not action:
    main_folders()
elif action == 'media_list':
    media_list(url)
elif action == 'episode_list':
    episode_list(url, id, page)
elif action == 'live' :
    live_channels()
elif action == 'resolve':
    resolve(title, url, mediatype)

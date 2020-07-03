# -*- coding: utf-8 -*-
import xbmc, xbmcgui, urllib, re, xbmcplugin, xbmcaddon, os, json, sys
from resources.lib import client, control, epglist


thisAddon = xbmcaddon.Addon(id='plugin.video.mediaklikk')
addonInfo = thisAddon.getAddonInfo
thisAddonDir = xbmc.translatePath(thisAddon.getAddonInfo('path')).decode('utf-8')
MediaDir = xbmc.translatePath(os.path.join(thisAddonDir, 'resources', 'media'))
sysfanart = addonInfo('fanart')

mklikk_url = 'https://www.mediaklikk.hu'

def main_folders():
    addDir('ÉLŐ', '', 5, MediaDir + '\\mediaklikk_logo.png', '', '')
    addDir('TV műsorok A-Z', mklikk_url + '/mediatar/', 1, MediaDir + '\\mediaklikk_logo.png', 'Tv', '')
    addDir('Rádió műsorok A-Z', mklikk_url + '/mediatar/', 1, MediaDir + '\\mediaklikk_logo.png', 'Rádió', '')

def live_folders():
    addDir('TV', '', 6, iconimage, 'Tv', '')
    addDir('Rádió', '', 8, iconimage, 'Rádió', '')

def musor_lista():
    radio_list = ['ks', 'pf', 'br', 'dk', 'nm', 'pm']
    tv_list = ['m1', 'm2', 'm4', 'dn', 'dw','m5']
    if description == 'Tv': chan_list = tv_list
    else: chan_list = radio_list
    r = client.request(url)
    m = re.compile('\{"Id":([0-9]+),"Channel":"(.+?)","Title":"(.+?)"').findall(r)
    for id, chan, title in m:
        try:
            if chan in chan_list:
                addDir(title.decode('unicode-escape').encode('utf-8'), id, 2, iconimage, description, '')
        except:
            pass

def epizod_lista():
    if description == 'Tv':
        r = client.request(mklikk_url + '/wp-content/plugins/hms-mediaklikk/interfaces/mediaStoreData.php?action=videos&id=' + url)
        m = json.loads(r)['Items']
        for i in m:
            try:
                title = i['Date'] + ' - ' + i['Title']
                addFile(title.encode('utf-8'), i['Token'].encode('utf-8'), 3, i['Image'].encode('utf-8'), description)
            except:
                pass
    elif description == 'Rádió':
        r = client.request(mklikk_url + '/wp-content/plugins/hms-mediaklikk/interfaces/mediaStoreData.php?action=audios&id=' + url + '&page=0&count=100')
        result = json.loads(r)['Items']
        for item in result:
            try:
                dataDate = re.sub(r'[\W_]+', '', item['DataDate'])
                dataEndDate = re.sub(r'[\W_]+', '', item['DataDateEnd'])
                date = item['BeginDate']
                file = re.search('from=([^&]+)', item['PlayParam']).group(1)
                addFile(name + ' - ' + date.encode('utf-8'), 'https://hangtar-cdn.connectmedia.hu/' + dataDate + '/' + dataEndDate + '/' + item['DataCh'] + '.mp3', 14, iconimage, description)
            except:
                pass


def live_tv():
    r = client.request(mklikk_url)
    m = client.parseDOM(r, 'div', attrs = {'class': 'liveStreamsMenu'})[0]
    m = client.parseDOM(m, 'div', attrs = {'class': 'col'})[0]
    m = client.parseDOM(m, 'li')
    for item in m:
        url = client.parseDOM(item, 'a', ret='href')[0]
        if "-elo" in url:
            if not url.startswith('http:'): url = 'http:' + url
            name = client.parseDOM(item, 'a')[0]
            name = name.split('>')[-1].strip()
            try: label = epglist.get_epg(name, active=True)
            except: label = name
            addFile(label, url, 7, MediaDir + '\\' + name.lower() + '.png', '')
    return

def live_radio():
    addFile('Kossuth Rádió', '/kossuth-radio-elo/', 9, MediaDir + '\\Kossuth.png', '')
    addFile('Petőfi Rádió', '/petofi-radio-elo', 9, MediaDir + '\\Petofi.png', '')
    addFile('Bartók Rádió', '/bartok-radio-elo/', 9, MediaDir + '\\Bartok.png', '')
    addFile('Dankó Rádió', '/danko-radio-elo', 9, MediaDir + '\\Danko.png', '')
    addFile('Nemzetiségi Rádió', '/nemzetisegi-adasok-elo/', 9, MediaDir + '\\Nemzetisegi.png', '')
    addFile('Parlamenti Rádió', '/parlamenti-adasok-elo', 9, MediaDir + '\\Parlamenti.png', '')
    addFile('Duna World Rádió', '/duna-world-radio-elo/', 9, MediaDir + '\\DUNA WORLD.png', '')

def get_epg():
    try:
        list = epglist.get_epg(name)
        programs = ['[B]%s[/B] - %s' % (i['start'], i['title']) for i in list]
        q = control.selectDialog(programs, name)
        if not q == -1: get_liveTv()
    except:
        return

def play_url(url, iconimage, name):
    videoitem = xbmcgui.ListItem(label=name, thumbnailImage=iconimage)
    videoitem.setInfo(type='Video', infoLabels={'Title': name})
    xbmc.Player().play(url, videoitem)
    
def get_Tv():   
    m = client.request('https://player.mediaklikk.hu/playernew/player.php?video=' + url)
    m = m.replace('\\', '')
    direct_url = re.search('"file"\s*:\s*"([^"]+)', m).group(1)
    chunk_list = client.request('http:%s' % direct_url)
    chunk_list = chunk_list.replace('\n', '')
    chunk_list = re.compile('BANDWIDTH=([0-9]+)(.+?m3u8)').findall(chunk_list)
    if len(chunk_list) == 0: direct_url = direct_url[0]
    else:
        chunk_list = [(int(i[0]), i[1]) for i in chunk_list]
        chunk_list = sorted(chunk_list, reverse=True)
        q_list = [str(i[0]) for i in chunk_list]
        q_list = [q.replace('3000000', '720p').replace('1600000', '480p').replace('1200000', '360p').replace('800000', '290p').replace('400000', '180p') for q in q_list]
        auto_pick = control.setting('autopick') == '1'

        if auto_pick == True:
            stream = chunk_list[0][1]
        else:
            q = xbmcgui.Dialog().select(u'Min\u0151s\u00E9g', q_list)
            if q == -1:
                return
            else:
                stream = chunk_list[q][1]
        direct_url = direct_url.split('playlist')[0] + stream
    play_url('http:%s' % direct_url, iconimage, name)


def get_liveTv():
    from resources.lib import m3u8_parser
    
    title = name.split('-')[0].strip()
    
    if not title.lower() == 'm3':
        r = client.request(url)
        streamid = re.search('"streamId"\s*:\s*"([^"]+)', r).group(1)

        drm_info = client.request('https://player.mediaklikk.hu/playernew/public/stream/%s.json' % streamid)
        drm_info = json.loads(drm_info)
        drm_info = drm_info['drm']

        if drm_info == True:
            control.infoDialog(u'Lej\u00E1tsz\u00E1s sikertelen. Az \u00E9l\u0151 ad\u00E1s DRM v\u00E9delemmel van ell\u00E1tva.', icon='')
            return

        r = client.request('https://player.mediaklikk.hu/playernew/player.php?video=%s' % streamid)
        r = r.replace('\\', '').replace('\n', '')
        direct_url = re.findall('"file"\s*:\s*"([^"]+)', r)
        direct_url = [i for i in direct_url if not 'FWC2018' in i][0]

        direct_url = direct_url.replace('\\', '')
        if not direct_url.startswith('http'): direct_url = 'http:' + direct_url
        result = client.request(direct_url)
        url_list = m3u8_parser.parse(result)['playlists']
        url_list = [(i['stream_info']['resolution'].split('x')[1], i['uri']) for i in url_list]
        url_list = sorted(url_list, key=lambda tup: int(tup[0]), reverse=True)
        q_list = [x[0] + 'p' for x in url_list]
        
        auto_pick = control.setting('autopick') == '1'

        if len(url_list) == 1 or auto_pick == True:
            stream = url_list[0][1]
        else:
            q = xbmcgui.Dialog().select(u'Min\u0151s\u00E9g', q_list)
            if q == -1:
                return
            else:
                stream = url_list[q][1]
        
        stream = direct_url.split('index.m3u8')[0] + stream
    
    else:
        m3_cookie = client.request(url, output = 'cookie')
        m3_token = re.search('Token=([a-zA-Z0-9]+)', m3_cookie).group(1)
        m3_streamUrl = client.request('https://archivum.mtva.hu/m3/stream?target=live')
        m3_streamUrl = json.loads(m3_streamUrl).get('live')
        stream = m3_streamUrl.replace('[sessid]', m3_token)
        
        '''direct_url = 'https://stream.nava.hu:443/m3_live_drm/smil:m3.smil/playlist.m3u8'''
 
    play_url(stream, iconimage, title)


def get_liveRadio():
    r = client.request(mklikk_url + url)
    r = r.replace('\'','')
    direct_url = re.compile('radioStreamUrl\s*?=\s*?(http.+?mp3)').findall(r)
    if direct_url:
        play_url(direct_url[0], iconimage, name)
    return   


def addDir(name, url, mode, iconimage, description, page):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&description="+urllib.quote_plus(description)+"&page="+str(page)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
    liz.setProperty( "Fanart_Image", sysfanart )
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
    return ok

def addFile(name, url, mode, iconimage, description):
    u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)+"&description="+urllib.quote_plus(description)
    ok=True
    liz=xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description } )
    liz.setProperty( "Fanart_Image", sysfanart )
    cm = []
    cm.append((u'M\u0171sor\u00FAjs\u00E1g', 'RunPlugin(%s?mode=20&url=%s&name=%s)' % (sys.argv[0], urllib.quote_plus(url), urllib.quote_plus(name.split('-')[0].strip()))))
    liz.addContextMenuItems(cm, replaceItems=True)
    ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=False)
    return ok


def get_params():
    param=[]
    paramstring=sys.argv[2]
    if len(paramstring)>=2:
        params=sys.argv[2]
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]
    return param

params = get_params()
url = None
name = None
mode = None
iconimage = None
description = ''
page = 0
search_text = ''

try:
    url = urllib.unquote_plus(params["url"])
except:
    pass
try:
    name = urllib.unquote_plus(params["name"])
except:
    pass
try:
    iconimage = urllib.unquote_plus(params["iconimage"])
except:
    pass
try:        
    mode = int(params["mode"])
except:
    pass
try:        
    description = urllib.unquote_plus(params["description"])
except:
    pass
try:        
    page = int(params["page"])
except:
    pass
try:        
    search_text = urllib.unquote_plus(params["description"])
except:
    pass

if mode==None:
    main_folders()
elif mode==1:
    musor_lista()
elif mode==2:
    epizod_lista()
elif mode==3:
    get_Tv()
elif mode==5:
    live_folders()
elif mode==6:
    live_tv()
elif mode==7:
    get_liveTv()
elif mode==8:
    live_radio()
elif mode==9:
    get_liveRadio()
elif mode==14:
    play_url(url, iconimage, name)
elif mode==20:
    get_epg()
    
xbmcplugin.endOfDirectory(int(sys.argv[1]))

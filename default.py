# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from kodi_six import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import re, os, json, sys
from resources.lib import client
import urllib.parse
import hashlib

import requests
from bs4 import BeautifulSoup

from urllib.parse import urlparse, parse_qsl, quote_plus, unquote_plus

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

json_path_file = os.path.join(__addon__.getAddonInfo('path'), 'temp_data.json')

BASE_URL = 'https://mediaklikk.hu'
API_URL = BASE_URL + '/wp-content/plugins/hms-mediaklikk/interfaces/mediaStoreData.php?action={}'

cookies = {
    'SERVERID': 'mtvacookieD',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://mediaklikk.hu'
}

radio_station_list = [
  {
    "stationName": "Kossuth",
    "stationShortId": "mr1",
    "stationLinkId": "kossuth-radio",
    "stationShortCode": "ks"
  },
  {
    "stationName": "Dankó",
    "stationShortId": "mr7",
    "stationLinkId": "danko-radio",
    "stationShortCode": "dk"
  },
  {
    "stationName": "Bartók",
    "stationShortId": "mr3",
    "stationLinkId": "bartok-radio",
    "stationShortCode": "br"
  },
  {
    "stationName": "Parlamenti",
    "stationShortId": "mr5",
    "stationLinkId": "parlamenti-radio",
    "stationShortCode": "pm"
  },
  {
    "stationName": "Nemzetiségi",
    "stationShortId": "mr4",
    "stationLinkId": "nemzetisegi-radio",
    "stationShortCode": "nm"
  },
  {
    "stationName": "Petőfi",
    "stationShortId": "mr2",
    "stationLinkId": "petofi-radio",
    "stationShortCode": "pl"
  },
  {
    "stationName": "Duna World",
    "stationShortId": "mr8",
    "stationLinkId": "duna-world-radio",
    "stationShortCode": "dw"
  },
  {
    "stationName": "Szakcsi",
    "stationShortId": "mr9",
    "stationLinkId": "szakcsi-radio",
    "stationShortCode": "s10"
  },
  {
    "stationName": "NSR",
    "stationShortId": "mr11",
    "stationLinkId": "nsr-radio",
    "stationShortCode": "nsr"
  },
  {
    "stationName": "Csukás",
    "stationShortId": "mr10",
    "stationLinkId": "csukas-radio",
    "stationShortCode": "s11"
  }
]

def main_folders():
    addDirectoryItem(u'ÉLŐ', 'live')
    addDirectoryItem(u'TV műsorok A-Z', 'media_list&url=tvchannels')
    addDirectoryItem(u'Rádió műsorok A-Z', 'media_list&url=radiochannels')
    addDirectoryItem(u'epg-ből visszatöltés (rádiók)', 'sub_epg_menu')
    addDirectoryItem(u'Főoldal', 'list_main_categories_from_json&url=https://mediaklikk.hu')
    addDirectoryItem(u'TV', 'list_main_categories_from_json&url=https://mediaklikk.hu/tv')
    addDirectoryItem(u'RÁDIÓ', 'list_main_categories_from_json&url=https://mediaklikk.hu/radio')
    addDirectoryItem(u'SPORT', 'list_main_categories_from_json&url=https://mediaklikk.hu/sport')
    addDirectoryItem(u'[B]Kereső[/B]', 'search')

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def search():
    keyboard = xbmc.Keyboard('', 'keresés a műsorok között')
    keyboard.doModal()
    
    if not keyboard.isConfirmed():
        xbmcplugin.endOfDirectory(handle=_handle, succeeded=True)
        return

    search_text = keyboard.getText()
    if not search_text:
        xbmcplugin.endOfDirectory(handle=_handle, succeeded=True)
        return

    try:
        response = requests.get('https://mediaklikk.hu/iface/mediaklikk/allPrograms/allMusor.json').json()
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Hiba", "Nem sikerült letölteni a keresési adatokat.")
        xbmcplugin.endOfDirectory(handle=_handle, succeeded=False)
        return

    found_items = []
    query_lower = search_text.lower()

    for block in response:
        label = block.get("label", "").lower()
        desc = [d.lower() for d in block.get("desc", [])]
        url = block.get("url", "").lower()

        if (query_lower in label or
            any(query_lower in d for d in desc) or
            query_lower in url):
            found_items.append(block)
    
    if not found_items:
        xbmcgui.Dialog().ok("Nincs találat", f"Nincs találat a következőre: '{search_text}'.")
        xbmcplugin.endOfDirectory(handle=_handle, succeeded=True)
        return

    for item in found_items:
        title = item.get("label", "")
        href_link = item.get("url", "")
        if href_link.startswith("//"):
            href_link = "https:" + href_link
        
        jpg_link = item.get("icon", "")
        if jpg_link.startswith("//"):
            jpg_link = "https:" + jpg_link
            jpg_link = re.sub(r'-150x150', r'', jpg_link)

        addDirectoryItem(
            name=title,
            query=f'extr_web_page&c_url={href_link}&c_title={title}&jpg_link={jpg_link}',
            icon=jpg_link,
            meta={'title': title},
            isFolder=True
        )

    xbmcplugin.endOfDirectory(handle=_handle, succeeded=True)

def date_picker(selected_date):
    from datetime import datetime, timedelta
    import xbmcgui

    yesterday = (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y')

    dialog = xbmcgui.Dialog()
    date_input = dialog.input(
        heading="Állítsd be a dátumot\n  nap/hónap/év",
        defaultt=yesterday,
        type=xbmcgui.INPUT_DATE
    )

    if date_input:
        date_input = date_input.replace(' ', '').strip()
        try:
            date_input_change = datetime.strptime(date_input, '%d/%m/%Y')
            selected_date = date_input_change.strftime('%Y-%m-%d')
        except ValueError as e:
            xbmcgui.Dialog().notification("Hiba", f"Érvénytelen dátumformátum: {e}", xbmcgui.NOTIFICATION_ERROR)

    return selected_date

def sub_epg_menu():
    addDirectoryItem(u'Médiaklikk epg-ből visszatöltés', 'mediaklikk_epg')
    addDirectoryItem(u'musor.tv epg-ből visszatöltés', 'musor_tv_epg')
    addDirectoryItem(u'Egy teljes nap visszatöltése', 'full_day_back')

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def mediaklikk_epg(station_names, ChannelIds, radio_code):
    radio_data = {'radios':[{'Names':'Kossuth','ChannelIds':'6','radio_code':'mr1',},{'Names':'Petőfi','ChannelIds':'21','radio_code':'mr2',},{'Names':'Bartók','ChannelIds':'12','radio_code':'mr3',},{'Names':'Dankó','ChannelIds':'9','radio_code':'mr7',},{'Names':'Nemzetiségi','ChannelIds':'18','radio_code':'mr4',},{'Names':'Parlamenti','ChannelIds':'15','radio_code':'mr5',},{'Names':'Szakcsi','ChannelIds':'43','radio_code':'mr9',},{'Names':'Csukás Meserádió','ChannelIds':'50','radio_code':'mr10',},{'Names':'Nemzeti Sportrádió','ChannelIds':'47','radio_code':'mr11',}]}
    
    for station in radio_data['radios']:
        station_names = station['Names']
        ChannelIds = station['ChannelIds']
        radio_code = station['radio_code']
        
        addDirectoryItem(station_names, f'extr_mediaklikk_epg&station_names={station_names}&ChannelIds={ChannelIds}&radio_code={radio_code}')

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_mediaklikk_epg(station_names, ChannelIds, radio_code, selected_date, join_title):
    selected_date = date_picker(selected_date)
    if selected_date:
        import requests
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://mediaklikk.hu',
            'Referer': 'https://mediaklikk.hu/musorujsag/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }
        
        data = {
            'ChannelIds': f'{ChannelIds},',
            'Date': f'{selected_date}',
        }
        
        resp = requests.post('https://mediaklikk.hu/wp-content/plugins/hms-global-widgets/widgets/programGuide/programGuideInterface.php', headers=headers, data=data)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        program_items = soup.find_all("li", class_="program_body")
        if program_items:
            date_day = f'{data["Date"]}'
        
            for index, item in enumerate(program_items, start=1):
                time_x = item.find("time").text.strip()
                time_x = re.sub(r':', r'#', time_x)
        
                program_info = item.find("h1").text.strip()
                program_info = re.sub(r'[\\\"]', r'', program_info)
                program_info = re.sub(r'[\\//]', r'#', program_info)
                program_info = re.sub(r':', r'#', program_info)
                program_info = re.sub(r'[!?]', r'#', program_info)
        
                from datetime import datetime, timedelta
        
                program_start = item["data-from"]
                start_date = datetime.strptime(program_start, '%Y-%m-%d %H:%M:%S%z')
                format_start = start_date.strftime('%Y%m%d%H%M%S')
                
                program_end = item["data-till"]
                end_date = datetime.strptime(program_end, '%Y-%m-%d %H:%M:%S%z')
                end_date += timedelta(minutes=2)
                format_end = end_date.strftime('%Y%m%d%H%M%S')
        
                time_difference = round((end_date - start_date).total_seconds() / 60)
        
                url = f'https://hangtar-cdn.connectmedia.hu/{format_start}/{format_end}/{radio_code}.mp3'
        
                join_title = f'{selected_date} {time_x} - {station_names} - {program_info} ({time_difference}p)'
        
                query = f'resolve&url={url}&mediatype=radio'
                addDirectoryItem(
                    f'{join_title}', query, '',
                    meta={'title': f"{join_title}"}, isFolder=False)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def musor_tv_epg(station_names, ChannelIds, radio_code):
    radio_data = {'radios':[{'Names':'Kossuth','ChannelIds':'MR1','radio_code':'mr1',},{'Names':'Petőfi','ChannelIds':'MR2','radio_code':'mr2',},{'Names':'Bartók','ChannelIds':'MR3','radio_code':'mr3',},{'Names':'Dankó','ChannelIds':'DANKO_RADIO','radio_code':'mr7',},{'Names':'Nemzetiségi','ChannelIds':'MR4','radio_code':'mr4',},{'Names':'Duna World','ChannelIds':'DUNAWORLDRADIO','radio_code':'mr8',}]}
    
    for station in radio_data['radios']:
        station_names = station['Names']
        ChannelIds = station['ChannelIds']
        radio_code = station['radio_code']
        
        addDirectoryItem(station_names, f'extr_musor_tv_epg&station_names={station_names}&ChannelIds={ChannelIds}&radio_code={radio_code}')

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)
    
def extr_musor_tv_epg(station_names, ChannelIds, radio_code, selected_date, link, target_title, entry_date, start_time):
    selected_date = date_picker(selected_date)
    selected_date = re.sub(r'-', r'.', str(selected_date))
    if selected_date:
        import requests
        
        headers = {
            'authority': 'musor.tv',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        }
        
        resp = requests.get(f'https://musor.tv/heti/tvmusor/{ChannelIds}/{selected_date}', headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        entries = soup.find_all('div', class_='smartpe_progentry')
        
        for entry in entries:
            content_gmt_date = entry.find('time')['content']
            
            from datetime import datetime, timedelta
        
            content_gmt_date_dt = datetime.strptime(content_gmt_date, '%Y-%m-%dGMT%H:%M:%S')
            content_gmt_date_plus_one_hour = content_gmt_date_dt + timedelta(hours=1)
            form_gmt_date = content_gmt_date_plus_one_hour.strftime('%Y-%m-%d %H:%M:%S')
        
            entry_date = form_gmt_date.split()[0]
        
            if entry_date == selected_date.replace('.', '-'):
                
                start_time = entry.find('time').text.strip()
                link = entry.find('a')['href']
                link = f'https://musor.tv{link}'
                link_id = entry.find('a')['id']
                
                target_title = entry.find('a').text.strip()
                target_title = re.sub(r'[\\\"]', r'', target_title)
                target_title = re.sub(r'[\\//]', r'#', target_title)
                target_title = re.sub(r':', r'#', target_title)
                target_title = re.sub(r'[!?]', r'#', target_title)
                
                query = f'extr_musor_mp3&station_names={station_names}&ChannelIds={ChannelIds}&radio_code={radio_code}&link={link}&target_title={target_title}&entry_date={entry_date}&start_time={start_time}'
                addDirectoryItem(f'{entry_date} - {start_time} - {target_title}', query)

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_musor_mp3(station_names, ChannelIds, radio_code, selected_date, link, target_title, entry_date, start_time):
    from datetime import datetime, timedelta
    import requests
    
    resp_link = requests.get(link, headers=headers).text
    get_end = re.findall(r'-&nbsp;(.*:\d+)&nbsp', str(resp_link))[0].strip()
    
    date_start = f'{entry_date} {start_time}:00'
    parsed_start_date = datetime.strptime(date_start, '%Y-%m-%d %H:%M:%S')
    form_start_date = parsed_start_date.strftime('%Y%m%d%H%M%S')
    
    date_end = f'{entry_date} {get_end}:00'
    end_date = datetime.strptime(date_end, '%Y-%m-%d %H:%M:%S')
    end_date += timedelta(minutes=1)
    form_end_date = end_date.strftime('%Y%m%d%H%M%S')
    
    title = f'{entry_date} {start_time}-{get_end} - {target_title}'

    url = f'https://hangtar-cdn.connectmedia.hu/{form_start_date}/{form_end_date}/{radio_code}.mp3'
    
    query = f'resolve&url={url}&mediatype=radio'
    addDirectoryItem(
        f'{title}', query, '',
        meta={'title': f"{title}"}, isFolder=False)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def full_day_back(station_names, ChannelIds, radio_code):
    radio_data = {'radios':[{'Names':'Kossuth','ChannelIds':'6','radio_code':'mr1',},{'Names':'Petőfi','ChannelIds':'21','radio_code':'mr2',},{'Names':'Bartók','ChannelIds':'12','radio_code':'mr3',},{'Names':'Dankó','ChannelIds':'9','radio_code':'mr7',},{'Names':'Nemzetiségi','ChannelIds':'18','radio_code':'mr4',},{'Names':'Duna World','ChannelIds':'29','radio_code':'mr8',},{'Names':'Parlamenti','ChannelIds':'15','radio_code':'mr5',},{'Names':'Szakcsi','ChannelIds':'43','radio_code':'mr9',},{'Names':'Nemzeti Sportrádió','ChannelIds':'47','radio_code':'mr11',},{'Names':'Csukás Meserádió','ChannelIds':'50','radio_code':'mr10',}]}
    
    for station in radio_data['radios']:
        station_names = station['Names']
        ChannelIds = station['ChannelIds']
        radio_code = station['radio_code']
        
        addDirectoryItem(station_names, f'extr_full_day_back&station_names={station_names}&ChannelIds={ChannelIds}&radio_code={radio_code}')

    
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_full_day_back(station_names, ChannelIds, radio_code, selected_date):
    selected_date = date_picker(selected_date)
    if selected_date:    
        from datetime import datetime, timedelta
        
        date_object = datetime.strptime(selected_date, '%Y-%m-%d')
        current_day_formatted = date_object.strftime('%Y%m%d')
        
        next_day_object = date_object + timedelta(days=1)
        next_day_formatted = next_day_object.strftime('%Y%m%d')
        
        title = f'{selected_date} - {station_names} - Teljes nap'
        
        url = f'https://hangtar-cdn.connectmedia.hu/{current_day_formatted}000000/{next_day_formatted}000000/{radio_code}.mp3'
        
        query = f'resolve&url={url}&mediatype=radio'
        addDirectoryItem(
            f'{title}', query, '',
            meta={'title': f"{title}"}, isFolder=False)
        
    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def media_list(url):
    headers = {'X-Requested-With': 'XMLHttpRequest'}
    ch = client.request(API_URL.format(url), headers=headers)
    channelCodes = [i['ShortCode'] for i in ch.json()]
    result = client.request(API_URL.format('programs'), headers=headers)
    u = 'videos' if url == 'tvchannels' else 'audios'
    for item in result.json():
        if item['Channel'] in channelCodes:
            addDirectoryItem(item['Title'], f"extr_web_page&url={u}&id={item['Id']}")

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def write_json_to_file(data, file_path):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        xbmc.log(f"Hiba a JSON fájl írásakor: {e}", xbmc.LOGERROR)

def read_json_from_file(file_path):
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        xbmc.log(f"Hiba a JSON fájl olvasásakor: {e}", xbmc.LOGERROR)
        return None

def extr_main_site(url):
    all_categories = []
    seen_hashes = set()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        main_page_html = response.text
    except requests.exceptions.RequestException as e:
        xbmcgui.Dialog().ok("Hiba", "Nem sikerült a weboldalt betölteni.")
        return []

    main_page_soup = BeautifulSoup(main_page_html, 'html.parser')
    ajax_loaders = main_page_soup.find_all(class_='ajaxloader')

    for loader in ajax_loaders:
        second_data_url = loader['data-url']
        full_url = urllib.parse.urljoin(BASE_URL, second_data_url)

        try:
            resp_cover_url = requests.get(full_url, headers=headers)
            resp_cover_url.raise_for_status()
            resp_cover_url.encoding = 'utf-8'
            main_cover_html = resp_cover_url.text
        except requests.exceptions.RequestException as e:
            xbmc.log(f"Hiba az aloldal lekérdezésekor: {e}, URL: {full_url}", xbmc.LOGERROR)
            continue
            
        main_cover_soup = BeautifulSoup(main_cover_html, 'html.parser')
        category_containers = main_cover_soup.find_all('div', class_='hh-row-container')
        
        for container in category_containers:
            category_title_tag = container.find('h2', class_='row-title')
            category_title = category_title_tag.text.strip() if category_title_tag and category_title_tag.text.strip() else 'Ismeretlen kategória'
            
            items_data = []
            items = container.find_all('div', class_=re.compile(r'cikk'))
            
            for item in items:
                title_tag = item.find('div', class_='article-title')
                title = title_tag.h1.text.strip() if title_tag and title_tag.h1 else None
                url_tag = item.find('a')
                item_url = url_tag['href'] if url_tag and url_tag.has_attr('href') else None
                
                content_type = "unknown"
                item_classes = item.get('class', [])
                if "video" in item_classes: content_type = "video"
                elif "audio" in item_classes: content_type = "audio"
                elif "musor" in item_classes: content_type = "musor"
                elif "cikk" in item_classes: content_type = "cikk"
                elif item_url:
                    if re.search(r'/video/', item_url): content_type = "video"
                    elif re.search(r'/audio/', item_url): content_type = "audio"
                    elif re.search(r'/musor/', item_url): content_type = "musor"
                
                is_valid_type = False
                if '/radio' in url:
                    if content_type in ["video", "audio", "musor", "cikk"] and title:
                        is_valid_type = True
                else:
                    if content_type in ["video", "audio", "musor"] and title:
                        is_valid_type = True
                
                if is_valid_type:
                    item_hash = hashlib.md5(f'{title}{item_url}'.encode('utf-8')).hexdigest()
                    if item_hash not in seen_hashes:
                        seen_hashes.add(item_hash)
                        
                        image_tag = item.find('div', class_='image-wrapper')
                        image_url = image_tag['data-src'] if image_tag and image_tag.has_attr('data-src') else None

                        full_path = urllib.parse.urlparse(item_url).path.strip('/') if item_url else ""
                        clean_slug = full_path.replace('/', '-')
                        
                        temp_item_data = {
                            "type": content_type,
                            "title": title,
                            "url": urllib.parse.urljoin(BASE_URL, item_url) if item_url else None,
                            "image_url": urllib.parse.urljoin(BASE_URL, image_url) if image_url else None,
                            'slug': clean_slug
                        }
                        items_data.append(temp_item_data)
            
            if items_data:
                all_categories.append({
                    "category_title": category_title,
                    "url": url,
                    "items": items_data
                }) 

    return all_categories

def list_main_categories_from_json(url):
    all_data = extr_main_site(url)
    
    if not all_data:
        xbmcgui.Dialog().ok("Hiba", "Nem sikerült a weboldalról adatokat letölteni.")
        xbmcplugin.endOfDirectory(_handle)
        return

    write_json_to_file(all_data, json_path_file)
    
    try:
        for i, category in enumerate(all_data):
            category_title = category.get('category_title', 'Ismeretlen kategória')
            
            display_title = category_title
            
            query = f'list_items_from_json&category_title={quote_plus(category_title)}&category_index={i}&url={quote_plus(url)}'
            
            addDirectoryItem(name=display_title, query=query, isFolder=True)
        
        xbmcplugin.setContent(_handle, 'videos')
    except Exception as e:
        xbmc.log(f"Hiba a kategóriák listázásakor: {e}", xbmc.LOGERROR)
    finally:
        xbmcplugin.endOfDirectory(_handle)

def list_items_from_json(category_title, category_index, url):
    data = read_json_from_file(json_path_file)
    if not data:
        xbmcgui.Dialog().ok("Hiba", "Nem sikerült beolvasni az adatokat.")
        xbmcplugin.endOfDirectory(_handle)
        return

    try:
        target_category = data[int(category_index)]
        
        if target_category:
            for item in target_category['items']:
                title = item.get('title')
                full_title = item.get('title')
                item_url = item.get('url')
                image_url = item.get('image_url')
                slug = item.get('slug')

                if title and item_url:
                    is_direct_playable = item_url.endswith('.mp3')
                    
                    if is_direct_playable:
                        query = f'resolve&url={item_url}&mediatype=radio'
                        addDirectoryItem(name=title, query=query, isFolder=False, icon=image_url)
                    else:
                        query = ''
                        is_folder = True
                        if item.get('type') == 'video' or '/video/' in item_url:
                            query = f'extr_video&href_link={item_url}&h1_title={title}&jpg_link={image_url}'
                        elif item.get('type') == 'audio' or '/audio/' in item_url:
                            title = slug
                            query = f'extr_radio&href_link={item_url}&h1_title={title}&jpg_link={image_url}'
                        elif item.get('type') in ["musor", "cikk"]:
                            query = f'extr_web_page&c_url={item_url}&c_title={title}&jpg_link={image_url}'

                        addDirectoryItem(name=title, query=query, isFolder=is_folder, icon=image_url)

    except IndexError:
        xbmcgui.Dialog().ok("Hiba", "Nem található kategória ezen a címen.")
    except Exception as e:
        xbmc.log(f"Hiba az elemek listázásakor: {e}", xbmc.LOGERROR)
    finally:
        xbmcplugin.endOfDirectory(_handle)

def extr_web_page(id, c_url, c_title, category_name, h1_title, href_link, jpg_link):
    try:
        short_url = f'https://mediaklikk.hu/?p={id}/'
        resp_head = requests.head(short_url, timeout=5)
        https_url = resp_head.headers['location'].replace('http', 'https')
    except (requests.exceptions.RequestException, KeyError) as e:
        if c_url:
            https_url = c_url.replace('http://', 'https://')
        else:
            return

    if not https_url.startswith('https://'):
        https_url = https_url.replace('http://', 'https://')

    if not https_url.endswith('/'):
        https_url = f'{https_url}/'
    
    try:
        response = requests.get(https_url, headers=headers)
        response.raise_for_status()
        response.encoding = 'utf-8'
        main_page_html = response.text
    except requests.exceptions.RequestException as e:
        xbmc.log(f"Hiba a weboldal lekérdezésekor: {e}", xbmc.LOGERROR)
        return
    
    match = re.search(r"p=(\d+)", main_page_html)
    show_id = match.group(1) if match else ''
    
    main_page_soup = BeautifulSoup(main_page_html, 'html.parser')
    
    final_media_list = []
    found_urls = set()

    def parse_grid_media(container, category_name="", season_name=""):
        articles = container.find_all('div', class_='cikk')
        if not articles:
            articles = container.find_all('article', class_='cikk')
        
        temp_items = []
        seen_titles = {}
    
        for idx, article in enumerate(articles):
            url = article.find('a')['href'] if article.find('a') and article.find('a').has_attr('href') else ''
            
            if re.search(r'/.*galeria.*/|/.*hirek.*/|/.*crew.*/', url):
                continue
                
            media_type = 'audio' if 'radio-audio' in article.get('class', []) else 'video'
            mediatype = 'radio' if media_type == 'audio' else 'tv'
            image_tag = article.find('div', class_='image-wrapper')
            image_src = image_tag['data-src'] if image_tag and image_tag.has_attr('data-src') else ''
            media_id = ''
            if media_type == 'video':
                video_id_tag = article.find('div', class_='video-progress-bar')
                media_id = video_id_tag['data-video-clip-id'] if video_id_tag and video_id_tag.has_attr('data-video-clip-id') else ''
            
            original_title = article.find('h1').text.strip() if article.find('h1') else ''
            date_time_tag = article.find('span', class_='post_time')
            date_time = date_time_tag.text.strip() if date_time_tag else ''
            title = f"{original_title} - {date_time}" if original_title and date_time else original_title
    
            if url:
                full_path = urllib.parse.urlparse(url).path.strip('/') if url else ""
                clean_slug = full_path.replace('/', '-')
    
                item_data = {
                    "category": category_name,
                    "type": media_type,
                    "mediatype": mediatype,
                    "title": title,
                    "original_title": original_title,
                    "url": url,
                    "image_src": image_src,
                    "date_time": date_time,
                    "season_info": season_name,
                    "slug": clean_slug
                }
                if media_type == 'video' and media_id:
                    item_data["video_id"] = media_id
                
                if media_type == 'video':
                    full_title_parts = []
                    if season_name:
                        full_title_parts.append(season_name)
                    if category_name not in ["Ismeretlen kategória", "Teljes adások", "Videók", "Epizódok"]:
                        full_title_parts.append(category_name)         
                    full_title_parts.append(original_title)
                    item_data["full_title"] = " - ".join(full_title_parts)
    
                    pattern = r"^(.*?)\s+-\s+\1\s+-\s+"
                    replacement = r"\1 - "
                    item_data["full_title"] = re.sub(pattern, replacement, item_data["full_title"])
    
                    full_category_title_parts = []
                    if season_name:
                        full_category_title_parts.append(season_name)         
                    if category_name not in ["Ismeretlen kategória", "Teljes adások", "Videók", "Epizódok"]:
                        full_category_title_parts.append(category_name)
                    item_data["full_category_title"] = " - ".join(full_category_title_parts)
                
                temp_items.append(item_data)
                
                if original_title not in seen_titles:
                    seen_titles[original_title] = []
                seen_titles[original_title].append(len(temp_items) - 1)
        
        for item in temp_items:
            original_title = item.get('original_title', '')
            
            if original_title in seen_titles and len(seen_titles[original_title]) > 1:
                item['title'] = item['slug']
            
            if item['url'] not in found_urls:
                final_media_list.append({
                    'category': item.get('category', ''),
                    'type': item.get('type', ''),
                    'mediatype': item.get('mediatype', ''),
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'image_src': item.get('image_src', ''),
                    'date_time': item.get('date_time', ''),
                    'season_info': item.get('season_info', ''),
                    'video_id': item.get('video_id', ''),
                    'full_title': item.get('full_title', ''),
                    'full_category_title': item.get('full_category_title', '')
                })
                found_urls.add(item['url'])
    
    def parse_audio_list_media(container, category_name="", season_name=""):
        audio_items = container.find_all('div', class_='showTip')
        
        temp_items = []
        
        for item in audio_items:
            original_title_elem = item.find('div', class_='TXT')
            original_title = original_title_elem.text.strip() if original_title_elem else ''
            
            date_time_elem = item.find('div', class_='showDate')
            date_time = date_time_elem.text.strip() if date_time_elem else ''
            
            play_button = item.find('a', class_='showPlay')
            if not play_button or not play_button.get('data-play'):
                continue
                
            data_play_url = play_button.get('data-play')
            full_url = f"https://mediaklikk.hu{data_play_url}"
            
            title = f"{original_title} - {date_time}" if original_title and date_time else original_title
    
            item_data = {
                "short_id": id,
                "category": category_name,
                "type": "audio",
                "mediatype": "radio",
                "title": title,
                "url": full_url,
                "date_time": date_time,
                "season_info": season_name,
            }
            temp_items.append(item_data)
        
        for item in temp_items:
            if item.get('url', '') not in found_urls:
                final_media_list.append({
                    'short_id': id,
                    'category': item.get('category', ''),
                    'type': item.get('type', ''),
                    'mediatype': item.get('mediatype', ''),
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'date_time': item.get('date_time', ''),
                    'season_info': item.get('season_info', '')
                })
                found_urls.add(item['url'])
    
    def parse_multiplerow_grid(container, category_name="", season_name=""):
        articles = container.find_all('div', class_='multiplerowCardHolder')
        
        temp_items = []
        seen_titles = {}
        
        for idx, article in enumerate(articles):
            link_tag = article.find('a', class_='multiplerowGridItemLink1')
            if not link_tag:
                continue
            url = link_tag['href'] if link_tag.has_attr('href') else ''
    
            if re.search(r'/.*galeria.*/|/.*hirek.*/|/.*crew.*/', url):
                continue
    
            if url:
                full_path = urllib.parse.urlparse(url).path.strip('/') if url else ""
                clean_slug = full_path.replace('/', '-')
                original_title = article.find('h1', class_='article-title').text.strip() if article.find('h1', class_='article-title') else ''
                image_tag = article.find('div', class_='image-wrapper')
                image_src = image_tag['data-src'] if image_tag and image_tag.has_attr('data-src') else ''
                duration_tag = article.find('p', class_='article-date')
                duration = duration_tag.text.strip() if duration_tag else ''
                title = f"{original_title} - {duration}" if original_title and duration else original_title
    
                media_type = 'video'
                mediatype = 'tv'
    
                item_data = {
                    "category": category_name,
                    "type": media_type,
                    "mediatype": mediatype,
                    "title": title,
                    "original_title": original_title,
                    "url": url,
                    "image_src": image_src,
                    "duration": duration,
                    "date_time": "",
                    "season_info": season_name,
                    "slug": clean_slug
                }
                
                if media_type == 'video':
                    full_title_parts = []
                    if season_name:
                        full_title_parts.append(season_name)
                    if category_name not in ["Ismeretlen kategória", "Teljes adások", "Videók", "Epizódok"]:
                        full_title_parts.append(category_name)         
                    full_title_parts.append(original_title)
                    item_data["full_title"] = " - ".join(full_title_parts)
    
                    pattern = r"^(.*?)\s+-\s+\1\s+-\s+"
                    replacement = r"\1 - "
                    item_data["full_title"] = re.sub(pattern, replacement, item_data["full_title"])
    
                    full_category_title_parts = []
                    if season_name:
                        full_category_title_parts.append(season_name)         
                    if category_name not in ["Ismeretlen kategória", "Teljes adások", "Videók", "Epizódok"]:
                        full_category_title_parts.append(category_name)
                    item_data["full_category_title"] = " - ".join(full_category_title_parts)
    
                temp_items.append(item_data)
                if original_title not in seen_titles:
                    seen_titles[original_title] = []
                seen_titles[original_title].append(len(temp_items) - 1)
        
        for item in temp_items:
            original_title = item.get('original_title', '')
            if original_title in seen_titles and len(seen_titles[original_title]) > 1:
                item['title'] = item['slug']
            if item.get('url', '') not in found_urls:
                final_media_list.append({
                    'category': item.get('category', ''),
                    'type': item.get('type', ''),
                    'mediatype': item.get('mediatype', ''),
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'image_src': item.get('image_src', ''),
                    'duration': item.get('duration', ''),
                    'date_time': item.get('date_time', ''),
                    'season_info': item.get('season_info', ''),
                    'full_title': item.get('full_title', ''),
                    'full_category_title': item.get('full_category_title', '')
                })
                found_urls.add(item['url'])
    

    all_titled_containers = main_page_soup.find_all('div', class_=['tab_content', 'hh-row-container'])
    
    for container in all_titled_containers:
        h2_tag = container.find('h2', class_='row-title')
        media_container = container.find('div', class_='coverGlobalGrid')
        
        if h2_tag and media_container:
            category_name = h2_tag.text.strip()
            parse_grid_media(media_container, category_name=category_name)

    program_attached_content_div = main_page_soup.find('div', class_='program_attached_content')
    if program_attached_content_div:
        global_grid_containers = program_attached_content_div.find_all('div', class_='coverGlobalGrid')
    
        category_name = "Teljes adások"
        season_select_tag = main_page_soup.find('div', class_='season-select-default')
        if season_select_tag:
            category_name = season_select_tag.text.strip()
    
        for media_container in global_grid_containers:
            parse_grid_media(media_container, category_name=category_name)

    audio_list_widgets = main_page_soup.find_all('div', class_='widget_triaudiolist_widget')
    for widget in audio_list_widgets:
        audio_list_container = widget.find('div', id='audioList')
        if audio_list_container:
            category_tag = widget.find('h2', class_='row-title')
            category_name = category_tag.text.strip() if category_tag else 'Rádióadások'
            parse_audio_list_media(audio_list_container, category_name)

    multiplerow_widgets = main_page_soup.find_all('div', class_='widget_multiplerowgrid_widget')
    for widget in multiplerow_widgets:
        multiplerow_container = widget.find('div', class_='coverMultipleGrid')
        if multiplerow_container:
            category_tag = widget.find('h2')
            category_name = category_tag.text.strip() if category_tag else 'Videók'
            parse_multiplerow_grid(multiplerow_container, category_name)

    season_names = {}
    season_options_container = main_page_soup.find('div', class_='season-select-options')
    if season_options_container:
        season_select_options = season_options_container.find_all('div', class_='season-select-option')
    else:
        season_select_options = main_page_soup.find_all('div', class_='season-select-option')
    
    for option in season_select_options:
        season_id = option.get('data-value')
        season_name = option.text.strip()
        if season_id and season_name:
            season_names[season_id] = season_name
    
    ban_this = ["Galéria", "Galériák", "Hírek", "A műsorról"]
    tab_divs = main_page_soup.find_all('div', attrs={'data-tab': True})
    
    for tab_div in tab_divs:
        tab_title_element = tab_div.find('div', class_='tab_title')
        tab_title = tab_title_element.get_text(strip=True) if tab_title_element else 'Ismeretlen kategória'
        
        if tab_title in ban_this:
            continue
    
        tab_id = tab_div.get('data-tab')
        content_id = tab_div.get('data-content-id')
        content_type = tab_div.get('data-content-type')
        season_id = tab_div.get('data-season-id')
        
        if not all([tab_id, content_id, content_type, show_id, season_id]):
            continue
        
        season_name = season_names.get(season_id, '')
    
        post_data = {
            'action': 'render_widget',
            'contentId': content_id,
            'contentType': content_type,
            'tabId': tab_id,
            'showId': show_id,
            'loop': 'false',
            'seasonId': season_id,
        }
        
        try:
            response = requests.post(
                'https://mediaklikk.hu/wp-content/plugins/hms-global-widgets/interfaces/ajaxHandler.php',
                data=post_data,
                headers=headers
            )
            response.raise_for_status()
            
            data_dict = response.json()
            widget_html = data_dict['data']['widget_html']
            soup = BeautifulSoup(widget_html, 'html.parser')
    
            rows = soup.find_all('div', class_='hh-row-container')
            if not rows:
                rows = [soup]
    
            for row in rows:
                category_tag = row.find('h2', class_='row-title')
                category_name = category_tag.text.strip() if category_tag else 'Ismeretlen kategória'
    
                if category_name == 'Ismeretlen kategória':
                    category_name = tab_title if tab_title_element else 'Ismeretlen kategória'
                
                grid_container = row.find('div', class_='coverGlobalGrid')
                if grid_container:
                    parse_grid_media(grid_container, category_name, season_name)
    
                audio_list_container = row.find('div', id='audioList')
                if audio_list_container:
                    parse_audio_list_media(audio_list_container, category_name, season_name)
    
                multiplerow_container = row.find('div', class_='coverMultipleGrid')
                if multiplerow_container:
                    parse_multiplerow_grid(multiplerow_container, category_name, season_name)
    
        except Exception as e:
            pass
    
    for stuffs in final_media_list:
        short_id = stuffs.get('short_id')
        href_link = stuffs.get('url')
        media_type = stuffs.get('mediatype')
        jpg_link = stuffs.get('image_src')
        category_name = stuffs.get('category')
    
        if re.search(r'.mp3', href_link):
            h1_title = stuffs.get('title', 'Nincs cím')
            
            match_from = re.search(r"from=(\d{8}_\d{6})", href_link)
            beginDateFormatted = match_from.group(1).replace("_", "") if match_from else "nincs_meg"
            
            match_channel = re.search(r"channel=(\w+)", href_link)
            stationShortCode = match_channel.group(1) if match_channel else "nincs_meg"
            
            match_dateend = re.search(r"dateend=(\d{8}_\d{6})", href_link)
            endDateFormatted = match_dateend.group(1).replace("_", "") if match_dateend else "nincs_meg"
            
            found_station = next((station for station in radio_station_list if station["stationShortCode"] == stationShortCode), None)
            if found_station:
                found_stationShortId = found_station['stationShortId']
                real_mp3_link = f'https://hangtar-cdn.connectmedia.hu/{beginDateFormatted}/{endDateFormatted}/{found_stationShortId}.mp3'           
            
                query = f'resolve&url={real_mp3_link}&mediatype=radio'
                addDirectoryItem(h1_title, query, '', meta={'title': h1_title}, isFolder=False)
        else:
            if media_type == 'tv':
                c_title = stuffs.get('full_category_title', '')
                h1_title = stuffs.get('full_title', '')
                
                query = f'extr_video&c_url={c_url}&c_title={c_title}&category_name={category_name}&h1_title={h1_title}&href_link={href_link}&jpg_link={jpg_link}'
                addDirectoryItem(h1_title, query, jpg_link, meta={'title': h1_title}, isFolder=True)
            else:
                c_title = stuffs.get('category', '')
                h1_title = stuffs.get('title', 'Nincs cím')
                
                query = f'extr_radio&c_url={c_url}&c_title={c_title}&category_name={category_name}&h1_title={h1_title}&href_link={href_link}&jpg_link={jpg_link}'
                addDirectoryItem(h1_title, query, jpg_link, meta={'title': h1_title}, isFolder=True)
    
    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_video(c_url, c_title, category_name, h1_title, href_link, jpg_link, title, url, mediatype):
    mediatype = 'tv'
    title = h1_title
    response_0 = requests.get(href_link, cookies=cookies, headers=headers).text
    
    try:
        url = re.findall(r'\"token\":\"(.*?)\"', str(response_0))[0].strip()
        
        query = f'resolve&url={url}&mediatype=tv'
        addDirectoryItem(title, query, icon=jpg_link, meta={'title': title}, isFolder=False)
    except IndexError:
        notification = xbmcgui.Dialog()
        notification.notification("Mediaklikk", f"Nem található videó!", time=5000)
    
    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_radio(c_url, c_title, category_name, h1_title, href_link, jpg_link):
    import re
    import requests
    from datetime import datetime, timedelta
    
    mediatype = 'radio'
    title = h1_title

    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://mediaklikk.hu'
    }
    
    def convert_date_format(date_str, delta_seconds=0):
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        date_obj += timedelta(seconds=delta_seconds)
        return date_obj.strftime('%Y%m%d%H%M%S')

    found_station = None
    for station in radio_station_list:
        if station['stationLinkId'] in href_link:
            found_station = station
            break
    
    if found_station:
        radio_name = found_station['stationLinkId']
        radio_station = found_station['stationShortId']
        
        response = requests.get(href_link, headers=headers)
        response.encoding = 'utf-8'
        
        try:
            link_page_html = response.text
            
            beginDate_found = re.findall(r"beginDate: '(\d.*?)',", link_page_html)
            endDate_found = re.findall(r"endDate: '(\d.*?)',", link_page_html)
            
            if beginDate_found and endDate_found:
                beginDate = beginDate_found[0].strip()
                endDate = endDate_found[0].strip()
            
                beginDateFormatted = convert_date_format(beginDate)
                endDateFormatted = convert_date_format(endDate)
                
                url = f'https://hangtar-cdn.connectmedia.hu/{beginDateFormatted}/{endDateFormatted}/{radio_station}.mp3'
            
                query = f'resolve&url={url}&mediatype=radio'
                addDirectoryItem(title, query, icon=jpg_link, meta={'title': title}, isFolder=False)
        except IndexError:
            notification = xbmcgui.Dialog()
            notification.notification("Mediaklikk", f"Nem található rádió adás!", time=5000)
    
    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def audios_extr_web_page(id):
    short_url = f'https://mediaklikk.hu/?p={id}/'
    
    resp_head = requests.head(short_url)
    https_url = resp_head.headers['location'].replace(r'http', r'https')
    https_url = f'{https_url}/'
    
    response = requests.get(https_url, cookies=cookies, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    extracted_data = []

    show_divs = soup.find_all("div", class_="showTip")

    for div in show_divs:
        title = div.find("span").text.strip()
        showLength = div.find("div", class_="showLength").text.strip()
        show_date = div.find("div", class_="showDate").text.strip()
        date_start = div.find("a", class_="showPlay")["data-date"]
        date_end = div.find("a", class_="showPlay")["data-dateend"]
        data_ch = div.find("a", class_="showPlay")["data-ch"]
        data_play_link = div.find("a", class_="showPlay")["data-play"]

        if all([title, showLength, show_date, date_start, date_end, data_ch, data_play_link]):
            extracted_data.append({
                "title": title,
                "showLength": showLength,
                "show_date": show_date,
                "date_start": date_start,
                "date_end": date_end,
                "data_ch": data_ch,
                "data_play_link": data_play_link
            })
    
    for stuffs in extracted_data:
        title = stuffs['title']
        showLength = stuffs['showLength']
        show_date = stuffs['show_date']
        
        date_start = stuffs['date_start']
        date_start = re.sub(r'[\W_]+', r'', date_start)
        
        date_end = stuffs['date_end']
        date_end = re.sub(r'[\W_]+', r'', date_end)
        
        data_ch = stuffs['data_ch']
        
        url = f'https://hangtar-cdn.connectmedia.hu/{date_start}/{date_end}/{data_ch}.mp3'
        
        query = f'resolve&url={url}&mediatype=radio'
        addDirectoryItem(
            f'{show_date} | {title}', query, '',
            meta={'title': f"{show_date} | {title}"}, isFolder=False)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def live_channels():
    from resources.lib import epglist
    channels = [{'title': u'M1', 'url': 'mtv1live', 'icon': 'm1.png', 'type': 'tv', 'epg': '1'},
                {'title': u'M2', 'url': 'mtv2live', 'icon': 'm2.png', 'type': 'tv', 'epg': '2'},
                {'title': u'M3', 'url': '', 'icon': 'm3.png', 'type': 'tv'},

                {'title': u'M4 Sport', 'url': 'mtv4live', 'icon': 'm4 sport.png', 'type': 'tv', 'epg': '30'},
                {'title': u'M4 Sport (1)', 'url': 'm4sport1', 'icon': 'm4 sport.png', 'type': 'tv', 'epg': '37'},
                {'title': u'M4 Sport (2)', 'url': 'm4sport2', 'icon': 'm4 sport.png', 'type': 'tv', 'epg': '38'},
                {'title': u'M4 Sport (3)', 'url': 'm4sport3', 'icon': 'm4 sport.png', 'type': 'tv', 'epg': '39'},
                {'title': u'M4 Sport (4)', 'url': 'm4sport4', 'icon': 'm4 sport.png', 'type': 'tv', 'epg': '40'},
                {'title': u'M4 Sport (5)', 'url': 'm4sport5', 'icon': 'm4 sport.png', 'type': 'tv', 'epg': '41'},

                {'title': u'M4 Sport +', 'url': 'mtv4plus', 'icon': 'm4 sport.png', 'type': 'tv', 'epg': '34'},
                {'title': u'M5', 'url': 'mtv5live', 'icon': 'm5.png', 'type': 'tv', 'epg': '33'},
                {'title': u'Duna', 'url': 'dunalive', 'icon': 'duna.png', 'type': 'tv', 'epg': '3'},
                {'title': u'Duna World', 'url': 'dunaworldlive', 'icon': 'duna world.png', 'type': 'tv', 'epg': '4'},

                {'title': u'Nemzeti Sportrádió', 'url': 'nss', 'icon': 'nsr.png', 'type': 'tv', 'epg': '47'},
                {'title': u'Kossuth Rádió', 'url': '/kossuth-radio-elo/', 'icon': 'kossuth.png', 'type': 'radio'},
                {'title': u'Petőfi Rádió', 'url': '/petofi-radio-elo', 'icon': 'petofi.png', 'type': 'radio'},
                {'title': u'Bartók Rádió', 'url': '/bartok-radio-elo/', 'icon': 'bartok.png', 'type': 'radio'},
                {'title': u'Dankó Rádió', 'url': '/danko-radio-elo', 'icon': 'danko.png', 'type': 'radio'},
                {'title': u'Nemzetiségi Rádió', 'url': '/nemzetisegi-adasok-elo/', 'icon': 'nemzetisegi.png', 'type': 'radio'},
                {'title': u'Parlamenti Rádió', 'url': '/parlamenti-adasok-elo', 'icon': 'parlamenti.png', 'type': 'radio'},
                {'title': u'Duna World Rádió', 'url': '/duna-world-radio-elo/', 'icon': 'duna world.png', 'type': 'radio'}]

    for channel in channels:
        display_title = channel['title']
        original_title = channel['title']
        
        if 'epg' in channel and __addon__.getSetting('showepg') == 'true':
            if hasattr(epglist, 'get_epg'):
                try:
                    full_epg_title = epglist.get_epg(channel['title'], channel['epg'], active=True)
                    if "  |  " in full_epg_title:
                        parts = full_epg_title.split("  |  ")
                        original_title = parts[0]
                        display_title = full_epg_title
                    else:
                        display_title = full_epg_title
                except Exception as e:
                    xbmc.log(f"Error getting EPG for {channel['title']}: {e}", xbmc.LOGERROR)

        addDirectoryItem(
            f"{display_title}",
            f"resolve&url={channel['url']}&mediatype={channel['type']}&title={quote_plus(display_title)}|{quote_plus(original_title)}",
            icon=os.path.join(MediaDir, channel['icon']),
            meta={'title': display_title},
            isFolder=False
        )

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def resolve(title, url, mediatype):
    play_item = xbmcgui.ListItem()
    streamURL = None

    if '|' in title:
        display_title, original_title = title.split('|')
        display_title = unquote_plus(display_title)
        original_title = unquote_plus(original_title)
    else:
        display_title = title
        original_title = title

    if mediatype == 'radio':
        type = 'video'
        if url.startswith('http'):
            streamURL = url
        else:
            try:
                r = client.request(BASE_URL + url)
                streamURL = re.search(r"""radioStreamUrl\s*=\s*['"]([^'"]+)""", r.text).group(1)
            except Exception as e:
                return xbmcplugin.setResolvedUrl(_handle, False, listitem=play_item)

    elif mediatype == 'tv':
        type = 'video'
        if original_title == 'M3':
            try:
                headers = {
                    'user-agent': f'{client.get_user_agent}',
                }
                
                streamData = requests.get('https://nemzetiarchivum.hu/api/m3/v3/stream?target=live&type=m3', headers=headers).json()
                
                license_key = (
                    f"https://nemzetiarchivum.hu/{streamData['proxy_url']}?drm-type=widevine&type=m3"
                    f"|User-Agent={client.get_user_agent}|R{{SSM}}|"
                )
                
                DRM = 'com.widevine.alpha'
                PROTOCOL = 'mpd'
                KODI_VERSION_MAJOR = int(xbmc.getInfoLabel('System.BuildVersion').split('.')[0])
            
                from inputstreamhelper import Helper
                is_helper = Helper(PROTOCOL)
            
                if is_helper.check_inputstream():
                    play_item = xbmcgui.ListItem(path=streamData['mpeg_dash']['url'])
                    play_item.setProperty('inputstream', is_helper.inputstream_addon if KODI_VERSION_MAJOR >= 19 else 'inputstreamaddon')
                    play_item.setProperty('inputstream.adaptive.manifest_type', PROTOCOL)
                    play_item.setProperty('inputstream.adaptive.license_type', DRM)
                    play_item.setProperty('inputstream.adaptive.license_key', license_key)
                    play_item.setProperty('inputstream.adaptive.stream_headers', f"User-Agent={client.get_user_agent}")
                    play_item.setProperty('inputstream.adaptive.manifest_headers', f"User-Agent={client.get_user_agent}")
                    
                    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)
                    return
            except Exception as e:
                xbmc.log(f"M3 stream Error: {e}", xbmc.LOGINFO)
                return xbmcplugin.setResolvedUrl(_handle, False, listitem=play_item)
        else:
            try:
                resp = client.request(f'https://player.mediaklikk.hu/playernew/player.php?noflash=yes&video={quote_plus(url)}').text
                json_regex_patt = r"setup\((.*?)\);"
                json_text = re.search(json_regex_patt, resp, re.DOTALL).group(1)
                norm_json = json.loads(json_text)

                if norm_json:
                    play_entry = next((x for x in norm_json["playlist"] if "bumper" not in x["file"]), None)
                    streamURL = play_entry["file"] if play_entry and play_entry["type"] == "hls" else norm_json['playlist'][0]['file']
            except Exception as e:
                xbmc.log(f"TV Error: {e}", xbmc.LOGINFO)

    if not streamURL:
        return xbmcplugin.setResolvedUrl(_handle, False, listitem=play_item)

    if streamURL.startswith('//'):
        streamURL = 'https:' + streamURL
    
    play_item.setLabel(display_title)
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
id = params.get('id')
mediatype = params.get('mediatype')

c_url = params.get('c_url')
c_title = params.get('c_title')

category_name = params.get('category_name')
h1_title = params.get('h1_title')
href_link = params.get('href_link')
jpg_link = params.get('jpg_link')

station_names = params.get('station_names')
ChannelIds = params.get('ChannelIds')
radio_code = params.get('radio_code')
selected_date = params.get('selected_date')
join_title = params.get('join_title')

target_title = params.get('target_title')
link = params.get('link')

entry_date = params.get('entry_date')
start_time = params.get('start_time')

category_title = params.get('category_title')
category_index = params.get('category_index')

if not action:
    main_folders()
elif action == 'list_main_categories_from_json':
    list_main_categories_from_json(url)
elif action == 'list_items_from_json':
    if category_title and category_index and url:
        list_items_from_json(unquote_plus(category_title), category_index, unquote_plus(url))
elif action == 'media_list':
    media_list(url)
elif action == 'live' :
    live_channels()
elif action == 'resolve':
    resolve(title, url, mediatype)
elif action == 'extr_web_page':
    extr_web_page(id, c_url, c_title, category_name, h1_title, href_link, jpg_link)
elif action == 'audios_extr_web_page':
    audios_extr_web_page(id)
elif action == 'extr_video':
    extr_video(c_url, c_title, category_name, h1_title, href_link, jpg_link, title, url, mediatype)
elif action == 'extr_radio':
    extr_radio(c_url, c_title, category_name, h1_title, href_link, jpg_link)
elif action == 'sub_epg_menu':
    sub_epg_menu()
elif action == 'date_picker':
    date_picker(selected_date)
elif action == 'mediaklikk_epg':
    mediaklikk_epg(station_names, ChannelIds, radio_code)
elif action == 'extr_mediaklikk_epg':
    extr_mediaklikk_epg(station_names, ChannelIds, radio_code, selected_date, join_title)
elif action == 'musor_tv_epg':
    musor_tv_epg(station_names, ChannelIds, radio_code)
elif action == 'extr_musor_tv_epg':
    extr_musor_tv_epg(station_names, ChannelIds, radio_code, selected_date, link, target_title, entry_date, start_time)
elif action == 'extr_musor_mp3':
    extr_musor_mp3(station_names, ChannelIds, radio_code, selected_date, link, target_title, entry_date, start_time)
elif action == 'full_day_back':
    full_day_back(station_names, ChannelIds, radio_code)
elif action == 'extr_full_day_back':
    extr_full_day_back(station_names, ChannelIds, radio_code, selected_date)
elif action == 'search':
    search()
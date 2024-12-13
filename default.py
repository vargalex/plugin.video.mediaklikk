# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals
from kodi_six import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import re, os, json, sys
from resources.lib import client

import requests
from bs4 import BeautifulSoup

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

cookies = {
    'SERVERID': 'mtvacookieD',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

def main_folders():
    addDirectoryItem(u'ÉLŐ', 'live')
    addDirectoryItem(u'TV műsorok A-Z', 'media_list&url=tvchannels')
    addDirectoryItem(u'Rádió műsorok A-Z', 'media_list&url=radiochannels')
    addDirectoryItem(u'epg-ből visszatöltés (rádiók)', 'sub_epg_menu')

    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def date_picker(selected_date):
    from datetime import datetime

    dialog = xbmcgui.Dialog()
    date_input = dialog.input(
        heading="Állítsd be a dátumot\n  nap/hónap/év",
        defaultt="",
        type=xbmcgui.INPUT_DATE)

    if date_input:
        date_input_change = datetime.strptime(date_input, '%d/%m/%Y')
        selected_date = date_input_change.strftime('%Y-%m-%d')
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
                    meta={'Title': f"{join_title}"}, isFolder=False)

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
        meta={'Title': f"{title}"}, isFolder=False)

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
            meta={'Title': f"{title}"}, isFolder=False)

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
            if url == 'tvchannels':
                addDirectoryItem(item['Title'], f"extr_web_page&url={u}&id={item['Id']}")
            else:
                addDirectoryItem(item['Title'], f"audios_extr_web_page&url={u}&id={item['Id']}")

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_web_page(id, c_url, c_title, category_name, h1_title, href_link, jpg_link):
    short_url = f'https://mediaklikk.hu/?p={id}/'

    resp_head = requests.head(short_url)
    https_url = resp_head.headers['location'].replace(r'http', r'https')
    https_url = f'{https_url}/'

    excluded_menu_ids = ['7378970', '7378976', '7378955', '7378958', '7378967',
                         '35', '943334', '943336', '3129072', '757092', '757095',
                         '757098', '757101', '4048045', '897387', '757082', '757085',
                         '757089', '757113', '757076', '757079', '7397729', '757107',
                         '757110', '7170004', '7587452', '757104', '801369', '757116',
                         '7043419', '7072192', '7078108', '7087711']

    response = requests.get(https_url, cookies=cookies, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    if re.search(r'/iface/cover/', str(soup)):

        result = []
        seen_menu_ids = set()

        menu_items = soup.find_all('li', id=lambda x: x and x.startswith('menu-item-'))
        for item in menu_items:
            menu_id = item['id'].split('-')[-1]
            if menu_id in excluded_menu_ids or menu_id in seen_menu_ids:
                continue
            link = item.find('a')
            if link and 'href' in link.attrs:
                title = link.text.strip()
                url = link['href'].strip()
                if url.startswith('http'):
                    result.append({
                        'menu_item': menu_id,
                        'title': title,
                        'url': url
                    })
                    seen_menu_ids.add(menu_id)

        if result:
            for entry in result:
                
                c_title = entry['title']
                c_url = entry['url']

                query = f'extr_cover_page&c_url={c_url}&c_title={c_title}'
                addDirectoryItem(c_title, query, '', meta={'Title': c_title}, isFolder=True)

        else:
            first_cover = re.findall(r'data-url=\"/iface/cover/(.*?)\"', str(soup))[0].strip()
            first_cover_url = f'https://mediaklikk.hu/iface/cover/{first_cover}'

            cover_response = requests.get(first_cover_url, cookies=cookies, headers=headers)
            cover_response.encoding = 'utf-8'

            soup_2 = BeautifulSoup(cover_response.text, 'html.parser')

            menu = soup_2.find('div', class_='broadcastPageHeaderContentMenu')
            if menu:
                links = menu.find_all('a')
                data = []
                for link in links:
                    title = link.text.strip()
                    href = link['href']
                    data.append({'title': title, 'link': href})

                for item in data:
                    c_title = item['title']
                    c_url = item['link']

                    query = f'extr_no_cover_no_page&c_url={c_url}&c_title={c_title}'
                    addDirectoryItem(c_title, query, '', meta={'Title': c_title}, isFolder=True)

            if soup_2.find_all('div', class_='multiplerowCardHolder'):
                extracted_data = []

                current_category = None
                widgets = soup_2.find_all('div', class_='widget')
                for widget in widgets:
                    header_h2 = widget.find('h2')
                    if header_h2:
                        current_category = header_h2.text.strip()

                    items = widget.find_all('div', class_='multiplerowCardHolder')
                    for item in items:
                        h1_title = item.find('h1', class_='article_title') or item.find('h1', class_='article-title')
                        h1_title_text = h1_title.text.strip() if h1_title else None
                        h1_title_text = re.sub(r'&', '§', h1_title_text)

                        a_tag = (
                            item.find('a', class_='multiplerowGridItemLink1')
                            or item.find('a', class_='multiplerowGridItemLink2')
                            or item.find('a', class_='accessibilityShowWhenWCAG')
                            or item.find('a')
                        )
                        if a_tag:
                            a_href_link = (
                                a_tag.get('href') if a_tag and a_tag.has_attr('href')
                                else re.search(r"location\.href\s*=\s*['\"](.*?)['\"]", a_tag.get('onclick', ''))
                            )
                            a_href_link = a_href_link.group(1) if isinstance(a_href_link, re.Match) else a_href_link
                            if a_href_link and '/galeria/' in a_href_link:
                                continue

                        image_div = item.find('div', class_='image-wrapper')
                        dot_jpg_link = None
                        if image_div:
                            data_src = image_div.get('data-src', '')
                            style = image_div.get('style', '')
                            dot_jpg_link = re.search(r'(http.*\.[pj][pn]g)', data_src or style)
                            dot_jpg_link = dot_jpg_link.group(1) if dot_jpg_link else None

                        if current_category and h1_title_text and a_href_link and dot_jpg_link:
                            extracted_data.append({
                                'header_h2_tag_category_name': current_category,
                                'h1_title': h1_title_text,
                                'a_href_link': a_href_link,
                                'dot_jpg_link': dot_jpg_link
                            })

                for stuffs in extracted_data:
                    category_name = stuffs['header_h2_tag_category_name']
                    h1_title = stuffs['h1_title']
                    href_link = stuffs['a_href_link']
                    jpg_link = stuffs['dot_jpg_link']

                    query = f'extr_video&c_url={c_url}&c_title={c_title}&category_name={category_name}&h1_title={h1_title}&href_link={href_link}&jpg_link={jpg_link}'
                    addDirectoryItem(
                        f'{f"{c_title} | " if c_title else ""}{category_name} | {h1_title}', query, jpg_link,
                        meta={'Title': c_title if c_title else f'{category_name} | {h1_title}'}, isFolder=True)

    else:
        extracted_data = []

        current_category = None
        widgets = soup.find_all('div', class_='widget')
        for widget in widgets:
            header_h2 = widget.find('h2')
            if header_h2:
                current_category = header_h2.text.strip()

            items = widget.find_all('div', class_='multiplerowCardHolder')
            for item in items:
                h1_title = item.find('h1', class_='article_title') or item.find('h1', class_='article-title')
                h1_title_text = h1_title.text.strip() if h1_title else None
                h1_title_text = re.sub(r'&', '§', h1_title_text)

                a_tag = (
                    item.find('a', class_='multiplerowGridItemLink1')
                    or item.find('a', class_='multiplerowGridItemLink2')
                    or item.find('a', class_='accessibilityShowWhenWCAG')
                    or item.find('a')
                )
                if a_tag:
                    a_href_link = (
                        a_tag.get('href') if a_tag and a_tag.has_attr('href')
                        else re.search(r"location\.href\s*=\s*['\"](.*?)['\"]", a_tag.get('onclick', ''))
                    )
                    a_href_link = a_href_link.group(1) if isinstance(a_href_link, re.Match) else a_href_link
                    if a_href_link and '/galeria/' in a_href_link:
                        continue

                image_div = item.find('div', class_='image-wrapper')
                dot_jpg_link = None
                if image_div:
                    data_src = image_div.get('data-src', '')
                    style = image_div.get('style', '')
                    dot_jpg_link = re.search(r'(http.*\.[pj][pn]g)', data_src or style)
                    dot_jpg_link = dot_jpg_link.group(1) if dot_jpg_link else None

                if current_category and h1_title_text and a_href_link and dot_jpg_link:
                    extracted_data.append({
                        'header_h2_tag_category_name': current_category,
                        'h1_title': h1_title_text,
                        'a_href_link': a_href_link,
                        'dot_jpg_link': dot_jpg_link
                    })

        for stuffs in extracted_data:
            category_name = stuffs['header_h2_tag_category_name']
            h1_title = stuffs['h1_title']
            href_link = stuffs['a_href_link']
            jpg_link = stuffs['dot_jpg_link']

            query = f'extr_video&c_url={c_url}&c_title={c_title}&category_name={category_name}&h1_title={h1_title}&href_link={href_link}&jpg_link={jpg_link}'
            addDirectoryItem(
                f'{f"{c_title} | " if c_title else ""}{category_name} | {h1_title}', query, jpg_link,
                meta={'Title': c_title if c_title else f'{category_name} | {h1_title}'}, isFolder=True)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_video(c_url, c_title, category_name, h1_title, href_link, jpg_link, title, url, mediatype):
    mediatype = 'tv'
    title = h1_title
    response_0 = requests.get(href_link, cookies=cookies, headers=headers).text

    try:
        url = re.findall(r'\"token\":\"(.*?)\"', str(response_0))[0].strip()

        query = f'resolve&url={url}&mediatype=tv'
        addDirectoryItem(title, query, icon=jpg_link, meta={'Title': title}, isFolder=False)
    except IndexError:
        notification = xbmcgui.Dialog()
        notification.notification("Mediaklikk", f"Nem található videó!", time=5000)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_cover_page(c_url, c_title):
    response = requests.get(c_url, cookies=cookies, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    cover = re.findall(r'data-url=\"/iface/cover/(.*?)\"', str(soup))[0].strip()
    cover_url = f'https://mediaklikk.hu/iface/cover/{cover}'

    cover_response = requests.get(cover_url, cookies=cookies, headers=headers)
    cover_response.encoding = 'utf-8'

    soup_2 = BeautifulSoup(cover_response.text, 'html.parser')

    extracted_data = []

    current_category = None
    widgets = soup_2.find_all('div', class_='widget_multiplerowgrid_widget') or soup_2.find_all('div', class_='row-title-container')
    for widget in widgets:
        header_h2 = widget.find('h2')
        if header_h2:
            current_category = header_h2.text.strip()

        items = widget.find_all('div', class_='multiplerowCardHolder')
        for item in items:
            h1_title = item.find('h1', class_='article-title')
            h1_title_text = h1_title.text.strip() if h1_title else None
            h1_title_text = re.sub(r'&', '§', h1_title_text)

            a_tag = (
                item.find('a', class_='multiplerowGridItemLink1')
                or item.find('a', class_='multiplerowGridItemLink2')
                or item.find('a', class_='accessibilityShowWhenWCAG')
                or item.find('a')
            )

            a_href_link = None
            if a_tag:
                a_href_link = a_tag.get('href')

                if not a_href_link and a_tag.get('onclick'):
                    onclick_content = a_tag.get('onclick', '')
                    match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick_content)
                    if match:
                        a_href_link = match.group(1)

            if a_href_link and '/galeria/' in a_href_link:
                continue

            image_div = item.find('div', class_='image-wrapper')
            dot_jpg_link = None
            if image_div:
                data_src = image_div.get('data-src', '')
                style = image_div.get('style', '')
                dot_jpg_link = re.search(r'(http.*\.[pj][pn]g)', data_src or style)
                dot_jpg_link = dot_jpg_link.group(1) if dot_jpg_link else None

            if h1_title_text and a_href_link and dot_jpg_link:
                extracted_data.append({
                    'header_h2_tag_category_name': current_category,
                    'h1_title': h1_title_text,
                    'a_href_link': a_href_link,
                    'dot_jpg_link': dot_jpg_link
                })

    for stuffs in extracted_data:
        category_name = stuffs['header_h2_tag_category_name']
        h1_title = stuffs['h1_title']
        href_link = stuffs['a_href_link']
        jpg_link = stuffs['dot_jpg_link']

        query = f'extr_video&id={id}&c_url={c_url}&c_title={c_title}&category_name={category_name}&h1_title={h1_title}&href_link={href_link}&jpg_link={jpg_link}'
        addDirectoryItem(
            f'{f"{c_title} | " if c_title else ""}{category_name} | {h1_title}', query, jpg_link,
            meta={'Title': c_title if c_title else f'{category_name} | {h1_title}'}, isFolder=True)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def extr_no_cover_no_page(c_url, c_title):
    response = requests.get(c_url, cookies=cookies, headers=headers)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'html.parser')

    extracted_data = []

    current_category = None
    widgets = soup.find_all('div', class_='widget')
    for widget in widgets:
        header_h2 = widget.find('h1', class_='super-title') or widget.find('h2')
        if header_h2:
            current_category = header_h2.text.strip()

        items = widget.find_all('div', class_='multiplerowCardHolder')
        for item in items:
            h1_title = item.find('h1', class_='article-title') or item.find('h1', class_='article_title')
            h1_title_text = h1_title.text.strip() if h1_title else None
            h1_title_text = re.sub(r'&', '§', h1_title_text)

            a_tag = (
                item.find('a', class_='multiplerowGridItemLink1')
                or item.find('a', class_='multiplerowGridItemLink2')
                or item.find('a', class_='accessibilityShowWhenWCAG')
                or item.find('a')
            )
            a_href_link = None
            if a_tag:
                a_href_link = (
                    a_tag.get('href')
                    or re.search(r"location\.href\s*=\s*['\"](.*?)['\"]", a_tag.get('onclick', ''))
                )
                a_href_link = a_href_link.group(1) if isinstance(a_href_link, re.Match) else a_href_link

            if a_href_link and '/galeria/' in a_href_link:
                continue

            image_div = item.find('div', class_='image-wrapper')
            dot_jpg_link = None
            if image_div:
                dot_jpg_link = image_div.get('data-src')
                if not dot_jpg_link:
                    style = image_div.get('style', '')
                    match = re.search(r'background-image:\s*url\([\'"]?(.*?)[\'"]?\);', style)
                    dot_jpg_link = match.group(1) if match else None

            if current_category and h1_title_text and a_href_link and dot_jpg_link:
                extracted_data.append({
                    'header_h2_tag_category_name': current_category,
                    'h1_title': h1_title_text,
                    'a_href_link': a_href_link,
                    'dot_jpg_link': dot_jpg_link
                })

    for stuffs in extracted_data:
        category_name = stuffs['header_h2_tag_category_name']
        h1_title = stuffs['h1_title']
        href_link = stuffs['a_href_link']
        jpg_link = stuffs['dot_jpg_link']

        query = f'extr_video&c_url={c_url}&c_title={c_title}&category_name={category_name}&h1_title={h1_title}&href_link={href_link}&jpg_link={jpg_link}'
        addDirectoryItem(f'{category_name} | {h1_title}', query, jpg_link, meta={'Title': c_title}, isFolder=True)

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
            meta={'Title': f"{show_date} | {title}"}, isFolder=False)

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
        if 'epg' in channel and __addon__.getSetting('showepg') == 'true':
            try: title = epglist.get_epg(channel['title'], channel['epg'], active=True)
            except: title = channel['title']
        else:
            title = channel['title']
        addDirectoryItem(title, 'resolve&url={0}&mediatype={1}&title={2}'.format(channel['url'], channel['type'], channel['title']), icon=os.path.join(MediaDir, channel['icon']), meta={'Title': channel['title']}, isFolder=False)

    xbmcplugin.setContent(_handle, 'videos')
    xbmcplugin.endOfDirectory(_handle, cacheToDisc=False)

def resolve(title, url, mediatype):
    play_item = xbmcgui.ListItem()
    streamURL = None

    if mediatype == 'radio':
        type = 'video'
        if url.startswith('http'):
            streamURL = url
        else:
            try:
                r = client.request(BASE_URL + url)
                streamURL = re.search(r"""radioStreamUrl\s*=\s*['"]([^'"]+)""", r.text).group(1)
            except Exception as e:
                xbmc.log(f"radio Error : {e}", xbmc.LOGINFO)
                return xbmcplugin.setResolvedUrl(_handle, False, listitem=play_item)

    elif mediatype == 'tv':
        type = 'video'
        if title == 'M3':
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

if not action:
    main_folders()
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
elif action == 'extr_cover_page':
    extr_cover_page(c_url, c_title)
elif action == 'extr_video':
    extr_video(c_url, c_title, category_name, h1_title, href_link, jpg_link, title, url, mediatype)
elif action == 'extr_no_cover_no_page':
    extr_no_cover_no_page(c_url, c_title)
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
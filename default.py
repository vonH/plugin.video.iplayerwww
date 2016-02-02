# -*- coding: utf-8 -*-

from __future__ import division

import datetime
import os
import re
import sys
import time
import urllib
from operator import itemgetter
import requests
from requests.packages import urllib3
import cookielib
import json
import HTMLParser

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

__addonid__ = "plugin.video.iplayerwww"
__plugin_handle__ = int(sys.argv[1])

def translation(id):
    return xbmcaddon.Addon(__addonid__).getLocalizedString(id)

def GetAddonInfo():
    addon_info = {}
    addon_info["id"] = __addonid__
    addon_info["addon"] = xbmcaddon.Addon(__addonid__)
    addon_info["language"] = addon_info["addon"].getLocalizedString
    addon_info["version"] = addon_info["addon"].getAddonInfo("version")
    addon_info["path"] = addon_info["addon"].getAddonInfo("path")
    addon_info["profile"] = xbmc.translatePath(addon_info["addon"].getAddonInfo('profile'))
    return addon_info


__addoninfo__ = GetAddonInfo()
ADDON = xbmcaddon.Addon(id='plugin.video.iplayerwww')
DIR_USERDATA = xbmc.translatePath(__addoninfo__["profile"])
cookie_jar = None


if(not os.path.exists(DIR_USERDATA)):
    os.makedirs(DIR_USERDATA)

def CATEGORIES():
    if content_type == "video":
        AddMenuEntry(translation(31000), 'iplayer', 106, '', '', '')
        AddMenuEntry(translation(31017), 'url', 109, '', '', '')
        AddMenuEntry(translation(31001), 'url', 105, '', '', '')
        AddMenuEntry(translation(31002), 'url', 102, '', '', '')
        AddMenuEntry(translation(31003), 'url', 103, '', '', '')
        AddMenuEntry(translation(31004), 'url', 104, '', '', '')
        AddMenuEntry(translation(31005), 'url', 101, '', '', '')
        AddMenuEntry(translation(31006), 'url', 107, '', '', '')
        AddMenuEntry(translation(31007), 'url', 108, '', '', '')
    else:
        AddMenuEntry("Live Radio", 'url', 113, '', '', '')
        AddMenuEntry("Radio A-Z", 'url', 112, '', '', '')
        AddMenuEntry("Radio Genres", 'url', 114, '', '', '')
        AddMenuEntry("Radio Search", 'url', 115, '', '', '')
        AddMenuEntry("Radio Most Popular", 'url', 116, '', '', '')


# ListLive creates menu entries for all live channels.
def ListLive():
    channel_list = [
        ('bbc_one_hd', 'bbc_one', 'BBC One'),
        ('bbc_two_hd', 'bbc_two', 'BBC Two'),
        ('bbc_three_hd', 'bbc_three', 'BBC Three'),
        ('bbc_four_hd', 'bbc_four', 'BBC Four'),
        ('cbbc_hd', 'cbbc', 'CBBC'),
        ('cbeebies_hd', 'cbeebies', 'CBeebies'),
        ('bbc_news24', 'bbc_news24', 'BBC News Channel'),
        ('bbc_parliament', 'bbc_parliament', 'BBC Parliament'),
        ('bbc_alba', 'bbc_alba', 'Alba'),
        ('s4cpbs', 's4c', 'S4C'),
        ('bbc_one_london', 'bbc_one', 'BBC One London'),
        ('bbc_one_scotland_hd', 'bbc_one_scotland', 'BBC One Scotland'),
        ('bbc_one_northern_ireland_hd', 'bbc_one_northern_ireland', 'BBC One Northern Ireland'),
        ('bbc_one_wales_hd', 'bbc_one_wales', 'BBC One Wales'),
        ('bbc_two_scotland', 'bbc_two', 'BBC Two Scotland'),
        ('bbc_two_northern_ireland_digital', 'bbc_two', 'BBC Two Northern Ireland'),
        ('bbc_two_wales_digital', 'bbc_two', 'BBC Two Wales'),
    ]
    for id, img, name in channel_list:
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
        if ADDON.getSetting('streams_autoplay') == 'true':
            AddMenuEntry(name, id, 203, iconimage, '', '')
        else:
            AddMenuEntry(name, id, 123, iconimage, '', '')

            
def RadioListLive():
    channel_list = [
        ('bbc_radio_one', 'BBC Radio 1'),
        ('bbc_1xtra', 'BBC Radio 1Xtra'),
        ('bbc_radio_two', 'BBC Radio 2'),
        ('bbc_radio_three', 'BBC Radio 3'),
        ('bbc_radio_fourfm', 'BBC Radio 4'),
        ('bbc_radio_four_extra', 'BBC Radio 4 Extra'),
        ('bbc_radio_five_live', 'BBC Radio 5 live'),
        ('bbc_radio_five_live_sports_extra', 'BBC Radio 5 live sports extra'),
        ('bbc_6music', 'BBC Radio 6 Music'),
        ('bbc_asian_network', 'BBC Asian Network'),
        ('bbc_radio_scotland_fm', 'BBC Radio Scotland'),
        ('bbc_radio_nan_gaidheal', u'BBC Radio nan Gàidheal'),
        ('bbc_radio_ulster', 'BBC Radio Ulster'),
        ('bbc_radio_foyle', 'BBC Radio Foyle'),
        ('bbc_radio_wales_fm', 'BBC Radio Wales'),
        ('bbc_radio_cymru', 'BBC Radio Cymru'),
        ('bbc_radio_berkshire', 'BBC Radio Berkshire'),
        ('bbc_radio_bristol', 'BBC Radio Bristol'),
        ('bbc_radio_cambridge', 'BBC Radio Cambridgeshire'),
        ('bbc_radio_cornwall', 'BBC Radio Cornwall'),
        ('bbc_radio_coventry_warwickshire', 'BBC Coventry & Warwickshire'),
        ('bbc_radio_cumbria', 'BBC Radio Cumbria'),
        ('bbc_radio_derby', 'BBC Radio Derby'),
        ('bbc_radio_devon', 'BBC Radio Devon'),
        ('bbc_radio_essex', 'BBC Essex'),
        ('bbc_radio_gloucestershire', 'BBC Radio Gloucestershire'),
        ('bbc_radio_guernsey', 'BBC Radio Guernsey'),
        ('bbc_radio_hereford_worcester', 'BBC Hereford & Worcester'),
        ('bbc_radio_humberside', 'BBC Radio Humberside'),
        ('bbc_radio_jersey', 'BBC Radio Jersey'),
        ('bbc_radio_kent', 'BBC Radio Kent'),
        ('bbc_radio_lancashire', 'BBC Radio Lancashire'),
        ('bbc_radio_leeds', 'BBC Radio Leeds'),
        ('bbc_radio_leicester', 'BBC Radio Leicester'),
        ('bbc_radio_lincolnshire', 'BBC Radio Lincolnshire'),
        ('bbc_london', 'BBC Radio London'),
        ('bbc_radio_manchester', 'BBC Radio Manchester'),
        ('bbc_radio_merseyside', 'BBC Radio Merseyside'),
        ('bbc_radio_newcastle', 'BBC Newcastle'),
        ('bbc_radio_norfolk', 'BBC Radio Norfolk'),
        ('bbc_radio_northampton', 'BBC Radio Northampton'),
        ('bbc_radio_nottingham', 'BBC Radio Nottingham'),
        ('bbc_radio_oxford', 'BBC Radio Oxford'),
        ('bbc_radio_sheffield', 'BBC Radio Sheffield'),
        ('bbc_radio_shropshire', 'BBC Radio Shropshire'),
        ('bbc_radio_solent', 'BBC Radio Solent'),
        ('bbc_radio_somerset_sound', 'BBC Somerset'),
        ('bbc_radio_stoke', 'BBC Radio Stoke'),
        ('bbc_radio_suffolk', 'BBC Radio Suffolk'),
        ('bbc_radio_surrey', 'BBC Surrey'),
        ('bbc_radio_sussex', 'BBC Sussex'),
        ('bbc_tees', 'BBC Tees'),
        ('bbc_three_counties_radio', 'BBC Three Counties Radio'),
        ('bbc_radio_wiltshire', 'BBC Wiltshire'),
        ('bbc_wm', 'BBC WM 95.6'),
        ('bbc_radio_york', 'BBC Radio York'),
    ]
    for id, name in channel_list:
        AddMenuEntry(name, id, 133, '', '', '')

def ListAtoZ():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    characters = [
        ('A', 'a'), ('B', 'b'), ('C', 'c'), ('D', 'd'), ('E', 'e'), ('F', 'f'),
        ('G', 'g'), ('H', 'h'), ('I', 'i'), ('J', 'j'), ('K', 'k'), ('L', 'l'),
        ('M', 'm'), ('N', 'n'), ('O', 'o'), ('P', 'p'), ('Q', 'q'), ('R', 'r'),
        ('S', 's'), ('T', 't'), ('U', 'u'), ('V', 'v'), ('W', 'w'), ('X', 'x'),
        ('Y', 'y'), ('Z', 'z'), ('0-9', '0-9')]

    if int(ADDON.getSetting('scrape_atoz')) == 1:
        pDialog = xbmcgui.DialogProgressBG()
        pDialog.create(translation(31019))
        page = 1
        total_pages = len(characters)
        for name, url in characters:
            GetAtoZPage(url)
            percent = int(100*page/total_pages)
            pDialog.update(percent,translation(31019),name)
            page += 1
        pDialog.close()
    else:
        for name, url in characters:
            AddMenuEntry(name, url, 124, '', '', '')


def GetAtoZPage(url):
    """Allows to list programmes based on alphabetical order.

    Creates the list of programmes for one character.
    """
    link = OpenURL('http://www.bbc.co.uk/iplayer/a-z/%s' % url)
    match = re.compile(
        '<a href="/iplayer/brand/(.+?)".+?<span class="title">(.+?)</span>',
        re.DOTALL).findall(link)
    for programme_id, name in match:
        AddMenuEntry(name, programme_id, 121, '', '', '')


def RadioListAtoZ():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    characters = [
        ('A', 'a'), ('B', 'b'), ('C', 'c'), ('D', 'd'), ('E', 'e'), ('F', 'f'),
        ('G', 'g'), ('H', 'h'), ('I', 'i'), ('J', 'j'), ('K', 'k'), ('L', 'l'),
        ('M', 'm'), ('N', 'n'), ('O', 'o'), ('P', 'p'), ('Q', 'q'), ('R', 'r'),
        ('S', 's'), ('T', 't'), ('U', 'u'), ('V', 'v'), ('W', 'w'), ('X', 'x'),
        ('Y', 'y'), ('Z', 'z'), ('0-9', '@')]

    for name, url in characters:
        AddMenuEntry(name, url, 134, '', '', '')

        
def RadioListGenres():
    """List programmes based on alphabetical order.

    Only creates the corresponding directories for each character.
    """
    genres = [
        ('childrens', 'Children\'s'),
        ('childrens/drama', 'Drama'),
        ('childrens/entertainmentandcomedy', 'Entertainment & Comedy'),
        ('childrens/factual', 'Factual'),
        ('childrens/music', 'Music'),
        ('comedy', 'Comedy'),
        ('comedy/character', 'Character'),
        ('comedy/impressionists', 'Impressionists'),
        ('comedy/music', 'Music'),
        ('comedy/satire', 'Satire'),
        ('comedy/sitcoms', 'Sitcoms'),
        ('comedy/sketch', 'Sketch'),
        ('comedy/spoof', 'Spoof'),
        ('comedy/standup', 'Standup'),
        ('comedy/stunt', 'Stunt'),
        ('drama', 'Drama'),
        ('drama/actionandadventure', 'Action & Adventure'),
        ('drama/biographical', 'Biographical'),
        ('drama/classicandperiod', 'Classic & Period'),
        ('drama/crime', 'Crime'),
        ('drama/historical', 'Historical'),
        ('drama/horrorandsupernatural', 'Horror & Supernatural'),
        ('drama/legalandcourtroom', 'Legal & Courtroom'),
        ('drama/medical', 'Medical'),
        ('drama/musical', 'Musical'),
        ('drama/political', 'Political'),
        ('drama/psychological', 'Psychological'),
        ('drama/relationshipsandromance', 'Relationships & Romance'),
        ('drama/scifiandfantasy', 'SciFi & Fantasy'),
        ('drama/soaps', 'Soaps'),
        ('drama/spiritual', 'Spiritual'),
        ('drama/thriller', 'Thriller'),
        ('drama/waranddisaster', 'War & Disaster'),
        ('drama/western', 'Western'),
        ('entertainment', 'Entertainment'),
        ('entertainment/varietyshows', 'Variety Shows'),
        ('factual', 'Factual'),
        ('factual/antiques', 'Antiques'),
        ('factual/artscultureandthemedia', 'Arts, Culture & the Media'),
        ('factual/beautyandstyle', 'Beauty & Style'),
        ('factual/carsandmotors', 'Cars & Motors'),
        ('factual/consumer', 'Consumer'),
        ('factual/crimeandjustice', 'Crime & Justice'),
        ('factual/disability', 'Disability'),
        ('factual/familiesandrelationships', 'Families & Relationships'),
        ('factual/foodanddrink', 'Food & Drink'),
        ('factual/healthandwellbeing', 'Health & Wellbeing'),
        ('factual/history', 'History'),
        ('factual/homesandgardens', 'Homes & Gardens'),
        ('factual/lifestories', 'Life Stories'),
        ('factual/money', 'Money'),
        ('factual/petsandanimals', 'Pets & Animals'),
        ('factual/politics', 'Politics'),
        ('factual/scienceandnature', 'Science & Nature'),
        ('factual/travel', 'Travel'),
        ('learning', 'Learning'),
        ('learning/adults', 'Adults'),
        ('learning/preschool', 'Pre-School'),
        ('learning/primary', 'Primary'),
        ('learning/secondary', 'Secondary'),
        ('music', 'Music'),
        ('music/classical', 'Classical'),
        ('music/classicpopandrock', 'Classic Pop & Rock'),
        ('music/country', 'Country'),
        ('music/danceandelectronica', 'Dance & Electronica'),
        ('music/desi', 'Desi'),
        ('music/easylisteningsoundtracksandmusicals', 'Easy Listening, Soundtracks & Musicals'),
        ('music/folk', 'Folk'),
        ('music/hiphoprnbanddancehall', 'Hip Hop, RnB & Dancehall'),
        ('music/jazzandblues', 'Jazz & Blues'),
        ('music/popandchart', 'Pop & Chart'),
        ('music/rockandindie', 'Rock & Indie'),
        ('music/soulandreggae', 'Soul & Reggae'),
        ('music/world', 'World'),
        ('religionandethics', 'Religion & Ethics'),
        ('sport', 'Sport'),
        ('sport/americanfootball', 'American Football'),
        ('sport/athletics', 'Athletics'),
        ('sport/baseball', 'Baseball'),
        ('sport/basketball', 'Basketball'),
        ('sport/bobsleigh', 'Bobsleigh'),
        ('sport/boxing', 'Boxing'),
        ('sport/commonwealthgames', 'Commonwealth Games'),
        ('sport/cricket', 'Cricket'),
        ('sport/cycling', 'Cycling'),
        ('sport/disabilitysport', 'Disability Sport'),
        ('sport/football', 'Football'),
        ('sport/formulaone', 'Formula One'),
        ('sport/gaelicgames', 'Gaelic Games'),
        ('sport/golf', 'Golf'),
        ('sport/gymnastics', 'Gymnastics'),
        ('sport/hockey', 'Hockey'),
        ('sport/horseracing', 'Horse Racing'),
        ('sport/icehockey', 'Ice Hockey'),
        ('sport/motorsport', 'Motorsport'),
        ('sport/netball', 'Netball'),
        ('sport/olympics', 'Olympics'),
        ('sport/rowing', 'Rowing'),
        ('sport/rugbyleague', 'Rugby League'),
        ('sport/rugbyunion', 'Rugby Union'),
        ('sport/sailing', 'Sailing'),
        ('sport/shinty', 'Shinty'),
        ('sport/snooker', 'Snooker'),
        ('sport/swimming', 'Swimming'),
        ('sport/synchronisedswimming', 'Synchronised Swimming'),
        ('sport/tabletennis', 'Table Tennis'),
        ('sport/taekwondo', 'Taekwondo'),
        ('sport/tennis', 'Tennis'),
        ('sport/triathlon', 'Triathlon'),
        ('sport/winterolympics', 'Winter Olympics'),
        ('sport/wintersports', 'Winter Sports'),
        ('weather', 'Weather'),
        ]

    group = ''
    for url, name in genres:
        if not "/" in url:
            group = name
            #print group
            AddMenuEntry("[B]%s[/B]" % name, url, 135, '', '', '')
        else:
            #print group
            AddMenuEntry("%s - %s " % (group, name), url, 135, '', '', '')
 
    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED) 
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

        

def RadioGetAtoZPage(url):
    """Allows to list programmes based on alphabetical order.

    Creates the list of programmes for one character.
    """
    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(31019))

    html = OpenURL('http://www.bbc.co.uk/radio/programmes/a-z/by/%s/current' % url)
    #print html.encode("utf8")
    
    #TODO: optional pagination and progress bar
    total_pages = 1
    current_page = 1
    page_range = range(1)
    paginate = re.search(r'<ol.+?class="pagination.*?</ol>',html)
    next_page = 1
    if paginate:
        pages = re.findall(r'<li.+?class="pagination__page.*?</li>',paginate.group(0))
        if pages:
            last = pages[-1]
            last_page = re.search(r'<a.+?href="(.*?=)(.*?)"',last)
            #print last_page.group(2)
            page_base_url = last_page.group(1)
            total_pages = int(last_page.group(2))
        page_range = range(1, total_pages+1)

    for page in page_range:

        if page > current_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(page)
            html = OpenURL(page_url)
            
        list_item_num = 1
    
        programmes = html.split('<div class="programme ')
        for programme in programmes:
            
            if not programme.startswith("programme--radio"):
                continue
            #print programme.encode("utf8")
            
            if "available" not in programme: #TODO find a more robust test
                continue

            programme_id = ''
            programme_id_match = re.search(r'data-pid="(.*?)"', programme)
            if programme_id_match:
                programme_id = programme_id_match.group(1)
                
            name = ''
            name_match = re.search(r'<span property="name">(.*?)</span>', programme)
            if name_match:
                name = name_match.group(1)
                
            image = ''    
            image_match = re.search(r'<meta property="image" content="(.*?)" />', programme)
            if image_match:
                image = image_match.group(1)
                
            synopsis = ''    
            synopsis_match = re.search(r'<span property="description">(.*?)</span>', programme)
            if synopsis_match:
                synopsis = synopsis_match.group(1)
                      
            station = ''    
            station_match = re.search(r'<p class="programme__service.+?<strong>(.*?)</strong>.*?</p>', programme)
            if station_match:
                station = station_match.group(1)
                
            title = "[B]%s[/B] - %s" % (station, name)
            
            if programme_id and title and image and synopsis:
                AddMenuEntry(title, programme_id, 131, image, synopsis, '')
                
            percent = int(100*(page+list_item_num/len(programmes))/total_pages)
            pDialog.update(percent,translation(31019),name)

            list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(31019))
        
    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

    pDialog.close()
    
    
    
def RadioGetGenrePage(url):
    """Allows to list programmes based on alphabetical order.

    Creates the list of programmes for one character.
    """
    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(31019))

    html = OpenURL('http://www.bbc.co.uk/radio/programmes/genres/%s/player/episodes' % url)
    #print html.encode("utf8")
    
    #TODO: optional pagination and progress bar
    total_pages = 1
    current_page = 1
    page_range = range(1)
    paginate = re.search(r'<ol.+?class="pagination.*?</ol>',html)
    next_page = 1
    if paginate:
        pages = re.findall(r'<li.+?class="pagination__page.*?</li>',paginate.group(0))
        if pages:
            last = pages[-1]
            last_page = re.search(r'<a.+?href="(.*?=)(.*?)"',last)
            #print last_page.group(2)
            page_base_url = last_page.group(1)
            total_pages = int(last_page.group(2))
        page_range = range(1, total_pages+1)

    for page in page_range:

        if page > current_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(page)
            html = OpenURL(page_url)
            
        list_item_num = 1
    
        programmes = html.split('<div class="programme ')
        for programme in programmes:
            
            if not programme.startswith("programme--radio"):
                continue
            #print programme.encode("utf8")
            
            if "available" not in programme: #TODO find a more robust test
                continue

            programme_id = ''
            programme_id_match = re.search(r'data-pid="(.*?)"', programme)
            if programme_id_match:
                programme_id = programme_id_match.group(1)
                #print programme_id
                
            name = ''
            name_match = re.search(r'<span property="name">(.*?)</span>', programme)
            if name_match:
                name = name_match.group(1)
                #print name
                
            #BUG not robust enough
            subtitle = ''
            subtitle_match = re.search(r'<span class="programme__subtitle.+?property="name">(.*?)</span>.*?property="name">(.*?)</span>', programme)
            if subtitle_match:
                series = subtitle_match.group(1)
                episode = subtitle_match.group(2)
                subtitle = "(%s, %s)" % (series, episode)
                #print subtitle
                
            image = ''    
            image_match = re.search(r'<meta property="image" content="(.*?)" />', programme)
            if image_match:
                image = image_match.group(1)
                #print image
                
            synopsis = ''    
            synopsis_match = re.search(r'<span property="description">(.*?)</span>', programme)
            if synopsis_match:
                synopsis = synopsis_match.group(1)
                #print synopsis.encode("utf8")
                      
            station = ''    
            station_match = re.search(r'<p class="programme__service.+?<strong>(.*?)</strong>.*?</p>', programme)
            if station_match:
                station = station_match.group(1)
                #print station
                
            title = "[B]%s[/B] - %s %s" % (station, name, subtitle)
            #print title
            
            if programme_id and title and image and synopsis:
                AddMenuEntry(title, programme_id, 132, image, synopsis, '')
                
            percent = int(100*(page+list_item_num/len(programmes))/total_pages)
            pDialog.update(percent,translation(31019),name)

            list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(31019))
        
    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)

    pDialog.close()
    
    
def ParseAired(aired):
    """Parses a string format %d %b %Y to %d/%n/%Y otherwise empty string."""
    if aired:
        try:
            # Need to use equivelent for datetime.strptime() due to weird TypeError.
            return datetime.datetime(*(time.strptime(aired[0], '%d %b %Y')[0:6])).strftime('%d/%m/%Y')
        except ValueError:
            pass
    return ''

def FirstShownToAired(first_shown):
    """Converts the 'First shown' tag to %Y %m %d format."""
    release_parts = first_shown.split(' ')

    if len(release_parts) == 1:
        month = '01'
        day = '01'
        year = first_shown
    else:
        year = release_parts[-1]
        month = release_parts[-2]
        monthDict={
            'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06',
            'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
        if month in monthDict:
            month = monthDict[month]
            day = release_parts[-3].rjust(2,'0')
        else:
            month = '01'
            day = '01'
    aired = year + '-' + month + '-' + day
    return aired


def GetEpisodes(url):
    new_url = 'http://www.bbc.co.uk/iplayer/episodes/%s' % url
    ScrapeEpisodes(new_url)


def RadioGetEpisodes(url):
    new_url = 'http://www.bbc.co.uk/programmes/%s/episodes/player' % url
    RadioScrapeEpisodes(new_url)


def GetGroup(url):
    new_url = "http://www.bbc.co.uk/iplayer/group/%s" % url
    ScrapeEpisodes(new_url)


def ScrapeEpisodes(page_url):
    """Creates a list of programmes on one standard HTML page.

    ScrapeEpisodes contains a number of special treatments, which are only needed for
    specific pages, e.g. Search, but allows to use a single function for all kinds
    of pages.
    """

    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(31019))

    html = OpenURL(page_url)

    total_pages = 1
    current_page = 1
    page_range = range(1)
    paginate = re.search(r'<div class="paginate.*?</div>',html)
    next_page = 1
    if paginate:
        if int(ADDON.getSetting('paginate_episodes')) == 0:
            current_page_match = re.search(r'page=(\d*)', page_url)
            if current_page_match:
                current_page = int(current_page_match.group(1))
            page_range = range(current_page, current_page+1)
            next_page_match = re.search(r'<span class="next txt">.+?href="(.*?page=)(.*?)"', paginate.group(0))
            if next_page_match:
                page_base_url = next_page_match.group(1)
                next_page = int(next_page_match.group(2))
            else:
                next_page = current_page
            page_range = range(current_page, current_page+1)
        else:
            pages = re.findall(r'<li class="page.*?</li>',paginate.group(0))
            if pages:
                last = pages[-1]
                last_page = re.search(r'<a href="(.*?page=)(.*?)">',last)
                page_base_url = last_page.group(1)
                total_pages = int(last_page.group(2))
            page_range = range(1, total_pages+1)


    for page in page_range:

        if page > current_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(page)
            html = OpenURL(page_url)

        # NOTE remove inner li to match outer li

        # <li data-version-type="hd">
        html = re.compile(r'<li data-version-type.*?</li>',
                          flags=(re.DOTALL | re.MULTILINE)).sub('', html)

        # <li class="list-item programme"  data-ip-id="p026f2t4">
        list_items = re.findall(r'<li class="list-item.*?</li>', html, flags=(re.DOTALL | re.MULTILINE))

        list_item_num = 1

        for li in list_items:

            # <li class="list-item unavailable"  data-ip-id="b06sq9xj">
            unavailable_match = re.search(
                '<li class="list-item.*?unavailable.*?"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if unavailable_match:
                continue

            # <li class="list-item search-group"  data-ip-id="b06rdtx0">
            search_group = False
            search_group_match = re.search(
                '<li class="list-item.*?search-group.*?"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if search_group_match:
                search_group = True

            main_url = None
            # <a href="/iplayer/episode/p026gmw9/world-of-difference-the-models"
            # title="World of Difference, The Models" class="list-item-link stat"
            url_match = re.search(
                r'<a.*?href="(.*?)".*?list-item-link.*?>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if url_match:
                url = url_match.group(1)
                if url:
                    main_url = 'http://www.bbc.co.uk' + url

            name = ''
            title = ''
            #<div class="title top-title">World of Difference</div>
            title_match = re.search(
                r'<div class="title top-title">\s*(.*?)\s*</div>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if title_match:
                title = title_match.group(1)
                name = title

            subtitle = None
            #<div class="subtitle">The Models</div>
            subtitle_match = re.search(
                r'<div class="subtitle">\s*(.*?)\s*</div>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if subtitle_match:
                subtitle = subtitle_match.group(1)
                if subtitle:
                    name = name + " - " + subtitle

            icon = ''
            type = None
            # <div class="r-image"  data-ip-type="episode"
            # data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/p026vl1q.jpg">
            # <div class="r-image"  data-ip-type="group"
            # data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/p037ty9z.jpg">
            image_match = re.search(
                r'<div class="r-image".+?data-ip-type="(.*?)".+?data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/(.*?)\.jpg"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if image_match:
                type = image_match.group(1)
                image = image_match.group(2)
                if image:
                    icon = "http://ichef.bbci.co.uk/images/ic/832x468/" + image + ".jpg"

            synopsis = ''
            # <p class="synopsis">What was it like to be a top fashion model 30 years ago? (1978)</p>
            synopsis_match = re.search(
                r'<p class="synopsis">\s*(.*?)\s*</p>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if synopsis_match:
                synopsis = synopsis_match.group(1)

            aired = ''
            # <span class="release">\nFirst shown: 8 Jun 1967\n</span>
            release_match = re.search(
                r'<span class="release">.*?First shown:\s*(.*?)\n.*?</span>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if release_match:
                release = release_match.group(1)
                if release:
                    aired = FirstShownToAired(release)

            episodes = None
            # <a class="view-more-container avail stat" href="/iplayer/episodes/p00db1jf" data-progress-state="">
            # <a class="view-more-container sibling stat"
            #  href="/iplayer/search?q=doctor&amp;search_group_id=urn:bbc:programmes:b06qbs4n">
            episodes_match = re.search(
                r'<a class="view-more-container.+?stat".+?href="(.*?)"',
                li, flags=(re.DOTALL | re.MULTILINE))
            if episodes_match:
                episodes = episodes_match.group(1)

            more = None
            # <em class="view-more-heading">27</em>
            more_match = re.search(
                r'<em class="view-more-heading">(.*?)</em>',
                li, flags=(re.DOTALL | re.MULTILINE))
            if more_match:
                more = more_match.group(1)

            if episodes:
                episodes_url = 'http://www.bbc.co.uk' + episodes
                if search_group:
                    AddMenuEntry('[B]%s[/B] - %s' % (title, translation(31018)),
                                 episodes_url, 128, icon, '', '')
                else:
                    AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(31013)),
                                 episodes_url, 128, icon, '', '')
            elif more:
                AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(31013)),
                             main_url, 128, icon, '', '')

            if type != "group":
                CheckAutoplay(name , main_url, icon, synopsis, aired)

            percent = int(100*(page+list_item_num/len(list_items))/total_pages)
            pDialog.update(percent,translation(31019),name)

            list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(31019))

    if int(ADDON.getSetting('paginate_episodes')) == 0:
        if current_page < next_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(next_page)
            AddMenuEntry('Next page', page_url, 128, '', '', '')
    else:
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)

    pDialog.close()



def RadioScrapeEpisodes(page_url):
    """Creates a list of programmes on one standard HTML page.

    ScrapeEpisodes contains a number of special treatments, which are only needed for
    specific pages, e.g. Search, but allows to use a single function for all kinds
    of pages.
    """
    pDialog = xbmcgui.DialogProgressBG()
    pDialog.create(translation(31019))
    
    html = OpenURL(page_url)
    #print html.encode("utf8")
    
    #TODO: optional pagination and progress bar
    total_pages = 1
    current_page = 1
    page_range = range(1)
    paginate = re.search(r'<ol.+?class="pagination.*?</ol>',html)
    next_page = 1
    if paginate:
        pages = re.findall(r'<li.+?class="pagination__page.*?</li>',paginate.group(0))
        if pages:
            last = pages[-1]
            last_page = re.search(r'<a.+?href="(.*?=)(.*?)"',last)
            #print last_page.group(2)
            page_base_url = last_page.group(1)
            total_pages = int(last_page.group(2))
        page_range = range(1, total_pages+1)

    for page in page_range:

        if page > current_page:
            page_url = 'http://www.bbc.co.uk' + page_base_url + str(page)
            html = OpenURL(page_url)
    
        title = ''
        title_match = re.search(r'<div class="br-masthead__title">.*?<a.*?title="(.*?)"', html)
        if title_match:
            title = title_match.group(1)
            #print title

        list_item_num = 1
            
        programmes = html.split('<div class="programme ')
        for programme in programmes:
            
            if not programme.startswith("programme--radio"):
                continue
            #print programme.encode("utf8")

            programme_id = ''
            programme_id_match = re.search(r'data-pid="(.*?)"', programme)
            if programme_id_match:
                programme_id = programme_id_match.group(1)
                
            name = ''
            name_match = re.search(r'<span property="name">(.*?)</span>', programme)
            if name_match:
                name = name_match.group(1)
                
            image = ''    
            image_match = re.search(r'<meta property="image" content="(.*?)" />', programme)
            if image_match:
                image = image_match.group(1)
                
            synopsis = ''    
            synopsis_match = re.search(r'<span property="description">(.*?)</span>', programme)
            if synopsis_match:
                synopsis = synopsis_match.group(1)
                      
            full_title = "[B]%s[/B] - %s" % (title, name)
            
            if programme_id and title and image and synopsis:
                AddMenuEntry(full_title, programme_id, 132, image, synopsis, '')
                
            percent = int(100*(page+list_item_num/len(programmes))/total_pages)
            pDialog.update(percent,translation(31019),name)

            list_item_num += 1

        percent = int(100*page/total_pages)
        pDialog.update(percent,translation(31019))

            
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)

    pDialog.close()


def ListCategories():
    """Parses the available categories and creates directories for selecting one of them.
    The category names are scraped from the website.
    """
    html = OpenURL('http://www.bbc.co.uk/iplayer')
    match = re.compile(
        '<a href="/iplayer/categories/(.+?)" class="stat">(.+?)</a>'
        ).findall(html)
    for url, name in match:
        AddMenuEntry(name, url, 125, '', '', '')


def ListCategoryFilters(url):
    """Parses the available category filters (if available) and creates directories for selcting them.
    If there are no filters available, all programmes will be listed using GetFilteredCategory.
    """
    NEW_URL = 'http://www.bbc.co.uk/iplayer/categories/%s/all?sort=atoz' % url
    # Read selected category's page.
    html = OpenURL(NEW_URL)
    # Some categories offer filters, we want to provide these filters as options.
    match1 = re.findall(
        '<li class="filter"> <a class="name" href="/iplayer/categories/(.+?)"> (.+?)</a>',
        html,
        re.DOTALL)
    if match1:
        AddMenuEntry('All', url, 126, '', '', '')
        for url, name in match1:
            AddMenuEntry(name, url, 126, '', '', '')
    else:
        GetFilteredCategory(url)


def GetFilteredCategory(url):
    """Parses the programmes available in the category view."""
    NEW_URL = 'http://www.bbc.co.uk/iplayer/categories/%s/all?sort=atoz' % url

    ScrapeEpisodes(NEW_URL)


def ListChannelHighlights():
    """Creates a list directories linked to the highlights section of each channel."""
    channel_list = [
        ('bbcone', 'bbc_one', 'BBC One'),
        ('bbctwo', 'bbc_two', 'BBC Two'),
        ('tv/bbcthree', 'bbc_three', 'BBC Three'),
        ('bbcfour', 'bbc_four', 'BBC Four'),
        ('tv/cbbc', 'cbbc', 'CBBC'),
        ('tv/cbeebies', 'cbeebies', 'CBeebies'),
        ('tv/bbcnews', 'bbc_news24', 'BBC News Channel'),
        ('tv/bbcparliament', 'bbc_parliament', 'BBC Parliament'),
        ('tv/bbcalba', 'bbc_alba', 'Alba'),
        ('tv/s4c', 's4c', 'S4C'),
    ]
    for id, img, name in channel_list:
        iconimage = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', img + '.png'))
        AddMenuEntry(name, id, 106, iconimage, '', '')


def ListHighlights(highlights_url):
    """Creates a list of the programmes in the highlights section.
    """

    html = OpenURL('http://www.bbc.co.uk/%s' % highlights_url)

    inner_anchors = re.findall(r'<a.*?(?!<a).*?</a>',html,flags=(re.DOTALL | re.MULTILINE))

    # First find all groups as we need to store some properties of groups for later reuse.
    group_properties = []

    # NOTE find episode count first
    episode_count = dict()
    groups = [a for a in inner_anchors if re.match(
        r'<a[^<]*?class="grouped-items__cta.*?data-object-type="group-list-link".*?',
        a, flags=(re.DOTALL | re.MULTILINE))]
    for group in groups:

        href = ''
        href_match = re.match(
            r'<a[^<]*?href="(.*?)"',
            group, flags=(re.DOTALL | re.MULTILINE))
        if href_match:
            href = href_match.group(1)

        count_match = re.search(
            r'>View all ([0-9]*).*?</a>',
            group, flags=(re.DOTALL | re.MULTILINE))
        if count_match:
            count = count_match.group(1)
            episode_count[href] = count

    groups = [a for a in inner_anchors if re.match(
        r'<a[^<]*?class="grouped-items__title.*?data-object-type="group-list-link".*?',
        a, flags=(re.DOTALL | re.MULTILINE))]
    for group in groups:

        href = ''
        href_match = re.match(
            r'<a[^<]*?href="(.*?)"',
            group, flags=(re.DOTALL | re.MULTILINE))
        if href_match:
            href = href_match.group(1)

        name = ''
        name_match = re.search(
            r'<strong>(.*?)</strong>',
            group, flags=(re.DOTALL | re.MULTILINE))
        if name_match:
            name = name_match.group(1)

        count = ''
        if href in episode_count:
            count = episode_count[href]

        url = 'http://www.bbc.co.uk' + href

        # Unfortunately, the group type is not inside the links, so we need to search the whole HTML.
        group_type = ''
        group_type_match = re.search(
            r'data-group-name="'+name+'".+?data-group-type="(.+?)"',
            html, flags=(re.DOTALL | re.MULTILINE))
        if group_type_match:
            group_type = group_type_match.group(1)

        position = ''
        position_match = re.search(
            r'data-object-position="(.+?)-ALL"',
            group, flags=(re.DOTALL | re.MULTILINE))
        if position_match:
            group_properties.append(
                             [position_match.group(1),
                             name, group_type])

        AddMenuEntry('[B]%s: %s[/B] - %s %s' % (translation(31014), name, count, translation(31015)),
                     url, 128, '', '', '')

    # Some programmes show up twice in HTML, once inside the groups, once outside.
    # We need to parse both to avoid duplicates and to make sure we get all of them.
    episodelist = []

    # <a\n    href="/iplayer/episode/b06tr74y/eastenders-24122015"\n    class="grouped-items__list-link
    listeds = [a for a in inner_anchors if re.search(
        r'class="grouped-items__list-link',
        a, flags=(re.DOTALL | re.MULTILINE))]

    for listed in listeds:

        episode_id = ''
        # <a\n    href="/iplayer/episode/b06tr74y/eastenders-24122015"
        id_match = re.match(
            r'<a.*?href="/iplayer/episode/(.*?)/',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if id_match:
            episode_id = id_match.group(1)

        name = ''
        # <p class="grouped-items__title grouped-items__title--item typo typo--skylark">
        # <strong>EastEnders</strong></p>
        title_match = re.search(
            r'<.*?class="grouped-items__title.*?<strong>(.*?)</strong>',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if title_match:
            name = title_match.group(1)
            name = re.compile(r'<.*?>', flags=(re.DOTALL | re.MULTILINE)).sub('', name)

        # <p class="grouped-items__subtitle typo typo--canary">24/12/2015</p>
        subtitle_match = re.search(
            r'<.*?class="grouped-items__subtitle.*?>(.*?)<',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if subtitle_match:
            name = name + ' - ' + subtitle_match.group(1)

        # Assign correct group based on the position of the episode
        position = ''
        position_match = re.search(
            r'data-object-position="(.+?)"',
            listed, flags=(re.DOTALL | re.MULTILINE))
        if position_match:
            for n,i in enumerate(group_properties):
                if re.match(i[0], position_match.group(1), flags=(re.DOTALL | re.MULTILINE)):
                    position = i[1]
                    # For series-catchup groups, we need to modify the title.
                    if i[2] == 'series-catchup':
                        name = i[1]+': '+name

        episodelist.append(
                    [episode_id,
                    name,
                    "%s %s" % (translation(31016), position),
                    'DefaultVideo.png',
                    '']
                    )

    # < a\nhref="/iplayer/episode/p036gq3z/bbc-music-introducing-from-buddhist-monk-to-rock-star"\n
    # class="single-item stat"
    singles = [a for a in inner_anchors if re.search(
        r'class="single-item',
        a, flags=(re.DOTALL | re.MULTILINE))]

    for single in singles:

        object_type = ''
        # data-object-type="episode-backfill"
        data_object_type = re.search(
            r'data-object-type="(.*?)"',
            single, flags=(re.DOTALL | re.MULTILINE))
        if data_object_type:
            object_type = data_object_type.group(1)
            if object_type == "episode-backfill":
                if (highlights_url not in ['tv/bbcnews', 'tv/bbcparliament']):
                    continue

        episode_id = ''
        url = ''
        # <a\nhref="/iplayer/episode/p036gq3z/bbc-music-introducing-from-buddhist-monk-to-rock-star"
        if object_type == "editorial-promo":
            id_match = re.match(
                r'<a.*?href="(.*?)"',
                single, flags=(re.DOTALL | re.MULTILINE))
        else:
            id_match = re.match(
                r'<a.*?href="/iplayer/episode/(.*?)/',
                single, flags=(re.DOTALL | re.MULTILINE))
        if id_match:
            episode_id = id_match.group(1)
            url = 'http://www.bbc.co.uk/iplayer/episode/' + episode_id

        name = ''
        # <h3 class="single-item__title typo typo--skylark"><strong>BBC Music Introducing</strong></h3>
        title_match = re.search(
            r'<.*?class="single-item__title.*?<strong>(.*?)</strong>',
            single, flags=(re.DOTALL | re.MULTILINE))
        if title_match:
            name = title_match.group(1)
            name = re.compile(r'<.*?>', flags=(re.DOTALL | re.MULTILINE)).sub('', name)

        # <p class="single-item__subtitle typo typo--canary">From Buddhist Monk to Rock Star</p>
        subtitle_match = re.search(
            r'<.*?class="single-item__subtitle.*?>(.*?)<',
            single, flags=(re.DOTALL | re.MULTILINE))
        if subtitle_match:
            name = name + ' - ' + subtitle_match.group(1)

        icon = ''
        # <div class="r-image"  data-ip-type="episode"
        # data-ip-src="http://ichef.bbci.co.uk/images/ic/406x228/p036gtc5.jpg">
        image_match = re.search(
            r'<.*?class="r-image.*?data-ip-src="(.*?)"',
            single, flags=(re.DOTALL | re.MULTILINE))
        if image_match:
            icon = image_match.group(1)

        desc = ''
        # <p class="single-item__overlay__desc">
        # The remarkable rise of Ngawang Lodup - from BBC Introducing to performing at the O2 Arena</p>
        desc_match = re.search(
            r'<.*?class="single-item__overlay__desc.*?>(.*?)<',
            single, flags=(re.DOTALL | re.MULTILINE))
        if desc_match:
            desc = desc_match.group(1)

        aired = ''
        # <p class="single-item__overlay__subtitle">First shown: 4 Nov 2015</p>
        release_match = re.search(
            r'<.*?class="single-item__overlay__subtitle">First shown: (.*?)<',
            single, flags=(re.DOTALL | re.MULTILINE))
        if release_match:
            release = release_match.group(1)
            if release:
                aired = FirstShownToAired(release)

        add_entry = True
        for n,i in enumerate(episodelist):
            if i[0]==episode_id:
                episodelist[n][2]=desc
                episodelist[n][3]=icon
                episodelist[n][4]=aired
                add_entry = False
        if add_entry:
            if object_type == "editorial-promo":
                AddMenuEntry('[B]%s[/B]' % (name), episode_id, 128, icon, '', '')
            else:
                CheckAutoplay(name, url, icon, desc, aired)

    # Finally add all programmes which have been identified as part of a group before.
    for episode in episodelist:
        episode_url = "http://www.bbc.co.uk/iplayer/episode/%s" % episode[0]
        if ((ADDON.getSetting('suppress_incomplete') == 'false') or (not episode[4] == '')):
            CheckAutoplay(episode[1], episode_url, episode[3], episode[2], episode[4])

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)


def ListMostPopular():
    """Scrapes all episodes of the most popular page."""
    ScrapeEpisodes("http://www.bbc.co.uk/iplayer/group/most-popular")

    
def RadioListMostPopular():
    html = OpenURL('http://www.bbc.co.uk/radio/popular')
    #print html.encode("utf8")
    
    programmes = re.split(r'<li class="(episode|clip) typical-list-item', html)
    for programme in programmes:
        
        if not programme.startswith(" item-idx-"):
            continue
        #print programme.encode("utf8")
        
        #if "available" not in programme: #TODO find a more robust test
        #    continue

        programme_id = ''
        programme_id_match = re.search(r'<a href="/programmes/(.*?)"', programme)
        if programme_id_match:
            programme_id = programme_id_match.group(1)
            #print programme_id
            
        name = ''
        name_match = re.search(r'<img src=".*?" alt="(.*?)"', programme)
        if name_match:
            name = name_match.group(1)
            #print name
            
        #BUG not robust enough
        subtitle = ''
        subtitle_match = re.search(r'<span class="subtitle">\s*(.+?)\s*</span>', programme)
        if subtitle_match:
            subtitle = "(%s)" % subtitle_match.group(1)
            #print subtitle.encode("utf8")
            
        image = ''    
        image_match = re.search(r'<img src="(.*?)"', programme)
        if image_match:
            image = image_match.group(1)
            #print image
                  
        station = ''    
        station_match = re.search(r'<span class="service_title">\s*(.+?)\s*</span>', programme)
        if station_match:
            station = station_match.group(1)
            #print station
            
        title = "[B]%s[/B] - %s %s" % (station, name, subtitle)
        #print title.encode("utf8")
        
        if programme_id and title and image:
            AddMenuEntry(title, programme_id, 132, image, ' ', '') #NOTE description can't be ''
                
        
    #BUG: this should sort by original order but it doesn't (see http://trac.kodi.tv/ticket/10252)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    
    
    

def Search(search_entered):
    """Simply calls the online search function. The search is then evaluated in EvaluateSearch."""
    if search_entered is None:
        keyboard = xbmc.Keyboard('', 'Search iPlayer')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText() .replace(' ', '%20')  # sometimes you need to replace spaces with + or %20

    if search_entered is None:
        return False

    NEW_URL = 'http://www.bbc.co.uk/iplayer/search?q=%s' % search_entered
    ScrapeEpisodes(NEW_URL)

    
def RadioSearch(search_entered):
    """Simply calls the online search function. The search is then evaluated in EvaluateSearch."""
    if search_entered is None:
        keyboard = xbmc.Keyboard('', 'Search iPlayer')
        keyboard.doModal()
        if keyboard.isConfirmed():
            search_entered = keyboard.getText()

    if search_entered is None:
        return False

    #NEW_URL = 'http://www.bbc.co.uk/radio/programmes/a-z/by/%s/current' % search_entered
    RadioGetAtoZPage(search_entered)
    

def ParseImageUrl(url):
    return url.replace("{recipe}", "288x162")


def AddAvailableStreamsDirectory(name, stream_id, iconimage, description):
    """Will create one menu entry for each available stream of a particular stream_id"""
    # print "Stream ID: %s"%stream_id
    streams = ParseStreams(stream_id)
    # print streams
    if streams[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams[1][0]
        # print subtitles_url
    else:
        subtitles_url = ''
    suppliers = ['', 'Akamai', 'Limelight', 'Level3']
    bitrates = [0, 800, 1012, 1500, 1800, 2400, 3116, 5510]
    for supplier, bitrate, url, resolution in sorted(streams[0], key=itemgetter(1), reverse=True):
        if bitrate in (5, 7):
            color = 'green'
        elif bitrate == 6:
            color = 'blue'
        elif bitrate in (3, 4):
            color = 'yellow'
        else:
            color = 'orange'
        title = name + ' - [I][COLOR %s]%0.1f Mbps[/COLOR] [COLOR lightgray]%s[/COLOR][/I]' % (
            color, bitrates[bitrate] / 1000, suppliers[supplier])
        AddMenuEntry(title, url, 201, iconimage, description, subtitles_url, resolution=resolution)


def RadioAddAvailableStreamsDirectory(name, stream_id, iconimage, description):
    """Will create one menu entry for each available stream of a particular stream_id"""
    # print "Stream ID: %s"%stream_id
    streams = RadioParseStreams(stream_id)
    #print streams
    suppliers = ['', 'Akamai', 'Limelight', 'Level3']
    for supplier, bitrate, url, encoding in sorted(streams[0], key=itemgetter(1), reverse=True):
        bitrate = int(bitrate)
        if bitrate >= 320:
            color = 'green'
        elif bitrate >= 192:
            color = 'blue'
        elif bitrate >= 128:
            color = 'yellow'
        else:
            color = 'orange'
        title = name + ' - [I][COLOR %s]%d Kbps %s[/COLOR] [COLOR lightgray]%s[/COLOR][/I]' % (
            color, bitrate, encoding, suppliers[supplier])
        AddMenuEntry(title, url, 201, iconimage, description, '', '')


def ParseStreams(stream_id):
    retlist = []
    # print "Parsing streams for PID: %s"%stream_id[0]
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id[0]
    html = OpenURL(NEW_URL)
    # Parse the different streams and add them as new directory entries.
    match = re.compile(
        'connection authExpires=".+?href="(.+?)".+?supplier="mf_(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    for m3u8_url, supplier, transfer_format in match:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_uk_hls':
                tmp_sup = 1
            elif supplier == 'limelight_uk_hls':
                tmp_sup = 2
            m3u8_breakdown = re.compile('(.+?)iptv.+?m3u8(.+?)$').findall(m3u8_url)
            #print m3u8_breakdown
            # print m3u8_url
            m3u8_html = OpenURL(m3u8_url)
            m3u8_match = re.compile('BANDWIDTH=(.+?),.+?RESOLUTION=(.+?)\n(.+?)\n').findall(m3u8_html)
            for bandwidth, resolution, stream in m3u8_match:
                # print bandwidth
                # print resolution
                #print stream
                url = "%s%s%s" % (m3u8_breakdown[0][0], stream, m3u8_breakdown[0][1])
                #print url
                if int(bandwidth) == 1012300:
                    tmp_br = 2
                elif int(bandwidth) == 1799880:
                    tmp_br = 4
                elif int(bandwidth) == 3116400:
                    tmp_br = 6
                elif int(bandwidth) == 5509880:
                    tmp_br = 7
                retlist.append((tmp_sup, tmp_br, url, resolution))
    # It may be useful to parse these additional streams as a default as they offer additional bandwidths.
    match = re.compile(
        'kind="video".+?connection href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    # print match
    unique = []
    [unique.append(item) for item in match if item not in unique]
    # print unique
    for m3u8_url, supplier, transfer_format in unique:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_hls_open':
                tmp_sup = 1
            elif supplier == 'limelight_hls_open':
                tmp_sup = 2
            m3u8_breakdown = re.compile('.+?master.m3u8(.+?)$').findall(m3u8_url)
        # print m3u8_url
        # print m3u8_breakdown
        m3u8_html = OpenURL(m3u8_url)
        # print m3u8_html
        m3u8_match = re.compile('BANDWIDTH=(.+?),RESOLUTION=(.+?),.+?\n(.+?)\n').findall(m3u8_html)
        # print m3u8_match
        for bandwidth, resolution, stream in m3u8_match:
            # print bandwidth
            # print resolution
            # print stream
            url = "%s%s" % (stream, m3u8_breakdown[0][0])
            # This is not entirely correct, displayed bandwidth may be higher or lower than actual bandwidth.
            if int(bandwidth) <= 801000:
                tmp_br = 1
            elif int(bandwidth) <= 1510000:
                tmp_br = 3
            elif int(bandwidth) <= 2410000:
                tmp_br = 5
            retlist.append((tmp_sup, tmp_br, url, resolution))
    match = re.compile('service="captions".+?connection href="(.+?)"').findall(html)
    # print "Subtitle URL: %s"%match
    # print retlist
    if not match:
        # print "No streams found"
        check_geo = re.search(
            '<error id="geolocation"/>', html)
        if check_geo:
            # print "Geoblock detected, raising error message"
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(32000), translation(32001))
            raise
    return retlist, match

def RadioParseStreams(stream_id):
    retlist = []
    # print "Parsing streams for PID: %s"%stream_id[0]
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id[0]
    html = OpenURL(NEW_URL)
    # Parse the different streams and add them as new directory entries.
    match = re.compile(
        'media.+?bitrate="(.+?)".+?encoding="(.+?)".+?connection.+?href="(.+?)".+?supplier="(.+?)".+?transferFormat="(.+?)"'
        ).findall(html)
    for bitrate, encoding, m3u8_url, supplier, transfer_format in match:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_hls_open':
                tmp_sup = 1
            elif supplier == 'limelight_hls_open': #NOTE: just guessing?
                tmp_sup = 2
            #m3u8_breakdown = re.compile('(.+?)iptv.+?m3u8(.+?)$').findall(m3u8_url)
            # print m3u8_url
            m3u8_html = OpenURL(m3u8_url)
            #print m3u8_html.encode("utf8")
            m3u8_match = re.compile('BANDWIDTH=(.+?),.*?CODECS="(.+?)"\n(.+?)\n').findall(m3u8_html)
            for bandwidth, codecs, stream in m3u8_match:
                #print bandwidth
                #print codecs
                #print stream
                #url = "%s%s%s" % (m3u8_breakdown[0][0], stream, m3u8_breakdown[0][1])
                url = stream
                retlist.append((tmp_sup, bitrate, url, encoding))

    ''' TODO
        # print "No streams found"
        check_geo = re.search(
            '<error id="geolocation"/>', html)
        if check_geo:
            # print "Geoblock detected, raising error message"
            dialog = xbmcgui.Dialog()
            dialog.ok(translation(32000), translation(32001))
            raise
    '''
    #print retlist
    #print match
    return retlist, match

    
def CheckAutoplay(name, url, iconimage, plot, aired=None):
    if ADDON.getSetting('streams_autoplay') == 'true':
        AddMenuEntry(name, url, 202, iconimage, plot, '', aired=aired)
    else:
        AddMenuEntry(name, url, 122, iconimage, plot, '', aired=aired)


def ScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    # Search for standard programmes.
    stream_id_st = re.compile('"vpid":"(.+?)"').findall(html)
    # Optionally, Signed programmes can be searched for. These have a different ID.
    if ADDON.getSetting('search_signed') == 'true':
        stream_id_sl = re.compile('data-download-sl="bbc-ipd:download/.+?/(.+?)/sd/').findall(html)
    else:
        stream_id_sl = []
    # Optionally, Audio Described programmes can be searched for. These have a different ID.
    if ADDON.getSetting('search_ad') == 'true':
        url_ad = re.compile('<a href="(.+?)" class="version link watch-ad-on"').findall(html)
        url_tmp = "http://www.bbc.co.uk%s" % url_ad[0]
        html = OpenURL(url_tmp)
        stream_id_ad = re.compile('"vpid":"(.+?)"').findall(html)
        # print stream_id_ad
    else:
        stream_id_ad = []
    return {'stream_id_st': stream_id_st, 'stream_id_sl': stream_id_sl, 'stream_id_ad': stream_id_ad}


def RadioScrapeAvailableStreams(url):
    # Open page and retrieve the stream ID
    html = OpenURL(url)
    # Search for standard programmes.
    stream_id_st = re.compile('"vpid":"(.+?)"').findall(html)
    return stream_id_st


def AddAvailableStreamItem(name, url, iconimage, description):
    """Play a streamm based on settings for preferred catchup source and bitrate."""
    stream_ids = ScrapeAvailableStreams(url)
    if stream_ids['stream_id_ad']:
        streams_all = ParseStreams(stream_ids['stream_id_ad'])
    elif stream_ids['stream_id_sl']:
        streams_all = ParseStreams(stream_ids['stream_id_sl'])
    else:
        streams_all = ParseStreams(stream_ids['stream_id_st'])
    if streams_all[1]:
        # print "Setting subtitles URL"
        subtitles_url = streams_all[1][0]
        # print subtitles_url
    else:
        subtitles_url = ''
    streams = streams_all[0]
    source = int(ADDON.getSetting('catchup_source'))
    bitrate = int(ADDON.getSetting('catchup_bitrate'))
    # print "Selected source is %s"%source
    # print "Selected bitrate is %s"%bitrate
    # print streams
    if source > 0:
        if bitrate > 0:
            # Case 1: Selected source and selected bitrate
            match = [x for x in streams if ((x[0] == source) and (x[1] == bitrate))]
            if len(match) == 0:
                # Fallback: Use same bitrate but different supplier.
                match = [x for x in streams if (x[1] == bitrate)]
                if len(match) == 0:
                    # Second Fallback: Use any lower bitrate from selected source.
                    match = [x for x in streams if (x[0] == source) and (x[1] in range(1, bitrate))]
                    match.sort(key=lambda x: x[1], reverse=True)
                    if len(match) == 0:
                        # Third Fallback: Use any lower bitrate from any source.
                        match = [x for x in streams if (x[1] in range(1, bitrate))]
                        match.sort(key=lambda x: x[1], reverse=True)
        else:
            # Case 2: Selected source and any bitrate
            match = [x for x in streams if (x[0] == source)]
            if len(match) == 0:
                # Fallback: Use any source and any bitrate
                match = streams
            match.sort(key=lambda x: x[1], reverse=True)
    else:
        if bitrate > 0:
            # Case 3: Any source and selected bitrate
            match = [x for x in streams if (x[1] == bitrate)]
            if len(match) == 0:
                # Fallback: Use any source and any lower bitrate
                match = streams
                match = [x for x in streams if (x[1] in range(1, bitrate))]
                match.sort(key=lambda x: x[1], reverse=True)
        else:
            # Case 4: Any source and any bitrate
            # Play highest available bitrate
            match = streams
            match.sort(key=lambda x: x[1], reverse=True)
    PlayStream(name, match[0][2], iconimage, description, subtitles_url)


def GetAvailableStreams(name, url, iconimage, description):
    """Calls AddAvailableStreamsDirectory based on user settings"""
    #print url
    stream_ids = ScrapeAvailableStreams(url)
    AddAvailableStreamsDirectory(name, stream_ids['stream_id_st'], iconimage, description)
    # If we searched for Audio Described programmes and they have been found, append them to the list.
    if stream_ids['stream_id_ad']:
        AddAvailableStreamsDirectory(name + ' - (Audio Described)', stream_ids['stream_id_ad'], iconimage, description)
    # If we search for Signed programmes and they have been found, append them to the list.
    if stream_ids['stream_id_sl']:
        AddAvailableStreamsDirectory(name + ' - (Signed)', stream_ids['stream_id_sl'], iconimage, description)


def RadioGetAvailableStreams(name, url, iconimage, description):
    """Calls AddAvailableStreamsDirectory based on user settings"""
    #print url
    stream_ids = RadioScrapeAvailableStreams(url)
    RadioAddAvailableStreamsDirectory(name, stream_ids, iconimage, description)



def AddAvailableLiveStreamItem(name, channelname, iconimage):
    """Play a live stream based on settings for preferred live source and bitrate."""
    stream_bitrates = [9999, 345, 501, 923, 1470, 1700, 2128, 2908, 3628, 5166]
    if int(ADDON.getSetting('live_source')) == 1:
        providers = [('ak', 'Akamai')]
    elif int(ADDON.getSetting('live_source')) == 2:
        providers = [('llnw', 'Limelight')]
    else:
        providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    bitrate_selected = int(ADDON.getSetting('live_bitrate'))
    for provider_url, provider_name in providers:
        # First we query the available streams from this website
        if channelname == 's4cpbs':
            url = 'http://a.files.bbci.co.uk/media/live/manifests/hds/pc/%s/%s.f4m' % (
                provider_url, channelname)
        else:
            url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio_video/simulcast/hds/uk/pc/%s/%s.f4m' % (
                provider_url, channelname)
        html = OpenURL(url)
        # Use regexp to get the different versions using various bitrates
        match = re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html)
        streams_available = []
        for address, bitrate in match:
            url = address.replace('f4m', 'm3u8')
            streams_available.append((int(bitrate), url))
        streams_available.sort(key=lambda x: x[0], reverse=True)
        # print streams_available
        # Play the prefered option
        if bitrate_selected > 0:
            match = [x for x in streams_available if (x[0] == stream_bitrates[bitrate_selected])]
            if len(match) == 0:
                # Fallback: Use any lower bitrate from any source.
                match = [x for x in streams_available if (x[0] in range(1, stream_bitrates[bitrate_selected - 1] + 1))]
                match.sort(key=lambda x: x[0], reverse=True)
            # print "Selected bitrate is %s"%stream_bitrates[bitrate_selected]
            # print match
            # print "Playing %s from %s with bitrate %s"%(name, match[0][1], match [0][0])
            PlayStream(name, match[0][1], iconimage, '', '')
        # Play the fastest available stream of the preferred provider
        else:
            PlayStream(name, streams_available[0][1], iconimage, '', '')


def AddAvailableLiveStreamsDirectory(name, channelname, iconimage):
    """Retrieves the available live streams for a channel

    Args:
        name: only used for displaying the channel.
        iconimage: only used for displaying the channel.
        channelname: determines which channel is queried.
    """
    providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    streams = []
    for provider_url, provider_name in providers:
        # First we query the available streams from this website
        if channelname == 's4cpbs':
            url = 'http://a.files.bbci.co.uk/media/live/manifests/hds/pc/%s/%s.f4m' % (
                provider_url, channelname)
        else:
            url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio_video/simulcast/hds/uk/pc/%s/%s.f4m' % (
                provider_url, channelname)
        html = OpenURL(url)
        # Use regexp to get the different versions using various bitrates
        match = re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html)
        # Add provider name to the stream list.
        streams.extend([list(stream) + [provider_name] for stream in match])

    # Add each stream to the Kodi selection menu.
    for address, bitrate, provider_name in sorted(streams, key=lambda x: int(x[1]), reverse=True):
        url = address.replace('f4m', 'm3u8')
        # For easier selection use colors to indicate high and low bitrate streams
        bitrate = int(bitrate)
        if bitrate > 2100:
            color = 'green'
        elif bitrate > 1000:
            color = 'yellow'
        elif bitrate > 600:
            color = 'orange'
        else:
            color = 'red'

        title = name + ' - [I][COLOR %s]%0.1f Mbps[/COLOR] [COLOR white]%s[/COLOR][/I]' % (
            color, bitrate / 1000, provider_name)
        # Finally add them to the selection menu.
        AddMenuEntry(title, url, 201, iconimage, '', '')

        
def RadioAddAvailableLiveStreamsDirectory(name, channelname, iconimage):
    """Retrieves the available live streams for a channel

    Args:
        name: only used for displaying the channel.
        iconimage: only used for displaying the channel.
        channelname: determines which channel is queried.
    """
    providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    streams = []
    for provider_url, provider_name in providers:
        # First we query the available streams from this website
        #TODO add high bitrate streams
        url = 'http://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hds/uk/high/%s/%s.f4m' % (provider_url, channelname)
        html = OpenURL(url)
        #print html.encode("utf8")
        # Use regexp to get the different versions using various bitrates
        match = re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html)
        # Add provider name to the stream list.
        streams.extend([list(stream) + [provider_name] for stream in match])

    # Add each stream to the Kodi selection menu.
    for address, bitrate, provider_name in sorted(streams, key=lambda x: int(x[1]), reverse=True):
        url = address.replace('f4m', 'm3u8')
        # For easier selection use colors to indicate high and low bitrate streams
        bitrate = int(bitrate)
        if bitrate > 192:
            color = 'green'
        elif bitrate > 128:
            color = 'yellow'
        elif bitrate > 64:
            color = 'orange'
        else:
            color = 'red'

        title = name + ' - [I][COLOR %s]%d Kbps[/COLOR] [COLOR white]%s[/COLOR][/I]' % (
            color, bitrate , provider_name)
        # Finally add them to the selection menu.
        #TODO find radio icons
        AddMenuEntry(title, url, 201, '', '', '')
        
        

def InitialiseCookieJar():
    cookie_file = os.path.join(DIR_USERDATA,'iplayer.cookies')
    cj = cookielib.LWPCookieJar(cookie_file)
    if(os.path.exists(cookie_file)):
        try:
            cj.load(ignore_discard=True, ignore_expires=True)
        except:
            xbmcgui.Dialog().notification(translation(32000), translation(32002), xbmcgui.NOTIFICATION_ERROR)
    return cj


def OpenURL(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:38.0) Gecko/20100101 Firefox/43.0'}
    try:
        r = requests.get(url, headers=headers, cookies=cookie_jar)
    except requests.exceptions.RequestException as e:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(32000), "%s" % e)
        sys.exit(1)
    try:
        for cookie in r.cookies:
            cookie_jar.set_cookie(cookie)
        cookie_jar.save(ignore_discard=True, ignore_expires=True)
    except:
        pass
    return HTMLParser.HTMLParser().unescape(r.content.decode('utf-8'))


def OpenURLPost(url, post_data):
    headers = {
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:38.0) Gecko/20100101 Firefox/43.0',
               'Host':'ssl.bbc.co.uk',
               'Accept':'*/*',
               'Referer':'https://ssl.bbc.co.uk/id/signin',
               'Content-Type':'application/x-www-form-urlencoded'}
    try:
        r = requests.post(url, headers=headers, data=post_data, allow_redirects=False, cookies=cookie_jar)
    except requests.exceptions.RequestException as e:
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(32000), "%s" % e)
        sys.exit(1)
    try:
        for cookie in r.cookies:
            cookie_jar.set_cookie(cookie)
        cookie_jar.save(ignore_discard=True, ignore_expires=True)
    except:
        pass
    return r


def PlayStream(name, url, iconimage, description, subtitles_url):
    html = OpenURL(url)
    check_geo = re.search(
        '<H1>Access Denied</H1>', html)
    if check_geo or not html:
        # print "Geoblock detected, raising error message"
        dialog = xbmcgui.Dialog()
        dialog.ok(translation(32000), translation(32001))
        raise
    liz = xbmcgui.ListItem(name, iconImage='DefaultVideo.png', thumbnailImage=iconimage)
    liz.setInfo(type='Video', infoLabels={'Title': name})
    liz.setProperty("IsPlayable", "true")
    liz.setPath(url)
    # print url
    # print subtitles_url
    # print name
    # print iconimage
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        subtitles_file = download_subtitles(subtitles_url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
    if subtitles_url and ADDON.getSetting('subtitles') == 'true':
        # Successfully started playing something?
        while True:
            if xbmc.Player().isPlaying():
                break
            else:
                xbmc.sleep(500)
        xbmc.Player().setSubtitles(subtitles_file)


def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
    return param


# Creates a 'urlencoded' string from a unicode input
def utf8_quote_plus(unicode):
    return urllib.quote_plus(unicode.encode('utf-8'))


# Gets a unicode string from a 'urlencoded' string
def utf8_unquote_plus(str):
    return urllib.unquote_plus(str).decode('utf-8')


def AddMenuEntry(name, url, mode, iconimage, description, subtitles_url, aired=None, resolution=None, logged_in=False):
    """Adds a new line to the Kodi list of playables.

    It is used in multiple ways in the plugin, which are distinguished by modes.
    """
    listitem_url = (sys.argv[0] + "?url=" + utf8_quote_plus(url) + "&mode=" + str(mode) +
                    "&name=" + utf8_quote_plus(name) +
                    "&iconimage=" + utf8_quote_plus(iconimage) +
                    "&description=" + utf8_quote_plus(description) +
                    "&subtitles_url=" + utf8_quote_plus(subtitles_url) +
                    "&logged_in=" + str(logged_in))

    if aired:
        ymd = aired.split('-')
        date_string = ymd[2] + '/' + ymd[1] + '/' + ymd[0]
    else:
        date_string = ""

    # Modes 201-299 will create a new playable line, otherwise create a new directory line.
    if mode in (201, 202, 203):
        isFolder = False
    else:
        isFolder = True

    listitem = xbmcgui.ListItem(label=name, label2=description,
                                iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    if aired:
        listitem.setInfo("video", {
            "title": name,
            "plot": description,
            "plotoutline": description,
            "date": date_string,
            "aired": aired})
    else:
        listitem.setInfo("video", {
            "title": name,
            "plot": description,
            "plotoutline": description})

    video_streaminfo = {'codec': 'h264'}
    if not isFolder:
        if resolution:
            resolution = resolution.split('x')
            video_streaminfo['aspect'] = round(int(resolution[0]) / int(resolution[1]), 2)
            video_streaminfo['width'] = resolution[0]
            video_streaminfo['height'] = resolution[1]
        listitem.addStreamInfo('video', video_streaminfo)
        listitem.addStreamInfo('audio', {'codec': 'aac', 'language': 'en', 'channels': 2})
        if subtitles_url:
            listitem.addStreamInfo('subtitle', {'language': 'en'})

    listitem.setProperty("IsPlayable", str(not isFolder).lower())
    listitem.setProperty("IsFolder", str(isFolder).lower())
    listitem.setProperty("Property(Addon.Name)", "iPlayer WWW")
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),
                                url=listitem_url, listitem=listitem, isFolder=isFolder)
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')
    return True

re_subtitles = re.compile('^\s*<p.*?begin=\"(.*?)(\.([0-9]+))?\"\s+.*?end=\"(.*?)(\.([0-9]+))?\"\s*>(.*?)</p>')


def download_subtitles(url):
    # Download and Convert the TTAF format to srt
    # SRT:
    # 1
    # 00:01:22,490 --> 00:01:26,494
    # Next round!
    #
    # 2
    # 00:01:33,710 --> 00:01:37,714
    # Now that we've moved to paradise, there's nothing to eat.
    #

    # TT:
    # <p begin="0:01:12.400" end="0:01:13.880">Thinking.</p>
    outfile = os.path.join(DIR_USERDATA, 'iplayer.srt')
    # print "Downloading subtitles from %s to %s"%(url, outfile)
    fw = open(outfile, 'w')

    if not url:
        fw.write("1\n0:00:00,001 --> 0:01:00,001\nNo subtitles available\n\n")
        fw.close()
        return

    txt = OpenURL(url)

    # print txt

    i = 0
    prev = None

    # some of the subtitles are a bit rubbish in particular for live tv
    # with lots of needless repeats. The follow code will collapse sequences
    # of repeated subtitles into a single subtitles that covers the total time
    # period. The downside of this is that it would mess up in the rare case
    # where a subtitle actually needs to be repeated
    for line in txt.split('\n'):
        entry = None
        m = re_subtitles.match(line)
        # print line
        # print m
        if m:
            if(m.group(3)):
                start_mil = "%s000" % m.group(3) # pad out to ensure 3 digits
            else:
                start_mil = "000"
            if(m.group(6)):
                end_mil = "%s000" % m.group(6)
            else:
                end_mil = "000"

            ma = {'start': m.group(1),
                  'start_mil': start_mil[:3],
                  'end': m.group(4),
                  'end_mil': end_mil[:3],
                  'text': m.group(7)}

            # ma['text'] = ma['text'].replace('&amp;', '&')
            # ma['text'] = ma['text'].replace('&gt;', '>')
            # ma['text'] = ma['text'].replace('&lt;', '<')
            ma['text'] = ma['text'].replace('<br />', '\n')
            ma['text'] = ma['text'].replace('<br/>', '\n')
            ma['text'] = re.sub('<.*?>', '', ma['text'])
            ma['text'] = re.sub('&#[0-9]+;', '', ma['text'])
            # ma['text'] = ma['text'].replace('<.*?>', '')
            # print ma
            if not prev:
                # first match - do nothing wait till next line
                prev = ma
                continue

            if prev['text'] == ma['text']:
                # current line = previous line then start a sequence to be collapsed
                prev['end'] = ma['end']
                prev['end_mil'] = ma['end_mil']
            else:
                i += 1
                entry = "%d\n%s,%s --> %s,%s\n%s\n\n" % (
                    i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], prev['text'])
                prev = ma
        elif prev:
            i += 1
            entry = "%d\n%s,%s --> %s,%s\n%s\n\n" % (
                i, prev['start'], prev['start_mil'], prev['end'], prev['end_mil'], prev['text'])

        if entry:
            fw.write(entry)

    fw.close()
    return outfile


def SignInBBCiD():
    #Below is required to get around an ssl issue
    urllib3.disable_warnings()
    sign_in_url="https://ssl.bbc.co.uk/id/signin"

    username=ADDON.getSetting('bbc_id_username')
    password=ADDON.getSetting('bbc_id_password')

    post_data={
               'unique': username,
               'password': password,
               'rememberme':'0'}
    r = OpenURLPost(sign_in_url, post_data)
    if (r.status_code == 302):
        xbmcgui.Dialog().notification(translation(31008), translation(31009))
    else:
        xbmcgui.Dialog().notification(translation(31008), translation(31010))


def SignOutBBCiD():
    sign_out_url="https://ssl.bbc.co.uk/id/signout"
    OpenURL(sign_out_url)


def StatusBBCiD():
    status_url="https://ssl.bbc.co.uk/id/status"
    html=OpenURL(status_url)
    if("You are signed in" in html):
        return True
    return False


def CheckLogin(logged_in):
    if(logged_in == True or StatusBBCiD() == True):
        logged_in = True
        return True
    elif ADDON.getSetting('bbc_id_enabled') != 'true':
        xbmcgui.Dialog().ok(translation(31008), translation(31011))
    else:
        attemptLogin = xbmcgui.Dialog().yesno(translation(31008), translation(31012))
        if attemptLogin:
            SignInBBCiD()
            if(StatusBBCiD()):
                xbmcgui.Dialog().notification(translation(31008), translation(31009))
                logged_in = True;
                return True;
            else:
                xbmcgui.Dialog().notification(translation(31008), translation(31010))

    return False

def ListWatching(logged_in):

    if(CheckLogin(logged_in) == False):
        CATEGORIES()
        return

    identity_cookie = None
    for cookie in cookie_jar:
        if (cookie.name == 'IDENTITY'):
            identity_cookie = cookie.value
            break
    url = "https://ibl.api.bbci.co.uk/ibl/v1/user/watching?identity_cookie=%s" % identity_cookie
    html = OpenURL(url)
    json_data = json.loads(html)
    watching_list = json_data.get('watching').get('elements')
    for watching in watching_list:
        programme = watching.get('programme')
        episode = watching.get('episode')
        title = episode.get('title')
        subtitle = episode.get('subtitle')
        if(subtitle):
            title += ", " + subtitle
        episode_id = episode.get('id')
        plot = episode.get('synopses').get('large') or " "
        aired = episode.get('release_date')
        image_url = ParseImageUrl(episode.get('images').get('standard'))
        aired = ParseAired(aired)
        url="http://www.bbc.co.uk/iplayer/episode/%s" % (episode_id)
        CheckAutoplay(title, url, image_url, plot, aired)


def ListFavourites(logged_in):

    if(CheckLogin(logged_in) == False):
        CATEGORIES()
        return

    """Scrapes all episodes of the favourites page."""
    html = OpenURL('http://www.bbc.co.uk/iplayer/usercomponents/favourites/programmes.json')
    json_data = json.loads(html)
    # favourites = json_data.get('favourites')
    programmes = json_data.get('programmes')
    for programme in programmes:
        id = programme.get('id')
        url = "http://www.bbc.co.uk/iplayer/brand/%s" % (id)
        title = programme.get('title')
        initial_child = programme.get('initial_children')[0]
        subtitle = initial_child.get('subtitle')
        episode_title = title
        if subtitle:
            episode_title = title + ' - ' + subtitle
        image=initial_child.get('images')
        image_url=ParseImageUrl(image.get('standard'))
        synopses = initial_child.get('synopses')
        plot = synopses.get('small')
        aired = FirstShownToAired(initial_child.get('release_date'))
        CheckAutoplay(episode_title, url, image_url, plot, aired)
        more = programme.get('count')
        if more:
            episodes_url = "http://www.bbc.co.uk/iplayer/episodes/" + id
            AddMenuEntry('[B]%s[/B] - %s %s' % (title, more, translation(31013)),
                         episodes_url, 128, image_url, '', '')

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)

cookie_jar = InitialiseCookieJar()
params = get_params()
print params
content_type = None
url = None
name = None
mode = None
iconimage = None
description = None
subtitles_url = None
logged_in = False
keyword = None

try:
    content_type = utf8_unquote_plus(params["content_type"])
except:
    pass
try:
    url = utf8_unquote_plus(params["url"])
except:
    pass
try:
    name = utf8_unquote_plus(params["name"])
except:
    pass
try:
    iconimage = utf8_unquote_plus(params["iconimage"])
except:
    pass
try:
    mode = int(params["mode"])
except:
    pass
try:
    description = utf8_unquote_plus(params["description"])
except:
    pass
try:
    subtitles_url = utf8_unquote_plus(params["subtitles_url"])
except:
    pass
try:
    logged_in = params['logged_in'] == 'True'
except:
    pass
try:
    keyword = utf8_unquote_plus(params["keyword"])
except:
    pass


# These are the modes which tell the plugin where to go.
if mode is None or url is None or len(url) < 1:
    CATEGORIES()

# Modes 101-119 will create a main directory menu entry
elif mode == 101:
    ListLive()

elif mode == 102:
    ListAtoZ()

elif mode == 103:
    ListCategories()

elif mode == 104:
    Search(keyword)

elif mode == 105:
    ListMostPopular()

elif mode == 106:
    ListHighlights(url)

elif mode == 107:
    ListWatching(logged_in)

elif mode == 108:
    ListFavourites(logged_in)

elif mode == 109:
    ListChannelHighlights()
    
elif mode == 112:
    RadioListAtoZ()

elif mode == 113:
    RadioListLive()
    
elif mode == 114:
    RadioListGenres()
    
elif mode == 115:
    RadioSearch(keyword)

elif mode == 116:
    RadioListMostPopular()
    
    # Modes 121-199 will create a sub directory menu entry
elif mode == 121:
    GetEpisodes(url)

elif mode == 122:
    GetAvailableStreams(name, url, iconimage, description)

elif mode == 123:
    AddAvailableLiveStreamsDirectory(name, url, iconimage)

elif mode == 124:
    GetAtoZPage(url)

elif mode == 125:
    ListCategoryFilters(url)

elif mode == 126:
    GetFilteredCategory(url)

elif mode == 127:
    GetGroup(url)

elif mode == 128:
    ScrapeEpisodes(url)
    
elif mode == 131:
    RadioGetEpisodes(url)
    
elif mode == 132:
    url = "http://www.bbc.co.uk/programmes/" + url
    RadioGetAvailableStreams(name, url, iconimage, description)
    
elif mode == 133:
    RadioAddAvailableLiveStreamsDirectory(name, url, iconimage)

elif mode == 134:
    RadioGetAtoZPage(url)
    
elif mode == 135:
    RadioGetGenrePage(url)

# Modes 201-299 will create a playable menu entry, not a directory
elif mode == 201:
    PlayStream(name, url, iconimage, description, subtitles_url)

elif mode == 202:
    AddAvailableStreamItem(name, url, iconimage, description)

elif mode == 203:
    AddAvailableLiveStreamItem(name, url, iconimage)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

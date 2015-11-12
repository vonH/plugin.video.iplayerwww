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
from bs4 import BeautifulSoup
import cookielib
import pickle

import json

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
    AddMenuEntry(translation(31000), 'iplayer', 106, '', '', '')
    AddMenuEntry(translation(31017), 'url', 109, '', '', '')
    AddMenuEntry(translation(31001), 'url', 105, '', '', '')
    AddMenuEntry(translation(31002), 'url', 102, '', '', '')
    AddMenuEntry(translation(31003), 'url', 103, '', '', '')
    AddMenuEntry(translation(31004), 'url', 104, '', '', '')
    AddMenuEntry(translation(31005), 'url', 101, '', '', '')
    AddMenuEntry(translation(31006), 'url', 107, '', '', '')
    AddMenuEntry(translation(31007), 'url', 108, '', '', '')


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


'''Parses a string format %d %b %Y to %d/%n/%Y otherwise empty string'''
def ParseAired(aired):
    if aired:
        try:
            # Need to use equivelent for datetime.strptime() due to weird TypeError.
            return datetime.datetime(*(time.strptime(aired[0], '%d %b %Y')[0:6])).strftime('%d/%m/%Y')
        except ValueError:
            pass
    return ''


def ScrapeEpisodes(url):

    new_url = url

    more_pages = True
    while more_pages:
        more_pages = False

        html = OpenURL(new_url)
        soup = BeautifulSoup(html,"html.parser")

        #Programme Groups

        links = soup.find_all("li", {"class":["programme"]})
        for link in links:

            name = ''
            title_tag = link.find("div", {"class":"title"})
            if title_tag:
                name = ''.join(title_tag.stripped_strings)

            url = ''
            count = ''
            link_tag = link.find("a", {"class":"avail"})
            if link_tag:

                url = link_tag["href"].rsplit('/',1)[1]
                count = '(' + ' '.join(link_tag.stripped_strings) + ')'

                AddMenuEntry('%s %s' % (name, count), url, 121, '', '', '')

        #Episodes

        #<li class="list-item episode numbered" data-ip-id="b06pmn74">
        links = soup.find_all("li", {"class":["programme", "episode"]})
        for link in links:

            #<li class="list-item episode numbered" data-ip-id="b06pmn74">
            id = link["data-ip-id"]

            #<a class="list-item-link stat" data-object-type="episode-most-popular" data-page-branded="0" data-progress-state="" href="/iplayer/episode/b06pmn74/eastenders-10112015" title="EastEnders, 10/11/2015">
            url = ''
            link_tag = link.find("a", {"class":"stat"})
            if link_tag:
                url = 'http://www.bbc.co.uk/' + link_tag["href"]

            #<div class="title">EastEnders</div>
            title = ''
            title_tag = link.find("div", {"class":"title"})
            if title_tag:
                title = ''.join(title_tag.stripped_strings)

            #<div class="subtitle">10/11/2015</div>
            subtitle_tag = link.find("div", {"class":"subtitle"})
            subtitle = ''
            if subtitle_tag:
                subtitle = ''.join(subtitle_tag.stripped_strings)
                title = title + " - " + subtitle

            icon = ''
            #<div class="r-image" data-ip-src="http://ichef.bbci.co.uk/images/ic/336x189/p0370ptv.jpg" data-ip-type="episode">
            image_tag = link.find("div", {"class":"r-image"})
            if image_tag:
                icon = image_tag["data-ip-src"]
                icon = icon.replace('336x189', '832x468')

            #<p class="synopsis">Ronnie and Dean continue to fight for Roxy. Tensions grow at the Vic.</p>
            synopsis = ''
            synopsis_tag = link.find("p", {"class":"synopsis"})
            if synopsis_tag:
                synopsis = ''.join(synopsis_tag.stripped_strings)

            #<span class="release">\nFirst shown: 10 Nov 2015\n</span>
            aired = None
            release_tag = link.find("span", {"class":"release"})
            if release_tag:
                string = ''.join(release_tag.stripped_strings)
                release_parts = string.split(' ')
                year = release_parts[-1]
                month = release_parts[-2]
                monthDict={'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06', 'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
                if month in monthDict:
                    month = monthDict[month]
                    day = release_parts[-3].rjust(2,'0')
                else:
                    month = '01'
                    day = '01'
                aired = year + '-' + month + '-' + day

            CheckAutoplay(title, url, icon, synopsis, aired)

        #<span class="next txt"> <a href="/iplayer/categories/news/all?sort=atoz&amp;page=2"> Next <span class="tvip-hide">page</span>
        href = soup.select(".paginate .next a[href]")
        if href:
            new_url = 'http://www.bbc.co.uk' + href[0]["href"]
            more_pages = True

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)


def EvaluateSearch(url):
    """Parses the Search result page(s) for available programmes and lists them."""
    ScrapeEpisodes(url)


def ListCategories():
    """Parses the available categories and creates directories for selecting one of them.

    The category names are scraped from the website.
    """
    html = OpenURL('http://www.bbc.co.uk/iplayer')
    match = re.compile(
        '<a href="/iplayer/categories/(.+?)" class="stat">(.+?)</a>'
        ).findall(html.replace('amp;', ''))
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
        html.replace('amp;', ''),
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


def GetEpisodeInfo(url):
    html = OpenURL(url)
    soup = BeautifulSoup(html,"html.parser")

    #<title>BBC iPlayer - Around the World with the Go Jetters - Go Jetters - 4. The Sahara Desert, Africa</title>    
    name = 'the episode with no name'
    title_tag = soup.find(name="title")
    if title_tag:
        string = ''.join(title_tag.stripped_strings)
        string = re.sub(r"\s+", " ", string, flags=re.UNICODE)
        name_parts = string.split('-')[1:]
        name = '-'.join(name_parts)
        name = name.strip()
        
    #<meta name="description" content="Glitch makes a sandcastle around an oasis in the Sahara. Can the Go Jetters save the day?">
    description = 'no description'
    description_tag = soup.find("meta", {"name":"description"})
    if description_tag:
        description = description_tag["content"]
        
    #<meta property="og:image" content="http://ichef.bbci.co.uk/images/ic/1200x675/p0369f42.jpg">    
    icon = ''
    img_tag = soup.find(name="meta",property="og:image")
    if img_tag:
        icon = img_tag["content"]
        
    #<span class="release"> First shown: 5:20pm 29 Oct 2015 </span>
    aired = None
    release_tag = soup.find("span", {"class":"release"})
    if release_tag:
        string = ''.join(release_tag.stripped_strings)
        release_parts = string.split(' ')
        year = release_parts[-1]
        month = release_parts[-2]
        monthDict={'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04', 'May':'05', 'Jun':'06', 'Jul':'07', 'Aug':'08', 'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'}
        if month in monthDict:
            month = monthDict[month]
            day = release_parts[-3].rjust(2,'0')
        else:
            month = '01'
            day = '01'
        aired = year + '-' + month + '-' + day
    
    return (name, description, icon, aired)


def ListChannelHighlights():
    """Creates a list directories linked to the highlights section of each channel."""
    channel_list = [
        ('bbcone', 'bbc_one', 'BBC One'),
        ('bbctwo', 'bbc_two', 'BBC Two'),
        ('bbcthree', 'bbc_three', 'BBC Three'),
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


def ListHighlights(url):
    """Creates a list of the programmes in the highlights section.
    All entries are scraped of the intro page and the pages linked from the intro page.
    """
    info = dict()
    if ADDON.getSetting('find_missing_images') == 'true':

        pDialog = xbmcgui.DialogProgressBG()
        pDialog.create('iPlayer: Finding images...')

        dataPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')
        path = os.path.join(dataPath, 'episode_info')
        if os.path.isfile(path):
            with open(path,'rb') as store:
                try:
                    info = pickle.load(store)
                    now = time.time()
                    expire = now - 60*60*24*30
                    for id in info.keys():
                        (unixtime, episode_name, episode_description, episode_icon, episode_aired) = info[id]
                        if unixtime < expire:
                            del info[id]
                except:
                    pass
                store.close()
    
    html = OpenURL('http://www.bbc.co.uk/%s' % url)
    soup = BeautifulSoup(html,"html.parser")
    
    groups = set()
    
    # Groups
    hrefs = set()
    for link in soup.find_all(href=re.compile("iplayer/group")):

        link = link.parent
        href = link.a["href"]
        if href in hrefs:
            continue
        hrefs.add(href)
        url = href.rsplit('/',1)[1]

        title = link.find(class_=["single-item__title","grouped-item__title","grouped-items__title"])
        name = "unnamed group"
        group = 'unnamed group'
        if title:
            string = ''.join(title.stripped_strings)
            group = string
            name = re.sub(r"\s+", " ", string, flags=re.UNICODE)

        link = link.parent
        title = link.find(class_=["single-item__item-count","grouped-item__item-count","grouped-items__item-count"])
        count = ''
        if title:
            string = ''.join(title.stripped_strings)
            string = re.sub(r"\s+", " ", string, flags=re.UNICODE)
            count = '(' + string + ')'
            if string.endswith('programmes'):
                groups.add(group)
                AddMenuEntry('  %s - %s %s' % (translation(31014), name, count), url, 127, '', '', '')
            else:
                AddMenuEntry('%s %s' % (name, count), url, 121, '', '', '')

    ids = set()
    total = 0
    processed = 0

    # inner function
    def ProcessLinks(soup, ids, processed, group_title=''):   

        links = soup.find_all(href=re.compile("episode"))
        total_episodes = len(links)
        episode = 0
        for link in links :
    
            href = link["href"]
            id = href.rsplit('/')[3]
            if id in ids:
                continue
            ids.add(id)
            url = 'http://www.bbc.co.uk' + href

            name = 'the episode with no name'
            title = link.find(class_=["single-item__title","group-item__title","grouped-items__title"])
            if title:
                string = ''.join(title.stripped_strings)
                name = group_title + re.sub(r"\s+", " ", string, flags=re.UNICODE)
                subtitle = link.find(class_=["single-item__subtitle","group-item__subtitle","grouped-items__subtitle"])
                if subtitle:
                    string = ''.join(subtitle.stripped_strings)
                    #TODO inconsistent: sometimes this is full of the plot summary (eg bbcone Doctor Who)
                    name = name + ' - ' + re.sub(r"\s+", " ", string, flags=re.UNICODE)

            if ADDON.getSetting('find_missing_images') == 'true':
                fraction = 100.0 / total
                episode_percent = int(fraction * episode / total_episodes)
                episode = episode + 1
                percent = int(100.0 * processed / total)
                percent = percent + episode_percent
                pDialog.update(percent, "iPlayer: Finding images...", name)
                #TODO this doesn't work
                #if pDialog.iscanceled():
                #    CATEGORIES

            description = 'no description'
            aired = None
            desc = link.find(class_=["single-item__overlay__desc","group-item__overlay__desc","grouped-items__overlay__desc"])
            if desc:
                string = ''.join(desc.stripped_strings)
                description = re.sub(r"\s+", " ", string, flags=re.UNICODE)
                subdesc = link.find(class_=["single-item__overlay__subtitle","group-item__overlay__subtitle","grouped-items__overlay__subtitle"])
                if subdesc:
                    string = ''.join(subdesc.stripped_strings)
                    aired = re.sub(r"\s+", " ", string, flags=re.UNICODE)
                    aired = ParseAired(aired)          
      
            icon = ''
            image = link.find(class_=["single-item__img","group-item__img","grouped-items__img"])
            if image:
                rimage = image.find(class_="r-image")
                if rimage:
                    icon = rimage["data-ip-src"]    

            if ADDON.getSetting('find_missing_images') == 'true':
                if id in info:
                    (unixtime, episode_name, episode_description, episode_icon, episode_aired) = info[id]
                else:
                    (episode_name, episode_description, episode_icon, episode_aired) = GetEpisodeInfo(url)
                name = episode_name
                icon = episode_icon
                description = episode_description
                aired = episode_aired
                info[id] = (time.time(), episode_name, episode_description, episode_icon, episode_aired)

            if icon:
                icon_id = icon.rsplit('/',1)[-1]
                icon = 'http://ichef.bbci.co.uk/images/ic/832x468/' + icon_id
            else:
                icon = 'DefaultVideo.png'

            CheckAutoplay(name, url, icon, description, aired)

        processed = processed + 1
        return (ids, info, processed)


    # Group Episodes
    group_tags = soup.find_all(class_="grouped-items")
    total = len(group_tags) + 1
    for group_tag in group_tags:

        group_title = group_tag["data-group-name"] or ''
        if group_title in groups:
            group_title = ''
        else:
            group_title = group_title + ' - '

        (ids, info, processed) = ProcessLinks(group_tag, ids, processed, group_title)

    # Episodes    
    (ids, info, processed) = ProcessLinks(soup, ids, processed )

    if ADDON.getSetting('find_missing_images') == 'true':
        dataPath = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8')
        path = os.path.join(dataPath, 'episode_info')
        store = open(path,'wb')
        pickle.dump(info, store)
        store.close()
        pDialog.close()

    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_VIDEO_TITLE)
    if ADDON.getSetting('find_missing_images') == 'true':
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_DATE)


def ListMostPopular():
    """Scrapes all episodes of the most popular page."""
    ScrapeEpisodes("http://www.bbc.co.uk/iplayer/group/most-popular")


def Search():
    """Simply calls the online search function. The search is then evaluated in EvaluateSearch."""
    search_entered = ''
    keyboard = xbmc.Keyboard(search_entered, 'Search iPlayer')
    keyboard.doModal()
    if keyboard.isConfirmed():
        search_entered = keyboard.getText() .replace(' ', '%20')  # sometimes you need to replace spaces with + or %20
        if search_entered is None:
            return False
    NEW_URL = 'http://www.bbc.co.uk/iplayer/search?q=%s' % search_entered
    EvaluateSearch(NEW_URL)


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


def ParseStreams(stream_id):
    retlist = []
    # print "Parsing streams for PID: %s"%stream_id[0]
    # Open the page with the actual strem information and display the various available streams.
    NEW_URL = "http://open.live.bbc.co.uk/mediaselector/5/select/version/2.0/mediaset/iptv-all/vpid/%s" % stream_id[0]
    html = OpenURL(NEW_URL)
    # Parse the different streams and add them as new directory entries.
    match = re.compile(
        'connection authExpires=".+?href="(.+?)".+?supplier="mf_(.+?)".+?transferFormat="(.+?)"'
        ).findall(html.replace('amp;', ''))
    for m3u8_url, supplier, transfer_format in match:
        tmp_sup = 0
        tmp_br = 0
        if transfer_format == 'hls':
            if supplier == 'akamai_uk_hls':
                tmp_sup = 1
            elif supplier == 'limelight_uk_hls':
                tmp_sup = 2
            m3u8_breakdown = re.compile('(.+?)iptv.+?m3u8(.+?)$').findall(m3u8_url)
            # print m3u8_url
            m3u8_html = OpenURL(m3u8_url)
            m3u8_match = re.compile('BANDWIDTH=(.+?),.+?RESOLUTION=(.+?)\n(.+?)\n').findall(m3u8_html)
            for bandwidth, resolution, stream in m3u8_match:
                # print bandwidth
                # print resolution
                # print stream
                url = "%s%s%s" % (m3u8_breakdown[0][0], stream, m3u8_breakdown[0][1])
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
        ).findall(html.replace('amp;', ''))
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
    match = re.compile('service="captions".+?connection href="(.+?)"').findall(html.replace('amp;', ''))
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
    stream_ids = ScrapeAvailableStreams(url)
    AddAvailableStreamsDirectory(name, stream_ids['stream_id_st'], iconimage, description)
    # If we searched for Audio Described programmes and they have been found, append them to the list.
    if stream_ids['stream_id_ad']:
        AddAvailableStreamsDirectory(name + ' - (Audio Described)', stream_ids['stream_id_ad'], iconimage, description)
    # If we search for Signed programmes and they have been found, append them to the list.
    if stream_ids['stream_id_sl']:
        AddAvailableStreamsDirectory(name + ' - (Signed)', stream_ids['stream_id_sl'], iconimage, description)


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
        match = re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html.replace('amp;', ''))
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
        match = re.compile('href="(.+?)".+?bitrate="(.+?)"').findall(html.replace('amp;', ''))
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:38.0) Gecko/20100101 Firefox/41.0'}
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
    return r.content.decode('utf-8')


def OpenURLPost(url, post_data):
    headers = {
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:38.0) Gecko/20100101 Firefox/41.0',
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


#Creates a 'urlencoded' string from a unicode input
def utf8_quote_plus(unicode):
    return urllib.quote_plus(unicode.encode('utf-8'))


#Gets a unicode string from a 'urlencoded' string
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
        date_string = "01/01/1970"

    # Modes 201-299 will create a new playable line, otherwise create a new directory line.
    if mode in (201, 202, 203):
        isFolder = False
    else:
        isFolder = True

    listitem = xbmcgui.ListItem(label=name, label2=description,
                                iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    listitem.setInfo("video", {
        "title": name,
        "plot": description,
        "plotoutline": description,
        'date': date_string,
        'aired': aired})

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

            ma['text'] = ma['text'].replace('&amp;', '&')
            ma['text'] = ma['text'].replace('&gt;', '>')
            ma['text'] = ma['text'].replace('&lt;', '<')
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
    #favourites = json_data.get('favourites')
    programmes = json_data.get('programmes')
    for programme in programmes:
        id = programme.get('id')
        url = "http://www.bbc.co.uk/iplayer/brand/%s" % (id)
        title = programme.get('title')
        initial_child = programme.get('initial_children')[0]
        image=initial_child.get('images')
        image_url=ParseImageUrl(image.get('standard'))
        synopses = initial_child.get('synopses')
        plot = synopses.get('small')
        aired = ParseAired(initial_child.get('release_date'))
        CheckAutoplay(title, url, image_url, plot, aired)


cookie_jar = InitialiseCookieJar()
params = get_params()
url = None
name = None
mode = None
iconimage = None
description = None
subtitles_url = None
logged_in = False

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
    Search()

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

# Modes 121-199 will create a sub directory menu entry
elif mode == 121:
    new_url = 'http://www.bbc.co.uk/iplayer/episodes/%s' % url
    ScrapeEpisodes(new_url)

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
    new_url = "http://www.bbc.co.uk/iplayer/group/%s" % url
    ScrapeEpisodes(new_url)

# Modes 201-299 will create a playable menu entry, not a directory
elif mode == 201:
    PlayStream(name, url, iconimage, description, subtitles_url)

elif mode == 202:
    AddAvailableStreamItem(name, url, iconimage, description)

elif mode == 203:
    AddAvailableLiveStreamItem(name, url, iconimage)

xbmcplugin.endOfDirectory(int(sys.argv[1]))

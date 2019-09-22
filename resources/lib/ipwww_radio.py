# -*- coding: utf-8 -*-

import sys
import os
import re
from operator import itemgetter
import random
import json
import HTMLParser
import datetime
import time
from bs4 import BeautifulSoup
from ipwww_cache import Cache
from ipwww_common import translation, AddMenuEntry, OpenURL, \
    CreateBaseDirectory
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

ADDON_ID = "plugin.video.iplayerwww"
ADDON = xbmcaddon.Addon(id=ADDON_ID)
SILENCE_MP3 = xbmc.translatePath("special://home/addons/plugin.video.iplayerwww/media/silence.mp3")
PROP_SEARCH_ENTERED = "%s_audio_search_entered" % ADDON_ID
PROP_LOG_DEBUG = "%s_audio_log_debug" % ADDON_ID
MODE_NOOP = 99
MODE_LIVE_ITEM = 213
MODE_LIVE_DIR = 133
MODE_LIVE_PLAY = 214
MODE_CATCHUP_ITEM = 212
MODE_CATCHUP_DIR = 132
MODE_CATCHUP_PLAY = 211
MODE_AZ_PAGE = 138
MODE_LIST_SUBCATS = 141
MODE_CATEGORY_PAGE = 137
MODE_PROGRAMMES_PAGE = 136
MODE_EPISODES = 131
MODE_SEARCH = 115
MODE_SEARCH_PAGE = 140
MODE_LIVE = 113
MODE_AZ = 112
MODE_CATEGORIES = 114
CACHE = Cache("radio")


def Init(mode):
    UpdateLogging()
    UpdateCache()


def DebugLog(fmt, *text):
    """Write to Kodi debug log"""
    log_debug = xbmcgui.Window(10000).getProperty(PROP_LOG_DEBUG)
    if log_debug != "True":
        return
    try:
        msg = fmt % text
    except Exception as err:
        msg = "DebugLog: error: %s: %s: %s" % (err, fmt, text)
    if isinstance(msg, unicode):
        msg = msg.encode("utf-8", "replace")
    xbmc.log("%s: %s: %s" % (ADDON_ID, __name__, msg), level=xbmc.LOGDEBUG)


def UpdateLogging():
    """Capture value of Kodi debug log setting"""
    rpc_cmd = {
        'jsonrpc': '2.0',
        'method': 'Settings.GetSettingValue',
        'params': {'setting': 'debug.showloginfo'},
        'id': '1'
    }
    json_data = json.loads(xbmc.executeJSONRPC(json.dumps(rpc_cmd)))
    log_debug = str(json_data.get("result", {}).get("value", True))
    xbmcgui.Window(10000).setProperty(PROP_LOG_DEBUG, log_debug)


def FormatText(fmt, *text):
    """Conditionally apply text formatting"""
    if ADDON.getSetting("audio_format_text") == "false":
        fmt = re.sub(r'\[/?([B|I]|COLOR)[^]]*\]', "", fmt, 0, re.I)
    try:
        msg = fmt % text
    except Exception as err:
        msg = "error: %s: %s: %s" % (err, fmt, text)
        DebugLog("FormatText: %s", msg)
    return msg


def UpdateCache():
    """Update cache configuration and trim"""
    cache_pages = int(ADDON.getSetting("audio_cache_pages"))
    CACHE.enabled = True
    CACHE.memcache = True
    if cache_pages > 0:
        CACHE.memcache = False
    if cache_pages > 1:
        CACHE.enabled = False
    CACHE.Trim()


def GetCacheExpiry():
    return int(ADDON.getSetting("audio_cache_expiry"))


def ClearCache():
    CACHE.Clear()
    xbmcgui.Dialog().ok(translation(30556), translation(30556))


def MainMenuLink():
    """Add main menu link to directory"""
    AddMenuEntry(FormatText("[COLOR ff32cd32]<< %s[/COLOR]", translation(30537)), "", 98, "DefaultFolderBack.png",
                 translation(30537), "")


def NextPageLink(url, mode):
    """Add next page link to directory"""
    DebugLog("NextPageLink: url=%s mode=%s", url, mode)
    AddMenuEntry(FormatText("[COLOR ffffa500]%s[/COLOR]", ">> %s" % translation(30320)), url, mode, "",
                 translation(30320), "")


def CheckAutoplay(name, url, iconimage, description, pid=None, vpid=None, resume_time=None, total_time=None,
                  commands=None):
    """Add directory item to play or show catchup stream for programme"""
    DebugLog("CheckAutoplay: name=%s url=%s iconimage=%s description=%s", name, url, iconimage, description)
    DebugLog("CheckAutoplay: pid=%s vpid=%s resume_time=%s total_time=%s", pid, vpid, resume_time, total_time)
    if ADDON.getSetting('streams_autoplay') == 'true':
        mode = MODE_CATCHUP_ITEM
    else:
        mode = MODE_CATCHUP_DIR
    url = "" if url is None else url
    pid = "" if pid is None else pid
    vpid = "" if vpid is None else vpid
    resume_time = 0 if resume_time is None else resume_time
    total_time = 0 if total_time is None else total_time
    params = "%s|%s|%s|%s|%s|%s" % (name, pid, vpid, resume_time, total_time, url)
    AddMenuEntry(name, params, mode, iconimage, description, "", commands=commands)


def CheckLiveAutoplay(station_id, station_name, station_logo):
    """Add directory item to play or show live stream for station"""
    DebugLog("CheckLiveAutoplay: station_id=%s station_name=%s station_logo=%s", station_id, station_name, station_logo)
    if ADDON.getSetting('streams_autoplay') == 'true':
        mode = MODE_LIVE_ITEM
    else:
        mode = MODE_LIVE_DIR
    AddMenuEntry(station_name, station_id, mode, station_logo, station_name, "")


def CheckGeoblock(url):
    """Check if stream url is geo-blocked"""
    DebugLog("CheckGeoblock: url=%s", url)
    html = OpenURL(url, decode_errors="replace")
    if not html:
        DebugLog("CheckGeoblock: master playlist: no HTML returned: url=%s", url)
    if ADDON.getSetting("audio_log_html") == "true":
        DebugLog("CheckGeoblock: master playlist: html=%s", html)
    denied = re.search('<TITLE>Access Denied</TITLE>', html, re.I)
    if denied:
        DebugLog("CheckGeoblock: master playlist: geo-block detected for url=%s", url)
    if denied or not html:
        return True
    m3u8_match = re.compile(r'BANDWIDTH=.+?,.*?\n(.+?)\n').findall(html)
    for m3u8_url in m3u8_match:
        DebugLog("CheckGeoblock: media playlist: m3u8_url=%s", m3u8_url)
        m3u8_url = HTMLParser.HTMLParser().unescape(m3u8_url)
        m3u8_html = OpenURL(m3u8_url, decode_errors="replace")
        if not m3u8_html:
            DebugLog("CheckGeoblock: media playlist: no HTML returned: m3u8_url=%s", m3u8_url)
        if ADDON.getSetting("audio_log_html") == "true":
            DebugLog("CheckGeoblock: media playlist: m3u8_html=%s", m3u8_html)
        m3u8_denied = re.search('<TITLE>Access Denied</TITLE>', m3u8_html, re.I)
        if m3u8_denied:
            DebugLog("CheckGeoblock: media playlist: geo-block detected for m3u8_url=%s", m3u8_url)
        if m3u8_denied or not m3u8_html:
            return True
    return False


def PlayLiveStream(name, url, iconimage, description):
    """Play live audio stream"""
    DebugLog("PlayLiveStream: name=%s url=%s iconimage=%s description=%s", name, url, iconimage, description)
    iconimage = "DefaultAudio.png" if not iconimage or iconimage == 'None' else iconimage
    lia = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    lia.setInfo("music", {"title": name, "lyrics": description})
    lia.setProperty("IsPlayable", "true")
    lia.setPath(url)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, lia)


def SkipLiveStream(name, url, iconimage, description):
    """Skip live audio stream"""
    DebugLog("SkipLiveStream: name=%s url=%s iconimage=%s description=%s", name, url, iconimage, description)
    # avoids retries
    PlayLiveStream(name, SILENCE_MP3, iconimage, description)
    xbmc.executebuiltin("PlayerControl(stop)")


def GetLiveStreamData(name, station_id, iconimage):
    """Generate live stream data for station"""
    DebugLog("GetLiveStreamData: name=%s station_id=%s iconimage=%s", name, station_id, iconimage)
    stream_data = []
    providers = [('ak', 'Akamai'), ('llnw', 'Limelight')]
    location_qualities = {
        'uk': ['sbr_vlow', 'sbr_low', 'sbr_med', 'sbr_high'],
        'nonuk': ['sbr_vlow', 'sbr_low']
    }
    if station_id == "bbc_world_service":
        location_qualities["uk"] = location_qualities["nonuk"]
    location_settings = ['uk', 'nonuk']
    location_names = {'uk': 'UK', 'nonuk': 'International'}
    quality_colours = {
        'sbr_vlow': 'ffff0000',
        'sbr_low': 'ffffa500',
        'sbr_med': 'ffffff00',
        'sbr_high': 'ff008000'
    }
    quality_bitrates = {
        'sbr_vlow': '48',
        'sbr_low': '96',
        'sbr_med': '128',
        'sbr_high': '320'
    }
    source = int(ADDON.getSetting('radio_source'))
    location_setting = int(ADDON.getSetting('radio_location'))
    location = location_settings[location_setting]
    qualities = location_qualities[location]
    max_quality = int(ADDON.getSetting('radio_live_bitrate')) + 1
    max_quality = min(len(qualities), max_quality)
    qualities = qualities[0:max_quality]
    qualities.reverse()
    if source > 0:
        providers = [providers[source - 1]]
    DebugLog("GetLiveStreamData: location=%s source=%s", location, source)
    for quality in qualities:
        for provider_url, provider_name in providers:
            title = name + FormatText(
                " - [I][COLOR " + quality_colours[quality] + "]%s Kbps %s[/COLOR] [COLOR ffd3d3d3]%s[/COLOR][/I]",
                quality_bitrates[quality], location_names[location], provider_name)
            stream_url = 'https://a.files.bbci.co.uk/media/live/manifesto/audio/simulcast/hls/%s/%s/%s/%s.m3u8' % (
                location, quality, provider_url, station_id)
            DebugLog("GetLiveStreamData: title=%s stream_url=%s", title, stream_url)
            if location_setting == 0:
                if CheckGeoblock(stream_url):
                    DebugLog("GetLiveStreamData: geoblock: title=%s stream_url=%s", title, stream_url)
                    xbmcgui.Dialog().ok(translation(30545), translation(30546))
                    return []
                else:
                    stream_data.append((title, stream_url))
            else:
                stream_data.append((title, stream_url))
    DebugLog("GetLiveStreamData: stream_data=%s", stream_data)
    return stream_data


def AddAvailableLiveStreamItem(name, station_id, iconimage):
    """Play a live stream based on settings for preferred live source and bitrate"""
    DebugLog("AddAvailableLiveStreamItem: name=%s station_id=%s iconimage=%s", name, station_id, iconimage)
    stream_data = GetLiveStreamData(name, station_id, iconimage)
    if not stream_data:
        DebugLog("AddAvailableLiveStreamItem: no stream data found: name=%s station_id=%s", name, station_id)
        xbmcgui.Dialog().ok(translation(30403), translation(30404))
        SkipLiveStream(name, "", iconimage, name)
        return
    stream_title = stream_data[0][0]
    stream_url = stream_data[0][1]
    DebugLog("AddAvailableLiveStreamItem: stream_title=%s stream_url=%s", stream_title, stream_url)
    PlayLiveStream(stream_title, stream_url, iconimage, name)


def AddAvailableLiveStreamsDirectory(name, station_id, iconimage):
    """Adds directory items for the available live streams for a channel"""
    DebugLog("AddAvailableLiveStreamsDirectory: name=%s station_id=%s iconimage=%s", name, station_id, iconimage)
    stream_data = GetLiveStreamData(name, station_id, iconimage)
    if not stream_data:
        DebugLog("AddAvailableLiveStreamsDirectory: no stream data found: name=%s station_id=%s", name, station_id)
        return
    MainMenuLink()
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", name), "", MODE_NOOP, "", name, "")
    for stream_title, stream_url in stream_data:
        DebugLog("AddAvailableLiveStreamsDirectory: stream_title=%s stream_url=%s", stream_title, stream_url)
        AddMenuEntry(stream_title, stream_url, MODE_LIVE_PLAY, iconimage, "", "")


def PlayStream(name, params, iconimage, description):
    """Play catchup audio stream"""
    DebugLog("PlayStream: name=%s params=%s iconimage=%s description=%s", name, params, iconimage, description)
    title, pid, vpid, resume_time, total_time, url = params.split("|", 5)
    DebugLog("PlayStream: title=%s pid=%s vpid=%s resume_time=%s total_time=%s url=%s", title, pid, vpid, resume_time,
             total_time, url)
    iconimage = "DefaultAudio.png" if not iconimage or iconimage == 'None' else iconimage
    lia = xbmcgui.ListItem(name, iconImage=iconimage, thumbnailImage=iconimage)
    lia.setInfo("music", {"title": name, "lyrics": description, "comment": "%s|%s|%s" % (ADDON_ID, params, "audio")})
    lia.setProperty("IsPlayable", "true")
    lia.setPath(url)
    lia.setProperty("ResumeTime", str(resume_time))
    lia.setProperty("TotalTime", str(total_time))
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, lia)


def SkipStream(name, params, iconimage, description):
    """Skip catchup audio stream"""
    DebugLog("SkipLiveStream: name=%s params=%s iconimage=%s description=%s", name, params, iconimage, description)
    # avoids retries
    params = "%s|%s|%s|%s|%s|%s" % (name, "", "", 0, 0, SILENCE_MP3)
    PlayStream(name, params, iconimage, description)
    xbmc.executebuiltin("PlayerControl(stop)")


def GetStreamData(name, url, iconimage, description, vpid):
    """Retrieve catchup stream data for programme"""
    DebugLog("GetStreamData: name=%s url=%s iconimage=%s description=%s", name, url, iconimage, description)
    stream_data = []
    streams = GetAvailableStreams(url, vpid)
    if not streams:
        DebugLog("GetStreamData: no streams found: url=%s", url)
        return []
    for supplier, bitrate, stream_url, encoding, stream_vpid in sorted(streams, key=itemgetter(1), reverse=True):
        bitrate = int(bitrate)
        if supplier == 1:
            supplier = 'Akamai'
        elif supplier == 2:
            supplier = 'Limelight'
        if bitrate >= 255:
            color = 'ff008000'
        elif bitrate >= 120:
            color = 'ffffff00'
        elif bitrate >= 80:
            color = 'ffffa500'
        else:
            color = 'ffff0000'
        title = name + FormatText(" - [I][COLOR " + color + "]%s Kbps %s[/COLOR] [COLOR ffd3d3d3]%s[/COLOR][/I]",
                                  bitrate, encoding, supplier)
        DebugLog("GetStreamData: stream: title=%s stream_url=%s", title, stream_url)
        stream_data.append((title, stream_url, stream_vpid))
    return stream_data


def AddAvailableStreamItem(name, params, iconimage, description):
    """Play a catchup stream based on settings for preferred catchup source and bitrate"""
    DebugLog("AddAvailableStreamItem: name=%s params=%s iconimage=%s description=%s", name, params, iconimage,
             description)
    title, pid, vpid, resume_time, total_time, url = params.split("|", 5)
    DebugLog("AddAvailableStreamItem: title=%s pid=%s vpid=%s resume_time=%s total_time=%s url=%s", title, pid, vpid,
             resume_time, total_time, url)
    stream_data = GetStreamData(name, url, iconimage, description, vpid)
    if not stream_data:
        DebugLog("AddAvailableStreamItem: no stream data found: name=%s url=%s", name, url)
        xbmcgui.Dialog().ok(translation(30403), translation(30404))
        SkipStream(name, params, iconimage, name)
        return
    stream_title = stream_data[0][0]
    stream_url = stream_data[0][1]
    stream_vpid = stream_data[0][2]
    DebugLog("AddAvailableStreamItem: stream_title=%s stream_url=%s stream_vpid=%s", stream_title, stream_url,
             stream_vpid)
    params = "%s|%s|%s|%s|%s|%s" % (stream_title, pid, stream_vpid, resume_time, total_time, stream_url)
    PlayStream(title, params, iconimage, description)


def AddAvailableStreamsDirectory(name, params, iconimage, description):
    """Add directory items for streams corresponding to BBC Sounds page"""
    DebugLog("AddAvailableStreamsDirectory: name=%s params=%s iconimage=%s description=%s", name, params, iconimage,
             description)
    title, pid, vpid, resume_time, total_time, url = params.split("|", 5)
    DebugLog("AddAvailableStreamsDirectory: title=%s pid=%s vpid=%s resume_time=%s total_time=%s url=%s", title, pid,
             vpid, resume_time, total_time, url)
    stream_data = GetStreamData(name, url, iconimage, description, vpid)
    if not stream_data:
        DebugLog("AddAvailableStreamsDirectory: no stream data found: name=%s url=%s", name, url)
        return
    MainMenuLink()
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", name), "", MODE_NOOP, "", name, "")
    for stream_title, stream_url, stream_vpid in stream_data:
        DebugLog("AddAvailableStreamsDirectory: stream_title=%s stream_url=%s stream_vpid=%s", stream_title, stream_url,
                 stream_vpid)
        params = "%s|%s|%s|%s|%s|%s" % (stream_title, pid, stream_vpid, resume_time, total_time, stream_url)
        AddMenuEntry(stream_title, params, MODE_CATCHUP_PLAY, iconimage, description, "")


def GetAvailableStreams(url, vpid):
    """Get available streams corresponding to BBC Sounds page"""
    DebugLog("GetAvailableStreams: url=%s", url)
    if not vpid:
        vpid = ScrapeVpid(url)
    if not vpid:
        DebugLog("GetAvailableStreams: vpid not found: url=%s", url)
        return []
    DebugLog("GetAvailableStreams: vpid found: vpid=%s", vpid)
    streams = ParseStreams(vpid)
    if not streams:
        DebugLog("GetAvailableStreams: no streams found: vpid=%s", vpid)
        return []
    if ADDON.getSetting('streams_autoplay') == "false":
        return streams
    catchup_source = int(ADDON.getSetting('radio_catchup_source'))
    catchup_bitrate = int(ADDON.getSetting('radio_catchup_bitrate'))
    max_bitrate = 9999
    if catchup_bitrate == 2:
        max_bitrate = 255
    elif catchup_bitrate == 1:
        max_bitrate = 119
    elif catchup_bitrate == 0:
        max_bitrate = 79
    DebugLog("GetAvailableStreams: catchup_source=%s max_bitrate=%s", catchup_source, max_bitrate)
    available_streams = []
    for stream in sorted(streams, key=itemgetter(1), reverse=True):
        bitrate = int(stream[1])
        if bitrate > max_bitrate:
            DebugLog("GetAvailableStreams: bitrate > max_bitrate: bitrate=%s max_bitrate=%s", bitrate, max_bitrate)
            continue
        supplier = int(stream[0])
        if catchup_source > 0 and supplier != catchup_source:
            DebugLog("GetAvailableStreams: supplier != catchup_source: supplier=%s catchup_source=%s", supplier,
                     catchup_source)
            continue
        available_streams.append(stream)
    return available_streams


def OpenMediaSelectorUrl(ms_url):
    """Retrieve mediaselector stream data"""
    DebugLog("OpenMediaSelectorUrl: ms_url=%s", ms_url)
    if not ms_url:
        return None
    request_headers = {"Accept": "application/json"}
    json_str = OpenURL(ms_url, decode_errors="replace", request_headers=request_headers)
    if not json_str:
        DebugLog("OpenMediaSelectorUrl: no JSON string returned: ms_url=%s", ms_url)
        return None
    if ADDON.getSetting("audio_log_html") == "true":
        DebugLog("OpenMediaSelectorUrl: json_data=%s", json_str)
    json_data = json.loads(json_str)
    if not json_data:
        DebugLog("OpenMediaSelectorUrl: no JSON data loaded: rms_url=%s", ms_url)
        return None
    if ADDON.getSetting("audio_log_json") == "true":
        DebugLog("OpenMediaSelectorUrl: json_data=%s", json.dumps(json_data))
    return json_data


def ParseStreams(vpid):
    """Parse streams from mediaselector stream data"""
    DebugLog("ParseStreams: vpid=%s", vpid)
    if not vpid:
        return []
    streams = []
    for api_version in [6, 5]:
        ms_url = "https://open.live.bbc.co.uk/mediaselector/%s/select/version/2.0/mediaset/iptv-all/vpid/%s/proto/http/format/json?cb=%d" % (
            api_version, vpid, random.randrange(10000, 99999))
        json_data = OpenMediaSelectorUrl(ms_url)
        if not json_data:
            DebugLog("ParseStreams: no JSON data returned: ms_url=%s", ms_url)
            continue
        medias = json_data.get("media", [])
        if not medias:
            DebugLog("ParseStreams: no medias found: vpid=%s api_version=%s", vpid, api_version)
            continue
        for media in medias:
            media_bitrate = int(media.get("bitrate", "0"))
            encoding = media.get("encoding", "aac")
            DebugLog("ParseStreams: media: bitrate=%s encoding=%s", media_bitrate, encoding)
            connections = media.get("connection", [])
            if not connections:
                DebugLog("ParseStreams: no connections found: media bitrate=%s encoding=%s", media_bitrate, encoding)
                continue
            for connection in connections:
                transfer_format = connection.get("transferFormat", "")
                if transfer_format != "hls":
                    continue
                conn_url = connection.get("href", "")
                DebugLog("ParseStreams: connection: conn_url=%s", conn_url)
                supplier = connection.get("supplier", "")
                if not conn_url or not supplier:
                    DebugLog("ParseStreams: invalid connection: conn_url=%s supplier=%s", conn_url, supplier)
                    continue
                m3u8_url = re.sub(r'([^/]+)\.ism(?:\.hlsv2\.ism)?/[^/]+\.m3u8', r'\1.ism/\1.m3u8', conn_url)
                DebugLog("ParseStreams: connection: master playlist=%s", m3u8_url)
                conn_supplier = 0
                if 'akamai' in supplier:
                    conn_supplier = 1
                elif 'limelight' in supplier:
                    conn_supplier = 2
                m3u8_html = OpenURL(m3u8_url, decode_errors="replace")
                if not m3u8_html:
                    DebugLog("ParseStreams: no HTML returned: m3u8_url=%s", m3u8_url)
                    continue
                if ADDON.getSetting("audio_log_html") == "true":
                    DebugLog("ParseStreams: connection: variant playlist=%s", m3u8_html)
                m3u8_match = re.compile(r'BANDWIDTH=(.+?),.*?\n(.+?)\n').findall(m3u8_html)
                if m3u8_match:
                    for bandwidth, stream_url in m3u8_match:
                        DebugLog("ParseStreams: connection: stream: bandwidth=%s stream_url=%s", bandwidth, stream_url)
                        stream_url = HTMLParser.HTMLParser().unescape(stream_url)
                        if not stream_url.startswith("http"):
                            stream_url = re.sub(r'[^/]+?\.m3u8', stream_url, m3u8_url)
                        audio_match = re.search(r'audio.*?=(\d+)', stream_url)
                        if audio_match:
                            conn_bitrate = int(audio_match.group(1)) / 1000
                        else:
                            conn_bitrate = int(bandwidth) / 1000
                        streams.append((conn_supplier, conn_bitrate, stream_url, encoding, vpid))
                else:
                    streams.append((conn_supplier, media_bitrate, m3u8_url, encoding, vpid))
        if streams:
            break
    DebugLog("ParseStreams: streams=%s", streams)
    return streams


def ScrapeVpid(page_url):
    """Scrape programme vpid from BBC Sounds page"""
    DebugLog("ScrapeVpid: page_url=%s", page_url)
    json_data = LoadPageState(page_url)
    if not json_data:
        DebugLog("ScrapeVpid: no JSON data returned: page_url=%s", page_url)
        return None
    if ADDON.getSetting("audio_log_json") == "true":
        DebugLog("ScrapeVpid: json_data=%s", json.dumps(json_data))
    vpid = json_data.get("programmes", {}).get("current", {}).get("id", "")
    DebugLog("ScrapeVpid: vpid=%s", vpid)
    return vpid


def LoadPageState(page_url):
    """Load JSON state from BBC Sounds page"""
    DebugLog("LoadPageState: page_url=%s", page_url)
    if not page_url:
        return None
    html = OpenURL(page_url, decode_errors="replace")
    if not html:
        DebugLog("LoadPageState: no HTML returned: page_url=%s", page_url)
        return None
    if ADDON.getSetting("audio_log_html") == "true":
        DebugLog("LoadPageState: html=%s", html)
    match = re.search(r'window.__PRELOADED_STATE__ = (.*?);\s*</script>', html, re.DOTALL)
    if not match:
        DebugLog("LoadPageState: page state not found")
        return None
    json_data = json.loads(match.group(1))
    if ADDON.getSetting("audio_log_json") == "true":
        DebugLog("LoadPageState: json_data=%s", json.dumps(json_data))
    return json_data


def ListLive():
    """Create a list of playable stations and add to directory"""
    channel_list = [
        ('bbc_radio_one', 'BBC Radio 1'),
        ('bbc_1xtra', 'BBC Radio 1Xtra'),
        ('bbc_radio_two', 'BBC Radio 2'),
        ('bbc_radio_three', 'BBC Radio 3'),
        ('bbc_radio_fourfm', 'BBC Radio 4 FM'),
        ('bbc_radio_fourlw', 'BBC Radio 4 LW'),
        ('bbc_radio_four_extra', 'BBC Radio 4 Extra'),
        ('bbc_radio_five_live', 'BBC Radio 5 live'),
        ('bbc_radio_five_live_sports_extra', 'BBC Radio 5 live sports extra'),
        ('bbc_6music', 'BBC Radio 6 Music'),
        ('bbc_asian_network', 'BBC Asian Network'),
        ('bbc_world_service', 'BBC World Service'),
        ('bbc_radio_scotland_fm', 'BBC Radio Scotland'),
        ('bbc_radio_nan_gaidheal', u'BBC Radio nan Gàidheal'),
        ('bbc_radio_ulster', 'BBC Radio Ulster'),
        ('bbc_radio_foyle', 'BBC Radio Foyle'),
        ('bbc_radio_wales_fm', 'BBC Radio Wales'),
        ('bbc_radio_cymru', 'BBC Radio Cymru'),
        ('bbc_radio_cymru_2', 'BBC Radio Cymru 2'),
        ('cbeebies_radio', 'CBeebies Radio'),
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
    page_title = translation(30522)
    MainMenuLink()
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", page_title), "", MODE_NOOP, "", page_title, "")
    for channel_id, name in channel_list:
        logo = xbmc.translatePath(
            os.path.join('special://home/addons/plugin.video.iplayerwww/media', channel_id + '.png'))
        CheckLiveAutoplay(channel_id, name, logo)


def ListAtoZ():
    """Create navigation to programmes based on alphabetical order"""
    DebugLog("ListAtoZ:")
    characters = [
        ('A', 'a'), ('B', 'b'), ('C', 'c'), ('D', 'd'), ('E', 'e'), ('F', 'f'),
        ('G', 'g'), ('H', 'h'), ('I', 'i'), ('J', 'j'), ('K', 'k'), ('L', 'l'),
        ('M', 'm'), ('N', 'n'), ('O', 'o'), ('P', 'p'), ('Q', 'q'), ('R', 'r'),
        ('S', 's'), ('T', 't'), ('U', 'u'), ('V', 'v'), ('W', 'w'), ('X', 'x'),
        ('Y', 'y'), ('Z', 'z'), ('0-9', '@')]
    page_title = translation(30523)
    MainMenuLink()
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", page_title), "", MODE_NOOP, "", page_title, "")
    for name, letter in characters:
        params = "%s|%s" % (letter, name)
        AddMenuEntry(name, params, MODE_AZ_PAGE, '', name, '')


def GetAtoZPage(params):
    """Scrape https://www.bbc.co.uk/programmes/a-z/by/<letter>/player?page=<page_num>"""
    DebugLog("GetAtoZPage: params=%s", params)
    if not params:
        return
    letter, name = params.split("|", 1)
    if not letter and not name:
        return
    page_url = 'https://www.bbc.co.uk/programmes/a-z/by/%s/player?page=1' % letter
    page_title = "%s - %s" % (translation(30523), name)
    params = "%s|%s" % (page_url, page_title)
    GetProgrammesPage(params)


def ListCategories():
    """List top-level programme genres/formats"""
    DebugLog("ListCategories:")
    headings = {"genres": translation(30557), "formats": translation(30558)}
    MainMenuLink()
    page_title = translation(30532)
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", page_title), "", MODE_NOOP, "", page_title, "")
    for categories_type in ["genres", "formats"]:
        heading = headings[categories_type]
        AddMenuEntry(FormatText("[I]%s[/I]", heading), "", MODE_NOOP, "", heading, "")
        categories = RADIO_CATEGORIES[categories_type]
        for name, path, _ in categories:
            if path and name:
                params = "%s|%s" % (path, name)
                AddMenuEntry(name, params, MODE_LIST_SUBCATS, "", name, "")


def ListSubcategories(params):
    """List programme sub-genres/sub-formats"""
    DebugLog("ListSubcategories: params=%s", params)
    if not params:
        return
    category_path, category_name = params.split("|", 1)
    if not category_path or not category_name:
        return
    if ADDON.getSetting("audio_show_subcat") == "false":
        GetCategoryPage(params)
        return
    category = None
    for categories_type in ["genres", "formats"]:
        categories = RADIO_CATEGORIES[categories_type]
        for item in categories:
            if item[1] == category_path:
                category = item
                break
    if not category:
        return
    subcategories = category[2]
    if not subcategories:
        GetCategoryPage(params)
        return
    MainMenuLink()
    page_title = "%s - %s" % (translation(30532), category_name)
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", page_title), "", MODE_NOOP, "", page_title, "")
    params = "%s|%s %s" % (category_path, translation(30535), category_name)
    AddMenuEntry("* %s %s" % (translation(30535), category_name), params, MODE_CATEGORY_PAGE, "", category_name, "")
    for name, path in subcategories:
        if path and name:
            path = re.sub(r'/player$', "", path)
            params = "%s|%s - %s" % (path, category_name, name)
            AddMenuEntry(name, params, MODE_CATEGORY_PAGE, "", name, "")


def GetCategoryPage(params):
    """Scrape
        https://www.bbc.co.uk/programmes/genres/<genre>/player?page=<page_num>
    or
        https://www.bbc.co.uk/programmes/formats/<format>/player?page=<page_num>
    """
    DebugLog("GetCategoryPage: params=%s", params)
    if not params:
        return
    category_path, category_name = params.split("|", 1)
    if not category_path or not category_name:
        return
    page_url = 'https://www.bbc.co.uk%s/player?page=1' % category_path
    page_title = "%s - %s" % (translation(30532), category_name)
    params = "%s|%s" % (page_url, page_title)
    GetProgrammesPage(params)


def GetProgrammesPage(params):
    """Scrape contents of a /programmes page"""
    DebugLog("GetProgrammesPage: params=%s", params)
    if not params:
        return
    page_url, page_title = params.split("|", 1)
    if not page_url or not page_title:
        return
    cache_key = page_url
    cache_data = CACHE.Get(cache_key)
    if not cache_data or not cache_data.get("programmes") or not cache_data.get("paging"):
        DebugLog("GetProgrammesPage: NOT loaded from cache: %s", page_url)
        cache_data = {"programmes": [], "paging": ()}
        html = OpenURL(page_url, decode_errors='replace')
        if not html:
            DebugLog("GetProgrammesPage: no HTML returned: page_url=%s", page_url)
            return
        if ADDON.getSetting("audio_log_html") == "true":
            DebugLog("GetProgrammesPage: html=%s", html)
        soup = BeautifulSoup(html, "html.parser")
        cache_data["paging"] = InitPaging(soup, page_url)
        programmes = soup.select("div.programmes-page div.programme--radio")
        for programme in programmes:
            series_id = ""
            series_id_match = programme.select("div.programme__child-availability > a[href]")
            if series_id_match:
                series_id = series_id_match[0].attrs.get("href", "")
            programme_id = programme.attrs.get("data-pid", "")
            if not series_id and not programme_id:
                continue
            name = ""
            name_match = programme.select("span.programme__title > span")
            if name_match:
                name = name_match[0].get_text().strip()
            if not name:
                continue
            image = GetImageUrl(programme, "img.image")
            synopsis = ""
            synopsis_match = programme.select("p.programme__synopsis > span")
            if synopsis_match:
                synopsis = synopsis_match[0].get_text().strip()
            station = translation(30530)
            station_match = programme.select("p.programme__service")
            if station_match:
                station = station_match[0].get_text().strip()
            cache_data["programmes"].append((series_id, programme_id, name, image, synopsis, station))
        CACHE.Set(cache_key, cache_data, ttl=GetCacheExpiry())
    else:
        DebugLog("GetProgrammesPage: WAS loaded from cache: %s", page_url)
    curr_page, next_page, total_pages = cache_data["paging"]
    paging = translation(30547) % (curr_page, total_pages)
    MainMenuLink()
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", "%s  %s" % (page_title, paging)), "", MODE_NOOP, "", page_title, "")
    for series_id, programme_id, name, image, synopsis, station in cache_data["programmes"]:
        if series_id and name:
            title = "%s - %s" % (name, station)
            url = "https://www.bbc.co.uk%s?page=1" % series_id
            series_params = "%s|%s - %s" % (url, name, station)
            DebugLog("GetProgrammesPage: series: title=%s url=%s image=%s synopsis=%s", title, url, image, synopsis)
            AddMenuEntry(FormatText("[B]%s[/B]", title), series_params, MODE_EPISODES, image, synopsis, "")
        elif programme_id and name:
            title = "%s - %s" % (name, station)
            url = "https://www.bbc.co.uk/sounds/play/%s" % programme_id
            CheckAutoplay(title, url, image, synopsis, pid=programme_id)
    if total_pages > 1:
        GoToProgrammesPageLink(params, MODE_PROGRAMMES_PAGE, total_pages)
    if next_page > curr_page:
        next_page_url = re.sub(r'\?page=\d+', "?page=" + str(next_page), page_url)
        next_page_data = "%s|%s" % (next_page_url, page_title)
        NextPageLink(next_page_data, MODE_PROGRAMMES_PAGE)


def InitPaging(soup, page_url):
    """Initialise paging parameters for programmes page"""
    DebugLog("InitPaging: page_url=%s", page_url)
    curr_page = 1
    next_page = 1
    total_pages = 1
    sel_pgn_block = "ol.pagination"
    sel_next_link = "li.pagination__next"
    sel_page_link = "li.pagination__page"
    pagination = soup.select(sel_pgn_block)
    if pagination:
        if page_url:
            curr_page_match = re.search(r'page=(\d+)', page_url)
            if curr_page_match:
                curr_page = int(curr_page_match.group(1))
                next_page = curr_page
        next_url_match = pagination[0].select(sel_next_link)
        if next_url_match:
            next_link_match = next_url_match[-1].select("a")
            if next_link_match:
                next_page_match = re.search(r'.*?page=(\d+)', next_link_match[0].attrs.get("href", ""))
                if next_page_match:
                    next_page = int(next_page_match.group(1))
        pages = pagination[0].select(sel_page_link)
        if pages:
            last_link_match = pages[-1].select("a")
            if last_link_match:
                last_page_match = re.search(r'.*?page=(\d+)', last_link_match[0].attrs.get("href", ""))
                total_pages = int(last_page_match.group(1))
            else:
                last_page_match = pages[-1].select("span")
                if last_page_match:
                    total_pages = int(last_page_match[0].get_text().strip())
    DebugLog("InitPaging: curr_page=%s next_page=%s total_pages=%s", curr_page, next_page, total_pages)
    return curr_page, next_page, total_pages


def GetEpisodes(params):
    """Scrape episodes: https://www.bbc.co.uk/programmes/<programme_id>/episodes/player?page=<page_num>"""
    DebugLog("GetEpisodes: params=%s", params)
    if not params:
        return
    page_url, page_title = params.split("|", 1)
    if not page_url or not page_title:
        return
    max_episodes = 100
    cache_key = page_url
    cache_data = CACHE.Get(cache_key)
    paginate = ADDON.getSetting("radio_episodes_paginate")
    order = int(ADDON.getSetting("radio_episodes_order"))
    if not cache_data or not cache_data.get("programmes") or not cache_data.get("paging") \
       or not cache_data.get("paginate") or cache_data.get("paginate") != paginate \
       or not cache_data.get("order"):
        DebugLog("GetEpisodes: NOT loaded from cache: %s", page_url)
        cache_data = {"programmes": [], "paging": (), "paginate": paginate, "order": order}
        html = OpenURL(page_url, decode_errors='replace')
        if not html:
            DebugLog("GetEpisodes: no HTML returned: page_url=%s", page_url)
            return
        if ADDON.getSetting("audio_log_html") == "true":
            DebugLog("GetEpisodes: html=%s", html)
        soup = BeautifulSoup(html, "html.parser")
        cache_data["paging"] = InitPaging(soup, page_url)
        page = 1
        start_page = 1
        curr_page, next_page, total_pages = cache_data["paging"]
        page = start_page = curr_page
        DebugLog("GetEpisodes: paging: curr_page=%s next_page=%s total_pages=%s", curr_page, next_page, total_pages)
        while page <= total_pages:
            if page > start_page:
                next_page_url = re.sub(r'\?page=\d+', "?page=" + str(page), page_url)
                DebugLog("GetEpisodes: page=%s next_page_url=%s", page, next_page_url)
                html = OpenURL(next_page_url, decode_errors="replace")
                if not html:
                    DebugLog("GetEpisodes: no HTML returned: next_page_url=%s", next_page_url)
                    break
                if ADDON.getSetting("audio_log_html") == "true":
                    DebugLog("GetEpisodes: html=%s", html)
                soup = BeautifulSoup(html, "html.parser")
            series_name = translation(30530)
            masthead_title_match = soup.select("div.br-masthead__title > a")
            if masthead_title_match and masthead_title_match[0].string:
                series_name = masthead_title_match[0].get_text().strip()
            else:
                masthead_pagetitle_match = soup.select("span.br-masthead__pagetitle")
                if masthead_pagetitle_match:
                    series_name = masthead_pagetitle_match[0].get_text().strip()
            station = translation(30530)
            masthead_masterbrand_match = soup.select("a.br-masthead__masterbrand")
            if masthead_masterbrand_match:
                station = masthead_masterbrand_match[0].get_text().strip()
            programmes = soup.select("div.programmes-page div.programme--radio")
            if not programmes:
                break
            for programme in programmes:
                programme_id = programme.attrs.get("data-pid", "")
                if not programme_id:
                    continue
                name = ""
                name_match = programme.select("span.programme__title > span")
                if name_match:
                    name = name_match[0].get_text().strip()
                if not name:
                    continue
                subtitle = ""
                subtitle_match = programme.select("span.programme__subtitle > span")
                if subtitle_match:
                    subtitle = subtitle_match[0].get_text().strip()
                image = GetImageUrl(programme, "img.image")
                synopsis = ""
                synopsis_match = programme.select("p.programme__synopsis > span")
                if synopsis_match:
                    synopsis = synopsis_match[0].get_text().strip()
                if subtitle:
                    title = "%s: %s - %s - %s" % (series_name, subtitle, name, station)
                else:
                    title = "%s - %s - %s" % (series_name, name, station)
                cache_data["programmes"].append((programme_id, title, image, synopsis))
                if len(cache_data["programmes"]) >= 100:
                    break
            if paginate == "true" or len(cache_data["programmes"]) >= max_episodes:
                break
            page += 1
        if cache_data["paginate"] == "false" and cache_data["order"] == 1:
           cache_data["programmes"].reverse()
        CACHE.Set(cache_key, cache_data, ttl=GetCacheExpiry())
    else:
        DebugLog("GetEpisodes: WAS loaded from cache: %s", page_url)
        if cache_data["paginate"] == "false" and cache_data["order"] != order:
           cache_data["programmes"].reverse()
    curr_page, next_page, total_pages = cache_data["paging"]
    if paginate == "true":
        paging = translation(30547) % (curr_page, total_pages)
    else:
        paging = translation(30568) % max_episodes
    MainMenuLink()
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", "%s  %s" % (page_title, paging)), "", MODE_NOOP, "", page_title, "")
    for programme_id, title, image, synopsis in cache_data["programmes"]:
        url = "https://www.bbc.co.uk/sounds/play/%s" % programme_id
        CheckAutoplay(title, url, image, synopsis, pid=programme_id)
    if paginate == "true":
        if total_pages > 1:
            GoToProgrammesPageLink(params, MODE_EPISODES, total_pages)
        if next_page > curr_page:
            next_page_url = re.sub(r'\?page=\d+', "?page=" + str(next_page), page_url)
            next_page_data = "%s|%s" % (next_page_url, page_title)
            NextPageLink(next_page_data, MODE_EPISODES)


def DoSearch(search_entered=None):
    """Prompt for search input and send to programmes search"""
    DebugLog("DoSearch: old: search_entered=%s", search_entered)
    if ADDON.getSetting("audio_keep_search") == "true":
        keep_search = True
    else:
        keep_search = False
    if not search_entered and keep_search:
        search_entered = xbmcgui.Window(10000).getProperty(PROP_SEARCH_ENTERED)
    keyboard = xbmc.Keyboard(search_entered, translation(30525))
    keyboard.doModal()
    if keyboard.isConfirmed():
        search_entered = keyboard.getText()
    DebugLog("DoSearch: new: search_entered=%s", search_entered)
    if not search_entered or not keyboard.isConfirmed():
        CreateBaseDirectory("audio")
        return
    if keep_search:
        xbmcgui.Window(10000).setProperty(PROP_SEARCH_ENTERED, search_entered)
    else:
        xbmcgui.Window(10000).clearProperty(PROP_SEARCH_ENTERED)
    url = "https://www.bbc.co.uk/search?filter=programmes&q=%s&page=1" % search_entered
    GetSearchPage(url)


def GetSearchPage(page_url):
    """Scrape search results: https://www.bbc.co.uk/search?filter=programmes&q=<search_entered>&page=<page_num>"""
    DebugLog("GetSearchPage: page_url=%s", page_url)
    if not page_url:
        return
    search_entered = ""
    start_page = 1
    match = re.search(r'&q=(.+?)&page=(\d+)', page_url)
    if match:
        search_entered = match.group(1)
        start_page = int(match.group(2))
    min_items = int(ADDON.getSetting("radio_page_size"))
    cache_key = page_url
    cache_data = CACHE.Get(cache_key)
    if not cache_data or not cache_data.get("programmes") or not cache_data.get("paging"):
        DebugLog("GetSearchPage: NOT loaded from cache: %s", page_url)
        cache_data = {"programmes": [], "paging": ()}
        item_num = 0
        max_empty = 10
        empty_pages = 0
        page = start_page
        utc_date = datetime.datetime.utcnow().date()
        progress_dialog = xbmcgui.DialogProgressBG()
        progress_dialog.create(translation(30319))
        html = OpenURL(page_url, decode_errors="ignore")
        if not html:
            DebugLog("GetSearchPage: no HTML returned: page_url=%s", page_url)
            progress_dialog.close()
            return
        if ADDON.getSetting("audio_log_html") == "true":
            DebugLog("GetSearchPage: html=%s", html)
        soup = BeautifulSoup(html, "html.parser")
        while True:
            if page > start_page:
                next_page_url = re.sub(r'&page=\d+', "&page=" + str(page + 1), page_url)
                DebugLog("GetSearchPage: page=%s next_page_url=%s", page, next_page_url)
                html = OpenURL(next_page_url, decode_errors="replace")
                if not html:
                    DebugLog("GetSearchPage: no HTML returned: next_page_url=%s", next_page_url)
                    page += 1
                    empty_pages += 1
                    if empty_pages > max_empty:
                        break
                    continue
                if ADDON.getSetting("audio_log_html") == "true":
                    DebugLog("GetSearchPage: html=%s", html)
                soup = BeautifulSoup(html, "html.parser")
            programmes = soup.select("ol.search-results > li > article.media-audio")
            if not programmes:
                DebugLog("GetSearchPage: no programmes: page=%s item_num=%s", page, item_num)
                page += 1
                empty_pages += 1
                if empty_pages > max_empty:
                    break
                continue
            for programme in programmes:
                pub_date = utc_date
                pub_date_match = programme.select("time.display-date")
                if not pub_date_match:
                    continue
                pub_date_str = pub_date_match[0].attrs.get("datetime", "")[0:10]
                if pub_date_str:
                    try:
                        pub_date = datetime.datetime(*(time.strptime(pub_date_str, '%Y-%m-%d')[0:6])).date()
                    except Exception as ex:
                        DebugLog("GetSearchPage: publish date parse failed: pub_date_str=%s error=%s", pub_date_str, ex)
                if pub_date > utc_date:
                    continue
                programme_id = ""
                programme_url_match = programme.select("a")
                if programme_url_match:
                    programme_url = programme_url_match[0].attrs.get("href", "")
                    programme_id_match = re.search(r'/programmes/([0-9a-z]+)$', programme_url)
                    if programme_id_match:
                        programme_id = programme_id_match.group(1)
                name = ""
                name_match = programme.select("h1[itemprop=headline] > a")
                if name_match:
                    name = name_match[0].get_text().strip()
                if not programme_id and not name:
                    continue
                image = GetImageUrl(programme, "img.imagepid")
                synopsis = ""
                synopsis_match = programme.select("p.summary.medium")
                if synopsis_match:
                    synopsis = synopsis_match[0].get_text().strip()
                if not synopsis:
                    synopsis_match = programme.select("p.summary.short")
                    if synopsis_match:
                        synopsis = synopsis_match[0].get_text().strip()
                station = translation(30530)
                station_match = programme.select("span.signpost-section")
                if station_match:
                    station = station_match[0].get_text().strip()
                title = "%s - %s" % (name, station)
                cache_data["programmes"].append((programme_id, title, image, synopsis))
                item_num += 1
                empty_pages = 0
                percent = min(100, int(100 * (item_num / (min_items * 1.0))))
                progress_dialog.update(percent, translation(30319), name)
            if item_num >= min_items:
                break
            page += 1
        progress_dialog.update(100, translation(30319))
        progress_dialog.close()
        cache_data["paging"] = (0, page + 1, 0)
        CACHE.Set(cache_key, cache_data, ttl=GetCacheExpiry())
    else:
        DebugLog("GetSearchPage: WAS loaded from cache: %s", page_url)
    _, next_page, _ = cache_data["paging"]
    MainMenuLink()
    AddMenuEntry(FormatText("[COLOR ffffff00][I]%s[/I][/COLOR]", "< %s" % translation(30542)), "url", MODE_SEARCH, "",
                 translation(30542), "")
    page_title = translation(30525)
    AddMenuEntry(FormatText("[B][I]%s[/I][/B]", "%s - '%s'" % (page_title, search_entered)), "", MODE_NOOP, "",
                 page_title, "")
    for programme_id, title, image, synopsis in cache_data["programmes"]:
        url = "https://www.bbc.co.uk/sounds/play/%s" % programme_id
        CheckAutoplay(title, url, image, synopsis, pid=programme_id)
    if len(cache_data["programmes"]) >= min_items:
        next_page_url = re.sub(r'\&page=\d+', "&page=" + str(next_page), page_url)
        NextPageLink(next_page_url, MODE_SEARCH_PAGE)


def GetImageUrl(programme, img):
    """Scrape thumbnail from multiple locations"""
    DebugLog("GetImageUrl:")
    if ADDON.getSetting("audio_log_html") == "true":
        DebugLog("GetImageUrl: programme=%s img=%s", programme, img)
    image_url = ""
    image_match = programme.select(img)
    if image_match:
        srcset = image_match[0].attrs.get("srcset", "")
        if not srcset:
            srcset = image_match[0].attrs.get("data-srcset", "")
        if srcset:
            srcset_match = re.search(r'(https?[^\s]+(384|480)x[^\s]+)', srcset)
            if srcset_match:
                image_url = srcset_match.group(1)
        if not image_url:
            image_url = image_match[0].attrs.get("src", "")
            if not image_url:
                image_url = image_match[0].attrs.get("data-src", "")
    return image_url


def GoToProgrammesPage(logged_in, params):
    """Navigate directly page in multi-page list"""
    DebugLog("GoToProgrammesPage: logged_in=%s params=%s", logged_in, params)
    if not params:
        return
    total_pages, page_mode, page_url, page_title = params.split("|", 3)
    DebugLog("GoToProgrammesPage: total_pages=%s page_mode=%s page_url=%s page_title=%s", total_pages, page_mode, page_url,
             page_title)
    if not page_mode or not page_url or not page_title:
        return
    page_mode = int(page_mode)
    next_page_data = "%s|%s" % (page_url, page_title)
    keyboard = xbmc.Keyboard("", translation(30549))
    keyboard.doModal()
    if keyboard.isConfirmed():
        next_page_num = 0
        next_page_str = keyboard.getText()
        if next_page_str:
            try:
                next_page_num = int(next_page_str)
                DebugLog("GoToProgrammesPage: valid page number: next_page_num=%s next_page_str=%s", next_page_num,
                         next_page_str)
            except Exception as err:
                DebugLog("GoToProgrammesPage: invalid page number: next_page_str=%s err=%s", next_page_str, err)
            if next_page_num > 0:
                total_pages = int(total_pages)
                if next_page_num > total_pages:
                    next_page_num = total_pages
                DebugLog("GoToProgrammesPage: next_page_num=%s total_pages=%s", next_page_num, total_pages)
                next_page_url = re.sub(r'\?page=\d+', "?page=" + str(next_page_num), page_url)
                next_page_data = "%s|%s" % (next_page_url, page_title)
    if page_mode == MODE_EPISODES:
        GetEpisodes(next_page_data)
    else:
        GetProgrammesPage(next_page_data)


def GoToProgrammesPageLink(params, mode, total_pages):
    """Add goto page link to directory"""
    DebugLog("GoToProgrammesPageLink: params=%s mode=%s total_pages=%s", params, mode, total_pages)
    goto_params = "%s|%s|%s" % (total_pages, mode, params)
    AddMenuEntry(FormatText("[COLOR ff00bfff]%s[/COLOR]", "> %s" % translation(30548)), goto_params, 215, "DefaultFolder.png",
                 translation(30548), "")


RADIO_GENRES = [
    (u"Children's", '/programmes/genres/childrens',
     [('Activities', '/programmes/genres/childrens/activities'),
      ('Drama', '/programmes/genres/childrens/drama'),
      ('Entertainment & Comedy', '/programmes/genres/childrens/entertainmentandcomedy'),
      ('Factual', '/programmes/genres/childrens/factual'),
      ('Music', '/programmes/genres/childrens/music'),
      ('News', '/programmes/genres/childrens/news'),
      ('Sport', '/programmes/genres/childrens/sport')]),
    ('Comedy', '/programmes/genres/comedy',
     [('Character', '/programmes/genres/comedy/character'),
      ('Chat', '/programmes/genres/comedy/chat'),
      ('Impressionists', '/programmes/genres/comedy/impressionists'),
      ('Music', '/programmes/genres/comedy/music'),
      ('Panel Shows', '/programmes/genres/comedy/panelshows'),
      ('Satire', '/programmes/genres/comedy/satire'),
      ('Sitcoms', '/programmes/genres/comedy/sitcoms'),
      ('Sketch', '/programmes/genres/comedy/sketch'),
      ('Spoof', '/programmes/genres/comedy/spoof'),
      ('Standup', '/programmes/genres/comedy/standup'),
      ('Stunt', '/programmes/genres/comedy/stunt')]),
    ('Drama', '/programmes/genres/drama',
     [('Action & Adventure', '/programmes/genres/drama/actionandadventure'),
      ('Biographical', '/programmes/genres/drama/biographical'),
      ('Classic & Period', '/programmes/genres/drama/classicandperiod'),
      ('Crime', '/programmes/genres/drama/crime'),
      ('Historical', '/programmes/genres/drama/historical'),
      ('Horror & Supernatural', '/programmes/genres/drama/horrorandsupernatural'),
      ('Legal & Courtroom', '/programmes/genres/drama/legalandcourtroom'),
      ('Medical', '/programmes/genres/drama/medical'),
      ('Musical', '/programmes/genres/drama/musical'),
      ('Political', '/programmes/genres/drama/political'),
      ('Psychological', '/programmes/genres/drama/psychological'),
      ('Relationships & Romance', '/programmes/genres/drama/relationshipsandromance'),
      ('SciFi & Fantasy', '/programmes/genres/drama/scifiandfantasy'),
      ('Soaps', '/programmes/genres/drama/soaps'),
      ('Spiritual', '/programmes/genres/drama/spiritual'),
      ('Thriller', '/programmes/genres/drama/thriller'),
      ('War & Disaster', '/programmes/genres/drama/waranddisaster'),
      ('Western', '/programmes/genres/drama/western')]),
    ('Entertainment', '/programmes/genres/entertainment',
     [('Variety Shows', '/programmes/genres/entertainment/varietyshows')]),
    ('Factual', '/programmes/genres/factual',
     [('Antiques', '/programmes/genres/factual/antiques'),
      ('Arts, Culture & the Media', '/programmes/genres/factual/artscultureandthemedia'),
      ('Beauty & Style', '/programmes/genres/factual/beautyandstyle'),
      ('Cars & Motors', '/programmes/genres/factual/carsandmotors'),
      ('Consumer', '/programmes/genres/factual/consumer'),
      ('Crime & Justice', '/programmes/genres/factual/crimeandjustice'),
      ('Disability', '/programmes/genres/factual/disability'),
      ('Families & Relationships', '/programmes/genres/factual/familiesandrelationships'),
      ('Food & Drink', '/programmes/genres/factual/foodanddrink'),
      ('Health & Wellbeing', '/programmes/genres/factual/healthandwellbeing'),
      ('History', '/programmes/genres/factual/history'),
      ('Homes & Gardens', '/programmes/genres/factual/homesandgardens'),
      ('Life Stories', '/programmes/genres/factual/lifestories'),
      ('Money', '/programmes/genres/factual/money'),
      ('Pets & Animals', '/programmes/genres/factual/petsandanimals'),
      ('Politics', '/programmes/genres/factual/politics'),
      ('Science & Nature', '/programmes/genres/factual/scienceandnature'),
      ('Travel', '/programmes/genres/factual/travel')]),
    ('Learning', '/programmes/genres/learning',
     [('Adults', '/programmes/genres/learning/adults'),
      ('Languages', '/programmes/genres/learning/languages'),
      ('Pre-School', '/programmes/genres/learning/preschool'),
      ('Primary', '/programmes/genres/learning/primary'),
      ('Secondary', '/programmes/genres/learning/secondary')]),
    ('Music', '/programmes/genres/music',
     [('Classical', '/programmes/genres/music/classical'),
      ('Classic Pop & Rock', '/programmes/genres/music/classicpopandrock'),
      ('Country', '/programmes/genres/music/country'),
      ('Dance & Electronica', '/programmes/genres/music/danceandelectronica'),
      ('Desi', '/programmes/genres/music/desi'),
      ('Easy Listening, Soundtracks & Musicals',
       '/programmes/genres/music/easylisteningsoundtracksandmusicals'),
      ('Folk', '/programmes/genres/music/folk'),
      ('Hip Hop, RnB & Dancehall',
       '/programmes/genres/music/hiphoprnbanddancehall'),
      ('Jazz & Blues', '/programmes/genres/music/jazzandblues'),
      ('Pop & Chart', '/programmes/genres/music/popandchart'),
      ('Rock & Indie', '/programmes/genres/music/rockandindie'),
      ('Soul & Reggae', '/programmes/genres/music/soulandreggae'),
      ('World', '/programmes/genres/music/world')]),
    ('News', '/programmes/genres/news', []),
    ('Religion & Ethics', '/programmes/genres/religionandethics', []),
    ('Sport', '/programmes/genres/sport',
     [('Alpine Skiing', '/programmes/genres/sport/alpineskiing'),
      ('American Football', '/programmes/genres/sport/americanfootball'),
      ('Archery', '/programmes/genres/sport/archery'),
      ('Athletics', '/programmes/genres/sport/athletics'),
      ('Badminton', '/programmes/genres/sport/badminton'),
      ('Baseball', '/programmes/genres/sport/baseball'),
      ('Basketball', '/programmes/genres/sport/basketball'),
      ('Beach Volleyball', '/programmes/genres/sport/beachvolleyball'),
      ('Biathlon', '/programmes/genres/sport/biathlon'),
      ('Bobsleigh', '/programmes/genres/sport/bobsleigh'),
      ('Bowls', '/programmes/genres/sport/bowls'),
      ('Boxing', '/programmes/genres/sport/boxing'),
      ('Canoeing', '/programmes/genres/sport/canoeing'),
      ('Commonwealth Games', '/programmes/genres/sport/commonwealthgames'),
      ('Cricket', '/programmes/genres/sport/cricket'),
      ('Cross Country Skiing', '/programmes/genres/sport/crosscountryskiing'),
      ('Curling', '/programmes/genres/sport/curling'),
      ('Cycling', '/programmes/genres/sport/cycling'),
      ('Darts', '/programmes/genres/sport/darts'),
      ('Disability Sport', '/programmes/genres/sport/disabilitysport'),
      ('Diving', '/programmes/genres/sport/diving'),
      ('Equestrian', '/programmes/genres/sport/equestrian'),
      ('Fencing', '/programmes/genres/sport/fencing'),
      ('Figure Skating', '/programmes/genres/sport/figureskating'),
      ('Football', '/programmes/genres/sport/football'),
      ('Formula One', '/programmes/genres/sport/formulaone'),
      ('Freestyle Skiing', '/programmes/genres/sport/freestyleskiing'),
      ('Gaelic Games', '/programmes/genres/sport/gaelicgames'),
      ('Golf', '/programmes/genres/sport/golf'),
      ('Gymnastics', '/programmes/genres/sport/gymnastics'),
      ('Handball', '/programmes/genres/sport/handball'),
      ('Hockey', '/programmes/genres/sport/hockey'),
      ('Horse Racing', '/programmes/genres/sport/horseracing'),
      ('Ice Hockey', '/programmes/genres/sport/icehockey'),
      ('Judo', '/programmes/genres/sport/judo'),
      ('Luge', '/programmes/genres/sport/luge'),
      ('Modern Pentathlon', '/programmes/genres/sport/modernpentathlon'),
      ('Motorsport', '/programmes/genres/sport/motorsport'),
      ('Netball', '/programmes/genres/sport/netball'),
      ('Nordic Combined', '/programmes/genres/sport/nordiccombined'),
      ('Olympics', '/programmes/genres/sport/olympics'),
      ('Rowing', '/programmes/genres/sport/rowing'),
      ('Rugby League', '/programmes/genres/sport/rugbyleague'),
      ('Rugby Union', '/programmes/genres/sport/rugbyunion'),
      ('Sailing', '/programmes/genres/sport/sailing'),
      ('Shinty', '/programmes/genres/sport/shinty'),
      ('Shooting', '/programmes/genres/sport/shooting'),
      ('Short Track Skating', '/programmes/genres/sport/shorttrackskating'),
      ('Skeleton', '/programmes/genres/sport/skeleton'),
      ('Ski Jumping', '/programmes/genres/sport/skijumping'),
      ('Snooker', '/programmes/genres/sport/snooker'),
      ('Snowboarding', '/programmes/genres/sport/snowboarding'),
      ('Softball', '/programmes/genres/sport/softball'),
      ('Speed Skating', '/programmes/genres/sport/speedskating'),
      ('Squash', '/programmes/genres/sport/squash'),
      ('Swimming', '/programmes/genres/sport/swimming'),
      ('Synchronised Swimming', '/programmes/genres/sport/synchronisedswimming'),
      ('Table Tennis', '/programmes/genres/sport/tabletennis'),
      ('Taekwondo', '/programmes/genres/sport/taekwondo'),
      ('Tennis', '/programmes/genres/sport/tennis'),
      ('Triathlon', '/programmes/genres/sport/triathlon'),
      ('Volleyball', '/programmes/genres/sport/volleyball'),
      ('Water Polo', '/programmes/genres/sport/waterpolo'),
      ('Weightlifting', '/programmes/genres/sport/weightlifting'),
      ('Winter Olympics', '/programmes/genres/sport/winterolympics'),
      ('Winter Sports', '/programmes/genres/sport/wintersports'),
      ('Wrestling', '/programmes/genres/sport/wrestling')]),
    ('Weather', '/programmes/genres/weather', [])
]


RADIO_FORMATS = [
    ('Animation', '/programmes/formats/animation', []),
    ('Appeals', '/programmes/formats/appeals', []),
    ('Audiobooks', '/programmes/formats/audiobooks', []),
    ('Bulletins', '/programmes/formats/bulletins', []),
    ('Discussion & Talk', '/programmes/formats/discussionandtalk', []),
    ('Docudramas', '/programmes/formats/docudramas', []),
    ('Documentaries', '/programmes/formats/documentaries', []),
    ('Films', '/programmes/formats/films', []),
    ('Games & Quizzes', '/programmes/formats/gamesandquizzes', []),
    ('Magazines & Reviews', '/programmes/formats/magazinesandreviews', []),
    ('Makeovers', '/programmes/formats/makeovers', []),
    ('Mixes', '/programmes/formats/mixes', []),
    ('Performances & Events', '/programmes/formats/performancesandevents', []),
    ('Phone-ins', '/programmes/formats/phoneins', []),
    ('Podcasts', '/programmes/formats/podcasts', []),
    ('Readings', '/programmes/formats/readings', []),
    ('Reality', '/programmes/formats/reality', []),
    ('Talent Shows', '/programmes/formats/talentshows', [])
]

RADIO_CATEGORIES = {"genres": RADIO_GENRES, "formats": RADIO_FORMATS}

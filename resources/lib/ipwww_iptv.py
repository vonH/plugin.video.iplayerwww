import socket
import json
from datetime import datetime, timedelta, timezone

import xbmc

from resources.lib.ipwww_video import (
    channel_list as tv_channel_list,
    SelectSynopsis,
    SelectImage)

from resources.lib.ipwww_common import (
    addonid,
    utf8_quote_plus,
    ADDON,
    OpenRequest)


# IPTVManager class from https://github.com/add-ons/service.iptv.manager/wiki/Integration
class IPTVManager:
    """Interface to IPTV Manager"""

    def __init__(self, port):
        """Initialize IPTV Manager object"""
        self.port = port

    def via_socket(func):
        """Send the output of the wrapped function to socket"""

        def send(self):
            """Decorator to send over a socket"""
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect(('127.0.0.1', self.port))
            try:
                sock.sendall(json.dumps(func(self)).encode())
            finally:
                sock.close()

        return send

    @via_socket
    def send_channels(self):
        """Return JSON-STREAMS formatted python datastructure to IPTV Manager"""
        tv_chans = enabled_channels(ADDON.getSetting('iptv.tv_channels').split(';'),
                                    tv_channel_list)
        return {'version': 1, 'streams': tv_chans}

    @via_socket
    def send_epg(self):
        """Return JSON-EPG formatted python data structure to IPTV Manager"""
        guide = tv_epg()
        return {'version': 1, 'epg': guide}


def channels(port):
    xbmc.log(f"[ipwww_iptv] Sending IPTV channels list.", xbmc.LOGDEBUG)
    try:
        IPTVManager(int(port)).send_channels()
    except Exception as err:
        # Catch all errors to prevent default() showing an error message
        xbmc.log(f"[ipwww_iptv] Error in iptvmanager.channels: {err!r}.", xbmc.LOGERROR)


def epg(port):
    try:
        IPTVManager(int(port)).send_epg()
    except Exception as err:
        # Catch all errors to prevent default() showing an error message
        xbmc.log(f"[ipwww_iptv] Error in iptvmanager.epg: {err!r}.", xbmc.LOGDEBUG)


def enabled_channels(enabled_ids, all_channels):
    mode = '203'
    # BBC Two England has the same channel ID as BBC TWO (HD) and is filtered out to
    # prevent both appearing in the TV list when BBC Two is enabled.
    enabled_chans = [chan for chan in all_channels if chan[0] in enabled_ids and chan[1] != 'BBC Two England']
    chan_list = []
    for chan in enabled_chans:
        chan_id = chan[0]
        chan_name = chan[1]
        iconimage = f'resource://resource.images.iplayerwww/media/{chan_id}.png'
        url = ''.join((
            'plugin://', addonid,
            '?url=', utf8_quote_plus(chan_id),
            '&mode=', mode,
            '&name=', utf8_quote_plus(chan_name),
            '&iconimage', utf8_quote_plus(iconimage)
        ))
        chan_list.append(
            {'id': 'ipwww.' + chan_id,
             'name': chan_name,
             'logo': iconimage,
             'stream': url,
             'radio': False}
        )
    return chan_list


def tv_epg():
    """Return the full TV EPG from 7 days back to 7 days ahead.

    """
    utc_now = datetime.now(timezone.utc)
    week_back = utc_now - timedelta(days=7)
    enabled_chan_ids = ADDON.getSetting('iptv.tv_channels').split(';')
    items_per_page = 200        # max allowed number
    tv_guide = {}
    xbmc.log(f"[ipwww_iptv] Creating IPTV EPG for channels {enabled_chan_ids}.", xbmc.LOGDEBUG)

    for chan_id in enabled_chan_ids:
        # There are no schedules specifically for HD channels.
        if chan_id == 'bbc_one_hd':
            schedule_chan_id = 'bbc_one_london'
        elif chan_id.endswith('_hd'):
            schedule_chan_id = chan_id[:-3]
        elif chan_id:
            schedule_chan_id = chan_id
        else:
            continue

        progr_list = []
        # Range is just to ensure we break out of the loop at some point if something goes
        # wrong with counting received items. Schedules should never have more than 2000
        # items in 2 weeks.
        for pagenr in range(1, 10):
            url = ''.join(('https://ibl.api.bbc.co.uk/ibl/v1/channels/',
                           schedule_chan_id,
                           '/broadcasts?per_page=',
                           str(items_per_page),
                           '&page=',
                           str(pagenr),
                           '&from_date=',
                           week_back.strftime('%Y-%m-%dT%H:%M')))
            resp_data = json.loads(OpenRequest('get', url))
            schedule_list = resp_data['broadcasts']['elements']
            for progr in schedule_list:
                episode = progr['episode']
                categories = episode.get('categories')
                if episode.get('status') == 'available':
                    url = 'https://www.bbc.co.uk/iplayer/episode/' + episode['id']
                    stream = ''.join(('plugin://',
                                      addonid,
                                      '?url=', utf8_quote_plus(url),
                                      '&mode=202'))  # &iconimage=&description=
                else:
                    stream = None
                progr_list.append({
                    'start': progr['scheduled_start'],
                    'stop': progr['scheduled_end'],
                    'title': episode.get('title'),
                    'description': SelectSynopsis(episode.get('synopses')),
                    'subtitle': episode.get('editorial_subtitle') or episode.get('subtitle'),
                    'genre': categories[0] if categories else None,
                    'image': SelectImage(episode.get('images')),
                    'date': episode.get('release_date_time'),
                    'stream': stream
                })
            if pagenr * items_per_page >= resp_data['broadcasts']['count']:
                break

        tv_guide['ipwww.' + chan_id] = progr_list
    return tv_guide

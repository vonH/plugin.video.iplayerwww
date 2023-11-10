
import xbmc

from resources.lib import ipwww_common
from resources.lib import ipwww_video


def parse_watching(json_data):
    config = json_data.get('config')
    if not config:
        return
    programme_list = json_data.get('items', [])
    for item in programme_list:
        yield parse_watching_item(item)


def parse_watching_item(item_data):
    props = item_data.get('props')
    meta = item_data.get('meta')
    if not (props and meta and 'href' in props):
        xbmc.log("[iPLayer WWW.parse_watching_item] Unparsable item: {}".format(item_data))
        return

    url = 'https://www.bbc.co.uk' + props['href']
    remaining_seconds = meta.get('remaining')
    if remaining_seconds:
        title = '{} - [I]{} min left[/I]'.format(props.get('title', ''), int(remaining_seconds / 60))
        duration_str = props.get('durationSubLabel', '0').split()[0]
        duration = int(duration_str) * 60
        # Resume a little bit earlier, so you can easily recognise where you've left off.
        resume_time = max(int(duration - meta.get('remaining', duration)) - 10, 0)
    else:
        title = '{} - [I]next episode[/I]'.format(props.get('title', ''))
        duration = ''
        resume_time = ''
    info = '\n'.join((props.get('title', ''), props.get('subtitle', ''), props.get('secondarySubLabel', '')))
    image = props.get('imageTemplate', 'DefaultFolder.png').replace('{recipe}', '832x468')
    return {'name': title, 'url': url, 'iconimage': image, 'plot': info,
            'resume_time': str(resume_time), 'total_time': str(duration)}

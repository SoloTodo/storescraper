import json
import re
import traceback
import validators

import requests
from bs4 import BeautifulSoup


def flixmedia_video_urls(mpn):
    try:
        session = requests.Session()

        url = 'https://media.flixcar.com/delivery/js/inpage/4800/cl/mpn/{}/' \
            ''.format(mpn)

        response = session.get(url).text
        match = re.search('product: \'(.+)\'', response)

        if not match:
            return None

        product_id = int(match.groups()[0])

        if not product_id:
            return None

        url = 'https://media.flixcar.com/delivery/inpage/show/4800/cl/{}/' \
            'html'.format(product_id)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        video_containers = soup.findAll('input', 'flix-jw')
        video_urls = []

        for container in video_containers:
            data = json.loads(container['value'])
            for entry in data['playlist']:
                if (validators.url(entry['file'])):
                    video_urls.append(entry['file'])
                else:
                    video_urls.append('https:' + entry['file'])

        return video_urls
    except Exception as e:
        print(e)
        traceback.print_exc()
        return None

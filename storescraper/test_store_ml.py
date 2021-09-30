import json
import re

import requests
from bs4 import BeautifulSoup


def main():
    url = 'https://www.mercadolibre.cl/tienda/apple'
    response = requests.get(url)
    json_container = re.search(
        r'window.__PRELOADED_STATE__ =([\S\s]+?);\n',
        response.text)
    import ipdb
    ipdb.set_trace()




if __name__ == '__main__':
    main()

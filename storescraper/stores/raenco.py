import logging
import re
from decimal import Decimal

from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER, ALL_IN_ONE, CELL, \
    HEADPHONES, MONITOR, NOTEBOOK, OVEN, PRINTER, REFRIGERATOR, \
    STEREO_SYSTEM, TABLET, TELEVISION, WASHING_MACHINE, WEARABLE

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Raenco(Store):
    @classmethod
    def categories(cls):
        return [
            REFRIGERATOR,
            WASHING_MACHINE,
            OVEN,
            AIR_CONDITIONER,
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            ALL_IN_ONE,
            NOTEBOOK,
            MONITOR,
            TABLET,
            WEARABLE,
            PRINTER,
            HEADPHONES,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ["hogar/linea-blanca/refrigeradoras.html", REFRIGERATOR],
            ["hogar/linea-blanca/lavadora.html", WASHING_MACHINE],
            ["hogar/linea-blanca/secadoras.html", WASHING_MACHINE],
            ["hogar/electrodomesticos/microondas.html", OVEN],
            ["aires-acondicionado.html", AIR_CONDITIONER],
            ["audio-y-video/tv/tv-led-hd-fhd.html", TELEVISION],
            ["audio-y-video/tv/tv-4k.html", TELEVISION],
            ["audio-y-video/tv/tv-crystal-uhd.html", TELEVISION],
            ["audio-y-video/tv/tv-nanocell.html", TELEVISION],
            ["audio-y-video/tv/tv-qled.html", TELEVISION],
            ["audio-y-video/equipos-de-sonido.html", STEREO_SYSTEM],
            ["audio-y-video/sound-bar.html", STEREO_SYSTEM],
            ["tecnologia/celulares.html", CELL],
            ["tecnologia/computadoras/desktop.html", ALL_IN_ONE],
            ["tecnologia/computadoras/core-i3-ryzen-3.html", NOTEBOOK],
            ["tecnologia/computadoras/core-i5-ryzen-5.html", NOTEBOOK],
            ["tecnologia/computadoras/core-i7-ryzen-7.html", NOTEBOOK],
            ["tecnologia/computadoras/celeron", NOTEBOOK],
            ["tecnologia/computadoras/monitores", MONITOR],
            ["tecnologia/tablet.html", TABLET],
            ["tecnologia/reloj-smartwatch.html", WEARABLE],
            ["tecnologia/impresora-y-escaner.html", PRINTER],
            ["tecnologia/audifonos-y-bocinas.html", HEADPHONES],
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        lg_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            local_urls = []
            done = False

            while True:
                if page >= 15:
                    raise Exception('Page overflow')

                url = 'https://raenco.com/index.php/departamentos/{}?p={}'\
                    .format(category_path, page)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('li', 'product')

                if not product_containers and page == 1:
                    logging.warning('Empty section {}'.format(category_path))
                    break

                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break

                    if 'LG' in container.find(
                            'strong', 'product-item-name').text.upper():
                        lg_urls.append(product_url)

                    local_urls.append(product_url)

                if done:
                    break

                product_urls.extend(local_urls)

                page += 1

        return list(set(lg_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url, allow_redirects=False)

        if response.status_code in [303, 500]:
            return []

        data = response.text

        if 'fatal error' in data.lower():
            return []

        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', 'page-title').text.strip()
        stock_and_sku = soup.find('div', 'product-info-stock-sku')
        sku = stock_and_sku.find('div', {'itemprop': 'sku'}).text.strip()
        stock_div = stock_and_sku.find('div', 'stock')
        stock = int(stock_div.text.replace(
            stock_div.find('span').text, '').strip())

        price = Decimal(soup.find('meta', {'itemprop': 'price'})['content'])

        image = soup.find('img', 'gallery-placeholder__image')['src']

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=[image]
        )

        return [p]

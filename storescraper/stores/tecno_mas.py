import json
import logging
import urllib
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import (
    VIDEO_CARD, ALL_IN_ONE, NOTEBOOK, PROCESSOR, MOTHERBOARD,
    SOLID_STATE_DRIVE, RAM, PRINTER, MONITOR, MOUSE, COMPUTER_CASE,
    EXTERNAL_STORAGE_DRIVE, STORAGE_DRIVE, TABLET, POWER_SUPPLY, GAMING_CHAIR,
    CELL, TELEVISION, UPS)
from storescraper.product import Product
from storescraper.store_with_url_extensions import StoreWithUrlExtensions
from storescraper.utils import session_with_proxy, remove_words


class TecnoMas(StoreWithUrlExtensions):
    url_extensions = [
        ['Notebooks', NOTEBOOK],
        ['Notebooks Reacondicionados', NOTEBOOK],
        ['Macbook', NOTEBOOK],
        ['Apple', NOTEBOOK],
        ['SSD - Disco Sólido', SOLID_STATE_DRIVE],
        ['HDD - Disco Duros', STORAGE_DRIVE],
        ['Monitores', MONITOR],
        ['Procesadores', PROCESSOR],
        ['Impresoras de Hogar', PRINTER],
        ['Placas Madre', MOTHERBOARD],
        ['Impresoras de Oficina', PRINTER],
        ['Impresoras', PRINTER],
        ['Almacenamiento', SOLID_STATE_DRIVE],
        ['Teclados y Mouse', MOUSE],
        ['Tarjetas de Video', VIDEO_CARD],
        ['All in One (AIO)', ALL_IN_ONE],
        ['AIOs Reacondicionados', ALL_IN_ONE],
        ['PC Oficina', ALL_IN_ONE],
        ['RAM', RAM],
        ['SO-DIMM', RAM],
        ['Gabinetes', COMPUTER_CASE],
        ['Almacenamiento Externo', EXTERNAL_STORAGE_DRIVE],
        ['Tablets', TABLET],
        ['Fuentes de Poder', POWER_SUPPLY],
        ['Sillas', GAMING_CHAIR],
        ['Celulares', CELL],
        ['Televisores', TELEVISION],
        ['UPS', UPS],
    ]

    @classmethod
    def discover_urls_for_url_extension(cls, url_extension, extra_args):
        session = session_with_proxy(extra_args)
        product_urls = []
        page = 0
        while True:
            if page > 10:
                raise Exception('page overflow: ' + url_extension)

            facet_filters = urllib.parse.quote(json.dumps(
                [['category:{}'.format(url_extension)]]
            ))

            payload = {
                'requests': [
                    {
                        'indexName': 'Product_production',
                        'params': 'facetFilters={}&hitsPerPage=48'
                                  '&page={}'.format(facet_filters, page)
                    }
                ]
            }

            response = session.post(
                'https://wnp9zg9fi5-dsn.algolia.net/1/indexes/*/queries?'
                'x-algolia-api-key=290ed9c571e4c27390d1e57e291379f0&'
                'x-algolia-application-id=WNP9ZG9FI5',
                json=payload
            )

            json_data = response.json()

            product_containers = json_data['results'][0]['hits']
            if not product_containers:
                if page == 0:
                    logging.warning('Empty category: ' + url_extension)
                break
            for container in product_containers:
                product_urls.append(
                    'https://www.tecnomas.cl/producto/{}'.format(
                        container['slug']))
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        if response.status_code == 500:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('h1').text.strip()
        key = soup.find('input', {'id': 'product_id'})['value']
        sku = soup.find('p', {'id': 'sku-' + key}).text.replace(
            'SKU: ', '').strip()

        stock_text = soup.find('p', {'id': 'stock-' + key}).text.strip()

        if 'Sin stock' in stock_text:
            stock = 0
        else:
            stock = -1

        if soup.find('span', text='Reacondicionado'):
            condition = 'https://schema.org/RefurbishedCondition'
        elif soup.find('span', text='Caja Abierta'):
            condition = 'https://schema.org/OpenBoxCondition'
        elif soup.find('span', text='Usado'):
            condition = 'https://schema.org/UsedCondition'
        else:
            condition = 'https://schema.org/NewCondition'

        offer_price_tag = soup.find(
            'span', {'id': 'wire-transfer-price-' + key})
        offer_price = Decimal(remove_words(offer_price_tag.text))

        normal_price_tag = soup.find(
            'span', {'id': 'webpay-price-' + key})
        normal_price = Decimal(remove_words(normal_price_tag.text))

        picture_urls = [tag.find('img')['src'] for tag in
                        soup.findAll('div', 'swiper-slide')]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=sku,
            picture_urls=picture_urls,
            condition=condition
        )
        return [p]

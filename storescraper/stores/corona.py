import json
import urllib

import re
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Corona(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Television',
            'Tablet',
            'Refrigerator',
            'Printer',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'Camera',
            'StereoSystem',
            'OpticalDiskPlayer',
            'HomeTheater',
            'VideoGameConsole',
            'AllInOne',
            'WaterHeater',
            'SpaceHeater',
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_urls = [
            ['C:/9/39/40/', None, 'Notebook'],
            ['C:/9/35/36/', None, 'Television'],
            ['C:/9/39/42/', None, 'Tablet'],
            ['C:/8/11/13/', None, 'Refrigerator'],
            ['C:/8/11/14/', '&fq=specificationFilter_32%3a'
                            'Hornos+El%c3%a9ctricos', 'Oven'],
            ['C:/8/11/14/', '&fq=specificationFilter_32'
                            '%3aMicroondas', 'Oven'],
            ['C:/8/11/12/', None, 'WashingMachine'],
            ['C:/44/45/', None, 'Cell'],
            ['C:/9/48/49/', None, 'StereoSystem'],
            # ['tecnologia/audio/home-theater', None, 'HomeTheater'],
            ['C:/9/35/37/', None, 'OpticalDiskPlayer'],
            ['C:/8/11/14/', '&fq=specificationFilter_32'
                            '%3aAspiradoras', 'VacuumCleaner'],
            # ['C:/9/56/57/', None, 'VideoGameConsole'],
            ['C:/8/11/15/', '&fq=specificationFilter_26%3aCalefont',
             'WaterHeater'],
            # ['C:/8/11/15/', '&fq=specificationFilter_26%3a'
            #                 'Calefactores+y+Termoventiladores',
            # 'SpaceHeater'],
            ['C:/8/11/15/', '&fq=specificationFilter_26%3aEstufas+a+Gas',
             'SpaceHeater'],
            ['C:/8/11/15/', '&fq=specificationFilter_26%3aEstufas+a+Le%c3%b1a',
             'SpaceHeater'],
            ['C:/8/11/15/', '&fq=specificationFilter_26%3aEstufas+a+Parafina',
             'SpaceHeater'],
            ['C:/8/11/15/', '&fq=specificationFilter_26%3a'
                            'Estufas+El%c3%a9ctricas', 'SpaceHeater'],
            ['C:/8/11/15/', '&fq=specificationFilter_26%3aAire+Acondicionado',
             'AirConditioner'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, extra_url_args, local_category in category_urls:
            if local_category != category:
                continue

            page = 1

            if extra_url_args is None:
                extra_url_args = ''

            while True:
                url = 'http://www.corona.cl/buscapagina?fq={}{}&PS=50&' \
                      'sl=e5ea4f52-95a2-43cf-874e-70d89cd91dce&cc=3&' \
                      'sm=0&PageNumber={}'.format(
                          urllib.parse.quote_plus(category_path),
                          extra_url_args,
                          page)
                if page >= 10:
                    raise Exception('Page overflow: ' + category_path)
                print(url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                product_blocks = soup.findAll('div', 'product-block')

                if not product_blocks:
                    if page == 1:
                        raise Exception('Empty category: {} - {} {}'.format(
                            category, category_path, extra_url_args))
                    else:
                        break

                for block in product_blocks:
                    if block.find('div', 'outOfStock'):
                        continue
                    url = block.find('a')['href']
                    product_urls.append(url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        page_source = session.get(url).text
        soup = BeautifulSoup(page_source, 'html.parser')

        if soup.find('p', 'title-not-found'):
            return []

        description_text = re.search(
            r'<div class="row detalles-producto">[\S\s]*'
            r'<div class="row recomendados-productos">',
            page_source)

        if description_text:
            description = html_to_markdown(description_text.group())
        else:
            description = ''

        sku = soup.find('div', 'skuReference').text.strip()

        # Pictures

        picture_urls = []
        gallery_links = soup.findAll('a', {'id': 'botaoZoom'})
        for link in gallery_links:
            picture_url = link['zoom']
            if not picture_url:
                picture_url = link['rel'][0]
            picture_urls.append(picture_url)

        # Offer price

        offer_price = None
        corona_price_container = soup.find('td', 'Oferta')
        if corona_price_container:
            offer_price_text = corona_price_container.string.split(
                '$')[-1].split('Con')[0]

            try:
                offer_price = Decimal(remove_words(offer_price_text))
            except InvalidOperation:
                pass

        # SKUS pricing

        skus_data = re.search(r'var skuJson_0 = ([\S\s]+?);',
                              page_source).groups()[0]

        skus_data = json.loads(skus_data)
        products = []

        for sku_data in skus_data['skus']:
            name = sku_data['skuname']
            key = str(sku_data['sku'])
            stock = sku_data['availablequantity']

            normal_price = Decimal(sku_data['bestPrice'] / 100)

            if offer_price and offer_price < normal_price:
                sku_offer_price = offer_price
            else:
                sku_offer_price = normal_price

            products.append(Product(
                name,
                cls.__name__,
                category,
                url,
                url,
                key,
                stock,
                normal_price,
                sku_offer_price,
                'CLP',
                sku=sku,
                description=description,
                picture_urls=picture_urls
            ))

        return products

import json
import urllib

import re
from collections import defaultdict

from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation

from storescraper.flixmedia import flixmedia_video_urls
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Corona(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_urls = [
            ['C:/8/122/124', None, ['Cell'],
             'Telefonía > Celulares > Smartphones', 1],
        ]

        product_entries = defaultdict(lambda: [])
        session = session_with_proxy(extra_args)

        for category_path, extra_url_args, local_categories, section_name, \
                category_weight in category_urls:
            if category not in local_categories:
                continue

            page = 1

            if extra_url_args is None:
                extra_url_args = ''

            idx = 0

            while True:
                url = 'http://www.corona.cl/buscapagina?fq={}{}&PS=60&' \
                      'sl=e5ea4f52-95a2-43cf-874e-70d89cd91dce&cc=3&' \
                      'sm=0&PageNumber={}'.format(
                          urllib.parse.quote_plus(category_path),
                          extra_url_args,
                          page)
                if page >= 40:
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
                    idx += 1
                    if block.find('div', 'outOfStock'):
                        continue
                    url = block.find('a')['href']
                    product_entries[url].append({
                        'category_weight': category_weight,
                        'section_name': section_name,
                        'value': idx
                    })

                page += 1

        return product_entries

    @classmethod
    def discover_urls_for_keyword(cls, keyword, threshold, extra_args=None):
        session = session_with_proxy(extra_args)
        product_urls = []

        page = 1

        while True:
            if page >= 40:
                raise Exception('Page overflow: ' + keyword)

            url = 'https://www.corona.cl/buscapagina?ft={}&PS=15&' \
                  'sl=4e4d7aaa-6b5b-4390-8d3a-e6ce5e306488&cc=3&sm=0' \
                  '&PageNumber={}'.format(keyword, page)

            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')
            product_blocks = soup.findAll('div', 'product')

            if not product_blocks:
                break

            for block in product_blocks:
                if block.find('div', 'outOfStock'):
                    continue
                product_url = block.find('a')['href']
                product_urls.append(product_url)

                if len(product_urls) == threshold:
                    return product_urls

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

        flixmedia_id = None
        video_urls = None

        flixmedia_tag = soup.find(
            'script', {'src': '//media.flixfacts.com/js/loader.js'})
        if flixmedia_tag:
            mpn = flixmedia_tag['data-flix-mpn'].strip()
            video_urls = flixmedia_video_urls(mpn)
            if video_urls is not None:
                flixmedia_id = mpn

        # SKUS pricing

        skus_data = re.search(r'var skuJson_0 = ([\S\s]+?);',
                              page_source).groups()[0]

        skus_data = json.loads(skus_data)
        products = []

        for sku_data in skus_data['skus']:
            name = sku_data['skuname']
            key = str(sku_data['sku'])
            stock = sku_data['availablequantity']

            if stock == 99999:
                stock = -1

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
                picture_urls=picture_urls,
                video_urls=video_urls,
                flixmedia_id=flixmedia_id
            ))

        return products

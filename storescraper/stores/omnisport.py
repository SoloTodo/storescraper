import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy
from storescraper.categories import TELEVISION, STEREO_SYSTEM, CELL, \
    REFRIGERATOR, OVEN, AIR_CONDITIONER, WASHING_MACHINE, \
    OPTICAL_DISK_PLAYER, STOVE, VACUUM_CLEANER


class Omnisport(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION,
            STEREO_SYSTEM,
            CELL,
            REFRIGERATOR,
            OVEN,
            AIR_CONDITIONER,
            WASHING_MACHINE,
            OPTICAL_DISK_PLAYER,
            STOVE,
            VACUUM_CLEANER
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # KEEPS ONLY LG PRODUCTS

        category_filters = [
            TELEVISION
        ]
        session = session_with_proxy(extra_args)
        product_urls = []

        for local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 20:
                    raise Exception('Page overflow')

                url = 'https://www.omnisport.com/marcas/lg?page={}' \
                      ''.format(page)
                print(url)

                res = session.get(url, verify=False)

                if res.url != url:
                    break

                soup = BeautifulSoup(res.text, 'html.parser')
                containers = soup.findAll('div', 'lg:w-1/3')

                if not containers:
                    break

                for container in containers:
                    if 'lg' in container.find('p', 'text-black').text.lower():
                        link = container.find('a', 'link-basic')
                        product_urls.append(link['href'])

                page += 1

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url, verify=False)

        soup = BeautifulSoup(response.text, 'html.parser')
        sku = soup.find('p', 'text-gray-700').contents[1].split('|')[0].strip()
        name = soup.find('h1').text.strip()
        price = Decimal(soup.find('p', 'text-2xl').text.replace('$', ''))

        pictures_tag = soup.find('product-images-gallery')

        if pictures_tag:
            picture_urls = [x['full_url'] for x in
                            json.loads(pictures_tag[':images'])]
        else:
            picture_urls = [soup.find('div', 'md:w-2/5').find('img')['src']]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'USD',
            sku=sku,
            picture_urls=picture_urls
        )

        return [p]

    @staticmethod
    def fix_price(price):
        fixed_price = price
        if price.count('.') > 1:
            split_price = price.split('.')
            fixed_price = split_price[0] + '.' + split_price[1]
        return Decimal(fixed_price.replace('$', '').replace(',', ''))

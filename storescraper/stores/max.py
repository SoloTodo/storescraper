import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Max(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'Refrigerator',
            'Oven',
            'AirConditioner',
            'WashingMachine',
            'OpticalDiskPlayer',
            'Stove',
            'Monitor',
            'Projector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('video/televisores', 'Television'),
            # ('video/cine-en-casa', 'StereoSystem'),
            # ('video/reproductores-dvd', 'OpticalDiskPlayer'),
            ('celulares/prepago', 'Cell'),
            ('celulares/prepago/tigo', 'Cell'),
            # ('celulares/prepago/claro', 'Cell'),
            # ('celulares/prepago/movistar', 'Cell'),
            ('celulares/liberados', 'Cell'),
            # ('lineablanca/combos-lavadora-y-secadora', 'WashingMachine'),
            ('lineablanca/secadoras', 'WashingMachine'),
            ('lineablanca/lavadoras', 'WashingMachine'),
            ('lineablanca/empotrables', 'Oven'),
            # ('lineablanca/estufas/hornos-empotrables', 'Oven'),
            ('electrodomesticos/microondas', 'Oven'),
            ('lineablanca/refrigeradoras/refrigeradoras', 'Refrigerator'),
            # ('lineablanca/refrigeradoras/congeladores', 'Refrigerator'),
            ('lineablanca/estufas/estufas-a-gas', 'Stove'),
            ('lineablanca/estufas/estufas-electricas', 'Stove'),
            ('lineablanca/estufas/cooktops-a-gas', 'Stove'),
            # ('lineablanca/estufas/cooktops-electricos', 'Stove'),
            ('computacion/proyectores', 'Projector'),
            ('audio', 'StereoSystem'),
            # ('audio/audio-para-casa/micro-componente', 'StereoSystem'),
            ('audio/audio-para-casa/mini-componente', 'StereoSystem'),
            ('audio/audio-para-casa/audio-vertical', 'StereoSystem'),
            ('audio/audio-portatil', 'StereoSystem'),
            # ('audio/audio-multizona', 'StereoSystem'),
            # ('computacion/pc-gaming/monitores', 'Monitor'),
            ('computacion/proyectores', 'Projector'),
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        lg_product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False
            local_urls = []

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.max.com.gt/{}?limit=30&p={}'.format(
                    category_path, page)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')

                items = soup.findAll('div', 'item')

                if page == 1 and not items:
                    raise Exception('No products for url {}'.format(url))

                for container in items:
                    logo = container.find('div', 'brand').find('img')
                    product_url = container.find('a')['href']

                    if product_url in local_urls:
                        done = True
                        break

                    if logo and logo['src'] == \
                            'https://www.max.com.gt/media/marcas/lg.jpg':
                        lg_product_urls.append(product_url)
                    local_urls.append(container.find('a')['href'])

                if done:
                    break

                page += 1

            product_urls.extend(local_urls)

        return list(set(lg_product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        sku = soup.find('h6', 'sku').text.strip()
        name = '{} ({})'.format(soup.find('h1').text.strip(), sku)

        if not soup.find('input', {'id': 'qty_stock'}):
            stock = 0
        else:
            stock = int(soup.find('input', {'id': 'qty_stock'})['value'])

        price_container = soup.find('span', {'itemprop': 'price'})
        price = Decimal(price_container.text.replace('Q', '').replace(',', ''))

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'fancybox-button')]
        description = html_to_markdown(
            str(soup.find('div', 'tab-product-detail')))

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
            'GTQ',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]

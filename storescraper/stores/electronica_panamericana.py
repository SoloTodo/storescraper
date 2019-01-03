import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class ElectronicaPanamericana(Store):
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
            'Headphones',
            'Monitor',
            'Projector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('hogar/electrodomesticos/hornos-microondas', 'Oven'),
            ('hogar/estufas/cooktop', 'Stove'),
            ('hogar/estufas/estufas-a-gas', 'Stove'),
            ('hogar/estufas/estufas-electricas', 'Stove'),
            ('hogar/hornos-empotrables', 'Oven'),
            ('hogar/lavanderia/centros-de-lavanderia', 'WashingMachine'),
            ('hogar/lavanderia/lavadoras', 'WashingMachine'),
            ('hogar/refrigeracion/congeladores', 'Refrigerator'),
            ('hogar/refrigeracion/refrigeradoras', 'Refrigerator'),
            ('tecnologia/audio-tecnologia', 'StereoSystem'),
            ('tecnologia/barras', 'StereoSystem'),
            ('tecnologia/celulares', 'Cell'),
            ('tecnologia/monitores', 'Monitor'),
            ('tecnologia/proyectores', 'Projector'),
            ('tv-y-video/4k', 'Television'),
            ('tv-y-video/oled-tv', 'Television'),
            ('tv-y-video/super-uhd', 'Television'),
            ('tv-y-video/televisores', 'Television'),
            ('tv-y-video/video', 'OpticalDiskPlayer'),

        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://electronicapanamericana.com/tienda/' \
                      'categoria-producto/{}/page/{}/' \
                      ''.format(category_path, page)
                print(url)
                response = session.get(url)

                if response.status_code == 404:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                soup = BeautifulSoup(response.text, 'html.parser')

                for container in soup.findAll('li', 'product'):
                    product_url = container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        sku = soup.find('span', 'sku').text.strip()
        name = '{} ({})'.format(
            soup.find('h1', 'entry-title-main').text.strip(), sku)
        stock = -1

        price_container = soup.find('span', 'woocommerce-Price-amount')
        price = Decimal(price_container.text.replace('Q', '').replace(',', ''))

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', {'itemprop': 'image'})]
        description = html_to_markdown(
            str(soup.find('div', 'woocommerce-tabs')))

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

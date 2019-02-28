import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Raenco(Store):
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
            'Stove',
            'Projector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('tecnologia/tv', 'Television'),
            ('tecnologia/tv/tv-led-hd-fhd', 'Television'),
            ('tecnologia/tv/lcd', 'Television'),
            ('tecnologia/tv/tv-4k', 'Television'),
            ('tecnologia/equipos-de-sonido', 'StereoSystem'),
            ('tecnologia/celulares', 'Cell'),
            ('tecnologia/celulares/8-gb-rom', 'Cell'),
            ('tecnologia/celulares/16-gb-rom', 'Cell'),
            ('tecnologia/celulares/32-gb-rom', 'Cell'),
            ('tecnologia/celulares/64-gb-rom', 'Cell'),
            ('tecnologia/celulares/128-gb-rom', 'Cell'),
            ('hogar/linea-blanca/refrigeradoras', 'Refrigerator'),
            ('hogar/linea-blanca/refrigeradoras/puerta-vertical',
             'Refrigerator'),
            ('hogar/linea-blanca/lavadoras', 'WashingMachine'),
            ('hogar/linea-blanca/lavadoras/semi-automaticas',
             'WashingMachine'),
            ('hogar/linea-blanca/lavadoras/centro-de-lavado-a-gas',
             'WashingMachine'),
            ('hogar/linea-blanca/lavadoras/lavadora-automatica',
             'WashingMachine'),
            ('hogar/linea-blanca/secadoras', 'WashingMachine'),
            ('hogar/aires-acondicionados', 'AirConditioner'),
            ('hogar/electrodomesticos/microondas', 'Oven'),
            ('hogar/linea-blanca/hornos-empotrable/horno-a-gas', 'Oven'),
            ('hogar/linea-blanca/estufas', 'Stove'),
            ('hogar/linea-blanca/estufas/a-gas-de-20-24-pulgadas', 'Stove'),
            ('hogar/linea-blanca/estufas/a-gas-de-30-y-36-pulgadas', 'Stove'),
            ('hogar/linea-blanca/estufas/estufas-electricas', 'Stove'),
            ('hogar/linea-blanca/estufas/estufas-empotrables', 'Stove'),
            ('hogar/linea-blanca/estufas/de-mesa-a-gas-electrica', 'Stove'),
            ('oficina/132/137', 'Projector'),
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            offset = 0
            local_urls = []
            done = False

            print(category_path)

            while True:
                if offset >= 200:
                    raise Exception('Page overflow')

                url = 'https://www.raenco.com/{}?start={}'.format(
                    category_path, offset)
                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('div', 'product')

                for container in product_containers:
                    product_url = 'https://www.raenco.com' + \
                                  container.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break

                    local_urls.append(product_url)

                if done:
                    break

                product_urls.extend(local_urls)

                offset += 12

        return list(set(product_urls))

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url).text
        soup = BeautifulSoup(data, 'html.parser')

        if not soup.find('span', 'addtocart-button'):
            return []

        name = soup.find('h1').text.strip()
        sku = re.search(r'/(\d+)-detail$', url).groups()[0]
        stock = -1

        price_container = soup.find('span', 'PricediscountedPriceWithoutTax')
        if not price_container:
            price_container = soup.find('span', 'PricebasePrice')

        price = Decimal(price_container.text.replace('$', '').replace(',', ''))

        part_number = None

        part_number_container = re.search(r'data-flix-mpn="(.+?)"', data)
        if part_number_container:
            part_number = part_number_container.groups()[0]

        picture_urls = ['https://www.raenco.com/images/virtuemart/product/{}'
                        '.jpg'.format(sku)]

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
            part_number=part_number,
            picture_urls=picture_urls
        )

        return [p]

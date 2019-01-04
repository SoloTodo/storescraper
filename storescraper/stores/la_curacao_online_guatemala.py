import json
import re
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class LaCuracaoOnlineGuatemala(Store):
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
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('electronica/celulares.html', 'Cell'),
            ('audio-y-video/televisores.html', 'Television'),
            ('audio-y-video/equipos-de-sonido.html', 'StereoSystem'),
            ('audio-y-video/reproductores-de-video.html', 'OpticalDiskPlayer'),
            ('hogar/ventilacion/aires-acondicionados.html', 'AirConditioner'),
            ('electrodomesticos/hornillas.html', 'Stove'),
            ('refrigeracion/refrigeradoras.html', 'Refrigerator'),
            ('refrigeracion/congeladores.html', 'Refrigerator'),
            ('lavadoras-y-secadoras/lavadoras.html', 'WashingMachine'),
            ('cocinas/microondas.html', 'Oven'),
        ]

        session = session_with_proxy(extra_args)

        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            local_urls = []
            done = False

            while True:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.lacuracaonline.com/guatemala/productos/{}' \
                      '?product_list_limit=36&p={}'.format(category_path, page)

                for i in range(5):
                    response = session.get(url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    product_containers = soup.findAll('li', 'product')
                    if product_containers:
                        break
                else:
                    # Called if no "break" was executed
                    raise Exception('Could not bypass Incapsulata')

                for container in product_containers:
                    product_url = container.find('a')['href']
                    if product_url in local_urls:
                        done = True
                        break

                    local_urls.append(product_url)

                if done:
                    break

                product_urls.extend(local_urls)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        for i in range(5):
            response = session.get(url)
            if response.status_code == 200:
                break
        else:
            # Called if no "break" was executed
            raise Exception('Could not bypass Incapsulata')

        soup = BeautifulSoup(response.text, 'html.parser')
        name = soup.find('span', {'itemprop': 'name'}).text.strip()
        sku = soup.find('div', {'itemprop': 'sku'}).text.strip()
        stock = -1
        price = Decimal(soup.find('span', 'price').text.replace(
            'Q', '').replace(',', ''))

        pictures_data = re.search(r'"mage/gallery/gallery": ([\s\S]*?)\}\n',
                                  response.text).groups()[0]
        pictures_json = json.loads(pictures_data + '}')
        picture_urls = [tag['full'] for tag in pictures_json['data']]

        description = '{}\n\n{}'.format(
            html_to_markdown(
                str(soup.find('div', 'additional-attributes-wrapper'))),
            html_to_markdown(str(soup.find('div', 'description')))
        )

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

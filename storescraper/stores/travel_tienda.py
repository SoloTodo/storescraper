from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TravelTienda(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Cell',
            'Television',
            'Tablet',
            'VideoGameConsole',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'Stove',
            'VacuumCleaner',
            'AllInOne',
            'Wearable',
            'Projector',
            'DishWasher',
            'AirConditioner',
            'StereoSystem',
            'Headphones'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.travelclub.cl/traveltienda/{}'

        category_filters = [
            ('categoria.asp?id=1566&idm=404', 'Notebook'),
            ('categoria.asp?id=1548&idm=447', 'Cell'),
            ('categoria.asp?id=1552&idm=404', 'Cell'),
            ('categoria.asp?id=1561&idm=483', 'Television'),
            ('categoria.asp?id=1550&idm=447', 'Tablet'),
            ('categoria.asp?id=1567&idm=404', 'Tablet'),
            ('categoria.asp?id=1419&idm=404', 'VideoGameConsole'),
            ('categoria.asp?id=1534&idm=438', 'Refrigerator'),
            ('categoria.asp?id=1535&idm=438', 'Refrigerator'),
            ('categoria.asp?id=1542&idm=480', 'WashingMachine'),
            ('categoria.asp?id=1543&idm=480', 'WashingMachine'),
            ('categoria.asp?id=1538&idm=436', 'Oven'),
            ('categoria.asp?id=1922&idm=436', 'Oven'),
            ('categoria.asp?id=1509&idm=476', 'Oven'),
            ('categoria.asp?id=1374&idm=476', 'Oven'),
            ('categoria.asp?id=1923&idm=436', 'Stove'),
            ('categoria.asp?id=1539&idm=436', 'Stove'),
            ('categoria.asp?id=1494&idm=473', 'VacuumCleaner'),
            ('categoria.asp?id=1870&idm=473', 'VacuumCleaner'),
            ('categoria.asp?id=1362&idm=404', 'AllInOne'),
            ('categoria.asp?id=1551&idm=447', 'Wearable'),
            ('categoria.asp?id=1858&idm=404', 'Wearable'),
            ('categoria.asp?id=1920&idm=404', 'Projector'),
            ('categoria.asp?id=1541&idm=480', 'DishWasher'),
            ('categoria.asp?id=1508&idm=475', 'AirConditioner'),
            ('categoria.asp?id=1563&idm=483', 'StereoSystem'),
            ('categoria.asp?id=1564&idm=483', 'StereoSystem'),
            ('categoria.asp?id=1565&idm=483', 'Headphones')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            url = base_url.format(category_path)
            print(url)

            soup = BeautifulSoup(session.get(url).text, 'html.parser')

            items = soup.findAll('div', 'contenedor-productos')

            for item in items:
                product_urls.append(base_url.format(item.parent['href']))

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('p', 'txt-nombre-producto').text

        if 'samsung' in name.lower():
            stock = -1
        else:
            stock = 0

        sku = soup.find('p', 'txt-sku').text.replace('SKU', '').strip()
        price = Decimal(soup.find('p', 'txt-precio').text
                        .replace('$', '').replace('.', '').strip())

        images = soup.find('div', {'id': 'img-thumb'}).findAll('img')
        picture_urls = ['https://www.travelclub.cl{}'.format(image['src'])
                        for image in images]

        description = html_to_markdown(
            str(soup.find('article', {'id': 'tab1'})))

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
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

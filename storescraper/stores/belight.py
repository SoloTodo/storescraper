from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Belight(Store):
    @classmethod
    def categories(cls):
        return [
            'Lamp',
            'LightTube',
            'LightProjector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Ampolletas LED
            ['ampolletas-led', 'Lamp'],
            # Proyectores LED
            ['proyectores-led', 'LightProjector'],
            # Tubos LED
            ['tubos-led', 'LightTube'],
        ]

        product_urls = []

        session = session_with_proxy(extra_args)

        for category_path, local_category in url_extensions:
            if local_category != category:
                continue

            category_url = 'http://www.belight.cl/productos/categoria/{}' \
                           ''.format(category_path)

            soup = BeautifulSoup(session.get(category_url).text,
                                 'html.parser')

            product_containers = soup.findAll('div', 'producto')

            for container in product_containers:
                product_url = 'http://www.belight.cl' + \
                              container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        name = soup.find('h1').text.strip()

        sku = soup.find('span', 'etiqueta').text.split(' : ')[-1].strip()

        description = html_to_markdown(
            str(soup.find('div', {'id': 'descripcion-producto'})))

        price_container = soup.find('div', 'valor').text

        if 'proyecto' in price_container.lower():
            return []

        normal_price = Decimal(remove_words(price_container.replace('.-', '')))
        offer_price = normal_price

        picture_tags = soup.find('div', 'slider-for').findAll('img')
        picture_urls = [picture['src'] for picture in picture_tags]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

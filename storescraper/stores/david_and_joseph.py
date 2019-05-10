from bs4 import BeautifulSoup
from decimal import Decimal
from collections import defaultdict

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class DavidAndJoseph(Store):
    @classmethod
    def categories(cls):
        return [
            'Monitor',
            'Headphones',
        ]

    @classmethod
    def discover_entries_for_category(cls, category, extra_args=None):
        category_paths = [
            ['video-pro/edicion-y-post-produccion/monitores-para-edicion',
             ['Monitor'],
             'Inicio > Video Pro > Edición y Post Producción > '
             'Monitores para Edición', 1],
            ['audio-pro/audifonos', ['Headphones'],
             'Inicio > Audio Pro > Audífonos', 1],
        ]

        session = session_with_proxy(extra_args)
        product_entries = defaultdict(lambda: [])

        for e in category_paths:
            category_path, local_categories, section_name, category_weight = e

            if category not in local_categories:
                continue

            category_url = 'http://davidandjoseph.cl/' + category_path

            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')
            link_containers = soup.findAll('div', 'product-list-item')

            if not link_containers:
                raise Exception('Empty category: ' + category_url)

            for idx, link_container in enumerate(link_containers):
                product_url = link_container.find('a')['href']
                product_entries[product_url].append({
                    'category_weight': category_weight,
                    'section_name': section_name,
                    'value': idx + 1
                })

        return product_entries

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', 'heading-title').text.strip()
        sku = soup.find('span', {'itemprop': 'model'}).text.strip()
        part_number = sku

        if soup.find('span', 'outofstock'):
            stock = 0
        else:
            stock = -1

        price_cell = soup.find('li', 'price-new')

        if not price_cell:
            price_cell = soup.find('li', 'product-price')
        price = Decimal(remove_words(price_cell.string.split('$')[1]))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        picture_urls = [tag['href'] for tag in soup.findAll('a', 'swipebox')]

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
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

import json
import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    remove_words


class ScGlobal(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Printer',
            'AllInOne',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'StereoSystem',
            'Monitor',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            # ['empresa/workstation/notebook.html', 'Notebook'],
            ['empresa/notebook-comercial.html', 'Notebook'],
            ['pc-y-portatiles/portatiles.html', 'Notebook'],
            ['empresa/plotters.html', 'Printer'],
            # ['impresion-e-imagen/impresoras-de-tinta.html', 'Printer'],
            ['impresion-e-imagen/impresoras-laser.html', 'Printer'],
            ['impresion-e-imagen/multifuncionales.html', 'Printer'],
            ['impresion-e-imagen/multifuncionales-laser.html', 'Printer'],
            # ['pc-y-portatiles/escritorio.html', 'AllInOne'],
            # ['audio/teclados-y-mouse.html', 'Mouse'],
            # ['audio/parlantes.html', 'StereoSystem'],
            ['monitores/monitores.html', 'Monitor'],
        ]

        session = session_with_proxy(extra_args)
        session.headers['X-Requested-With'] = 'XMLHttpRequest'

        product_urls = []
        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            subcategory_product_urls = []
            page = 1

            while True:
                category_url = 'https://www.scglobal.cl/index.php/{}?p={}' \
                               ''.format(category_path, page)
                print(category_url)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                json_data = json.loads(session.get(
                    category_url, verify=False).text)
                soup = BeautifulSoup(json_data['listing'], 'html.parser')
                product_cells = soup.findAll('li', 'item')

                if not product_cells and page == 1:
                    raise Exception('Empty category: ' + category_url)

                done = False

                for cell in product_cells:
                    product_url = cell.find('a')['href']
                    if product_url in subcategory_product_urls:
                        done = True
                        break
                    subcategory_product_urls.append(product_url)

                if done:
                    break

                page += 1

            product_urls.extend(subcategory_product_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        data = session.get(url, verify=False).text
        soup = BeautifulSoup(data, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('p', 'titulo-atributo-ficha').find('span').text.strip()

        pricing_container = soup.find('div', 'product-shop')
        price_container = pricing_container.find('span', 'regular-price')

        pn_match = re.search(r'ccs_cc_args.push\(\[\'pn\', \'(.+)\'\]\);',
                             data)
        part_number = pn_match.groups()[0].strip() if pn_match else None

        if not price_container:
            price_container = pricing_container.find('p', 'special-price')

        price = Decimal(remove_words(price_container.find(
            'span', 'price').text))
        description = html_to_markdown(
            str(soup.find('div', 'product-description')))
        picture_urls = [tag['href'] for tag in soup.findAll('a', 'lightbox')]

        if soup.find('button', 'btn-cart') or \
                soup.findAll('p', 'tienda-disponible'):
            stock = -1
        else:
            stock = 0

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

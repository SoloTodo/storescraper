import time

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class Clie(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'Monitor',
            'Television',
            'Printer'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        category_codes = [
            ['157', 'Notebook'],        # Notebooks i3
            ['845', 'Notebook'],        # Notebooks i5
            ['849', 'Notebook'],        # Notebooks i7
            ['872', 'Notebook'],        # Notebooks Celeron
            # ['870', 'Notebook'],      # Notebooks Pentium
            ['877', 'Notebook'],        # Notebooks AMD
            ['615', 'Monitor'],         # LED Monitor
            ['613', 'Television'],      # LED Television
            ['441', 'Printer'],         # Plotters
            # ['921', 'Printer'],       # Plotters + Scanner
            # ['908', 'Printer'],       # Plotters sublimacion
            ['896', 'Printer'],         # Plotters pedestal
            ['884', 'Printer'],         # Plotters de corte
            ['114', 'Printer'],         # Impresoras Multi. Laser negro
            ['456', 'Printer'],         # Impresoras Multi. Laser color
            ['1050', 'Printer'],        # Impresoras Multi. Laser Color A3
            ['863', 'Printer'],         # Impresoras Multi. Tinta Solida
            ['80', 'Printer'],          # Impresoras Laser negro
            ['205', 'Printer'],         # Impresoras Laser color
            ['363', 'Printer'],         # Multifuncional tinta
            ['917', 'Printer'],         # Multifuncional tinta a3
            ['174', 'Printer'],         # Impresoras tinta A3
            ['31', 'Printer'],          # Impresoras tinta
            ['208', 'Printer'],         # Matriz de punto
            ['292', 'Printer'],         # Impresoras moviles
        ]

        subcategory_urls = []

        for category_code, local_category in category_codes:
            if local_category != category:
                continue

            time.sleep(1)

            category_url = 'http://www.clie.cl/?categoria=' + category_code
            print(category_url)
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            brands_table = soup.find('table', {'width': '150'})
            brand_links = brands_table.findAll('a', {'id': 'ocultar'})

            if not brand_links:
                raise Exception('Empty category: {}'.format(category_code))

            for link in brand_links:
                complete_url = 'http://www.clie.cl/' + link['href']
                subcategory_urls.append([complete_url, local_category])

        product_urls = []

        for subcategory_url, local_category in subcategory_urls:
            if local_category != category:
                continue

            page = 1

            while True:
                subcategory_page_url = subcategory_url + '&pagina=' + str(page)

                if page >= 10:
                    raise Exception('Page overflow: ' + subcategory_page_url)

                time.sleep(1)

                soup = BeautifulSoup(session.get(subcategory_page_url).text,
                                     'html.parser')

                product_cells = soup.findAll('td', {'width': '450'})

                if not product_cells:
                    break

                for product_cell in product_cells:
                    product_link = product_cell.find('a')
                    product_path = product_link['onclick'].split('\'')[1]
                    product_url = 'http://www.clie.cl/{}'.format(product_path)

                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        name = soup.findAll('td', 'texto-precio-ahorro')[1].text.strip()

        if soup.find('img', {'src': 'images/ficha/ico_sin_stock.gif'}):
            stock = 0
        else:
            stock = int(soup.find('td', 'stock-product').text.split()[0])
        sku = soup.find('td', 'sku').text.split()[-1]

        part_number = soup.findAll('td', 'texto-precio-ahorro')[2]\
            .find('td').text.split(':')[1].strip()

        container = soup.find('td', 'lowPrice')

        offer_price = container.contents[0].split('$')[1]
        offer_price = offer_price.split('IVA')[0]
        offer_price = Decimal(remove_words(offer_price))

        normal_price = container.parent.parent.find(
            'td', 'price-normal').contents[0].split('$')[1].split('IVA')[0]
        normal_price = Decimal(remove_words(normal_price))

        picture_links = soup.findAll('a', {'rel': 'lightbox[roadtrip]'})

        picture_urls = []
        for tag in picture_links:
            if not tag.find('img'):
                continue
            picture_url = tag.find('img')['src'].replace(' ', '%20')
            if picture_url == 'http://www.clie.cl/photos/':
                continue
            picture_urls.append(picture_url)

        if not picture_urls:
            picture_urls = None

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            part_number,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            part_number=part_number,
            picture_urls=picture_urls
        )

        return [p]

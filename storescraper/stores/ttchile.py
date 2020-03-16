from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class TtChile(Store):
    preferred_products_for_url_concurrency = 3

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'VideoCard',
            'Processor',
            'Monitor',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'http://www.ttchile.cl/'

        category_paths = [
            # ['subpro.php?ic=21&isc=20', 'Notebook'],  # Notebooks
            # ['catpro.php?ic=45', 'Notebook'],  # Apple
            ['catpro.php?ic=31', 'VideoCard'],  # Tarjetas de video
            ['catpro.php?ic=25', 'Processor'],  # Procesadores AMD
            ['catpro.php?ic=26', 'Processor'],  # Procesadores Intel
            ['catpro.php?ic=18', 'Monitor'],  # LCD
            ['catpro.php?ic=23', 'Motherboard'],  # MB AMD
            ['catpro.php?ic=24', 'Motherboard'],  # MB Intel
            ['subpro.php?ic=16&isc=10', 'Ram'],  # RAM DDR4
            ['subpro.php?ic=16&isc=13', 'Ram'],  # RAM Notebook
            # ['subpro.php?ic=10&isc=6', 'StorageDrive'],  # HDD Notebook
            ['subpro.php?ic=10&isc=5', 'StorageDrive'],  # HDD SATA
            ['subpro.php?ic=10&isc=7', 'SolidStateDrive'],  # SSD
            ['catpro.php?ic=12', 'PowerSupply'],  # Fuentes de poder
            ['catpro.php?ic=13', 'ComputerCase'],  # Gabinetes
            ['subpro.php?ic=28&isc=38', 'CpuCooler'],  # Cooler CPU
            ['subpro.php?ic=28&isc=87', 'CpuCooler'],  # Ref. liquida
            ['subpro.php?ic=19&isc=16', 'Mouse'],
            ['subpro.php?ic=19&isc=17', 'Keyboard'],
            ['subpro.php?ic=19&isc=18', 'KeyboardMouseCombo'],
            ['subpro.php?ic=22&isc=22', 'Headphones'],
            ['subpro.php?ic=22&isc=23', 'StereoSystem'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                category_url = base_url + category_path + '&pagina=' + \
                               str(page)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                soup = BeautifulSoup(session.get(
                    category_url, timeout=30).text, 'html.parser')

                product_description = soup.findAll(
                    'table', 'tableEdicionProductos')[1:]

                if not product_description:
                    if page == 1:
                        raise Exception('Empty category: ' + category_url)
                    break

                for table in product_description:
                    product_url = base_url + table.find('a')['href']
                    if product_url in product_urls:
                        done = True
                        break
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        soup = BeautifulSoup(session.get(
            url, timeout=30).text, 'html.parser')

        containers = soup.findAll('div', 'textOtrosPrecios')

        normal_price = Decimal(remove_words(containers[0].text))

        stock_image = containers[1].find('img')['src']

        if stock_image in ['images/imagenes/ico_normal.jpg',
                           'images/imagenes/ico_bajo.jpg']:
            stock = -1
        else:
            stock = 0

        sku = containers[2].text.strip()
        name = soup.find('div', 'textTituloProducto').text.strip()
        offer_price = Decimal(remove_words(
            soup.find('div', 'textPrecioContado').text))

        description = html_to_markdown(str(soup.find('div', 'p7TPcontent')))

        main_picture = soup.findAll(
            'table', {'id': 'table20'})[1].findAll('img')[2]['src']

        picture_paths = [main_picture]
        picture_paths.extend([tag['src'] for tag in
                              soup.findAll('img', 'Imagen')])

        picture_urls = []
        for path in picture_paths:
            picture_id = path.split('=')[-1]
            picture_url = 'http://www.ttchile.cl/images/imgproductos/' \
                          'imgImagenMarco.php?imagen=' + picture_id
            picture_urls.append(picture_url.replace(' ', '%20'))

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

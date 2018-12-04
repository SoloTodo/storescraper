from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Stylus(Store):
    SESSION_COOKIES = None

    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        category_paths = [
            ('Id_Subrubro=338', 'ExternalStorageDrive'),
            # Discos rígidos -> Externos
            ('Id_Subrubro=336', 'StorageDrive'),
            # Discos rígidos -> Internos
            ('Id_Subrubro=495', 'SolidStateDrive'),    # Discos rígidos -> SSD
            ('Id_Subrubro=611', 'SolidStateDrive'),    # Memorias -> SSD
            ('Id_Subrubro=396', 'MemoryCard'),    # Memorias -> Micro SD Card
            # ('Id_Subrubro=298', 'MemoryCard'),    # Memorias -> SD Card
            ('Id_Rubro=2', 'UsbFlashDrive'),    # Pen Drives
        ]

        product_urls = []

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 0

            while True:
                category_url = \
                    'http://www.stylus.com.ar/productos.php?{}&pag={}' \
                    ''.format(category_path, page)
                print(category_url)

                response = cls._retrieve_page(
                    session,
                    category_url,
                    extra_args)
                soup = BeautifulSoup(response.text, 'html.parser')

                products_container = soup.find('div', 'prod-lista')

                if not products_container:
                    if page == 0:
                        raise Exception('Empty category: {}'.format(
                            category_url))
                    break

                for product_cell in products_container.findAll('li'):
                    product_url = 'http://www.stylus.com.ar/' + \
                                  product_cell.find('a')['href'].replace(
                                      '&Menu=', '')
                    product_urls.append(product_url)

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        response = cls._retrieve_page(
            session,
            url,
            extra_args)
        soup = BeautifulSoup(response.text, 'html.parser')
        container = soup.find('div', 'prod-info')
        name = container.find('h1').text.strip()
        sku = container.find('input', {'name': 'Id_Producto'})['value']

        price_container = container.find('span', 'precio')

        if not price_container:
            return []

        price = Decimal(price_container.text.replace(
            'U$S ', '').replace('.', '').replace(',', '.'))

        stock = int(container.find('strong', text='Stock:').parent.find(
            'span').text)

        part_number = container.find('span', 'rojo').text.strip()
        picture_urls = ['http://www.stylus.com.ar/' +
                        soup.find('a', 'thickbox')['href']]

        return [Product(
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
        )]

    @classmethod
    def _retrieve_page(cls, session, url, extra_args, refresh=False):
        cookies = cls._session_cookies(session, extra_args, refresh)
        response = session.get(url, cookies=cookies, timeout=30)

        if 'compra.php' not in response.text:
            if refresh:
                raise Exception('Invalid username / password')
            else:
                return cls._retrieve_page(session, url, extra_args,
                                          refresh=True)
        else:
            return response

    @classmethod
    def _session_cookies(cls, session, extra_args, refresh=True):
        if not cls.SESSION_COOKIES or refresh:
            login_payload = 'action=send&Email={}&Password={}'.format(
                extra_args['username'], extra_args['password'])

            session.post(
                'http://www.stylus.com.ar/login.php',
                login_payload,
                timeout=30)

            cls.SESSION_COOKIES = session.cookies.get_dict()

        return cls.SESSION_COOKIES

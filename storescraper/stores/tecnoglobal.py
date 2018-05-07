import urllib

from bs4 import BeautifulSoup
from decimal import Decimal
from selenium import webdriver

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, check_ean13, PhantomJS


class Tecnoglobal(Store):
    SESSION_COOKIES = None

    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'ExternalStorageDrive',
            'UsbFlashDrive',
            'MemoryCard',
            'StorageDrive',
            'SolidStateDrive',
            'Printer',
            'VideoCard',
            'Motherboard',
            'Processor',
            'CpuCooler'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        category_paths = [
            ('bu_familia=40&bu_subfam=45', 'Notebook'),
            ('bu_familia=220&bu_subfam=20', 'ExternalStorageDrive'),
            ('bu_familia=220&bu_subfam=80', 'StorageDrive'),
            ('bu_familia=100&bu_subfam=320', 'UsbFlashDrive'),
            ('bu_familia=100&bu_subfam=300', 'MemoryCard'),
            ('bu_familia=20&bu_subfam=22', 'Printer'),  # Laser
            ('bu_familia=20&bu_subfam=143', 'Printer'),  # Multifuncionales
            ('bu_familia=20&bu_subfam=21', 'Printer'),  # Inkjet
            ('bu_familia=100&bu_subfam=220', 'VideoCard'),  # Tarjetas de video
            ('bu_familia=100&bu_subfam=180', 'Motherboard'),  # Placas madre
            # ('bu_familia=100&bu_subfam=20', 'Processor'),  # Procesadores
        ]

        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            base_url = 'http://www.tecnoglobal.cl/default.asp?command=' \
                       'pa_buscar&command2=bu_categorias&bu_stock=1&{0}' \
                       ''.format(category_path)

            page = 1

            while True:
                category_url = '{}&bu_pagina={}'.format(base_url, page)

                print(category_url)

                if page >= 10:
                    raise Exception('Page overflow: ' + category_url)

                cookies = cls._retrieve_page(session, extra_args)
                response = session.get(category_url, cookies=cookies)
                soup = BeautifulSoup(response.text, 'html.parser')

                containers = soup.findAll('td', {
                    'title': 'Codigo TecnoGlobal'})[1:]

                if not containers:
                    if page == 1:
                        raise Exception('Empty category: {} - {}'.format(
                            local_category, category_path))
                    else:
                        break

                for container in containers:
                    cod_tg = container.text.strip()
                    product_url = 'http://www.tecnoglobal.cl/default.asp' \
                                  '?command=pa_catalogo&command2=ca_ficha&' \
                                  'ca_codigo_item={}'.format(cod_tg)

                    product_urls.append(product_url)
                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        cookies = cls._retrieve_page(session, extra_args)

        query = urllib.parse.urlparse(url).query

        response = session.post(
            'http://www.tecnoglobal.cl/default.asp',
            data=query,
            cookies=cookies)

        soup = BeautifulSoup(response.text, 'html.parser')

        has_offer_price = soup.find('img', {'src': '../../img/params/'
                                                   'listado/ofertas.gif'})
        specs = soup.findAll('td', 'celdatitulonegro')

        name = specs[1].text.strip()
        sku = specs[2].text.strip()
        part_number = specs[3].text.strip()
        ean = specs[4].text.strip()

        if len(ean) == 12:
            ean = '0' + ean

        if not check_ean13(ean):
            ean = None

        currency = specs[5].text.split('$')[0]

        if currency == 'CL':
            currency = 'CLP'
        else:
            currency = 'USD'

        if has_offer_price:
            offer_price = Decimal(specs[6].text.split('$')[1].replace(
                ',', '').replace('&nbsp;', ''))
            normal_price = Decimal(specs[5].text.split('$')[1].replace(
                ',', ''))
            stock = int(specs[8].text.replace(',', ''))
        else:
            normal_price = Decimal(specs[5].text.split('$')[1].replace(
                ',', ''))
            offer_price = normal_price
            stock = int(specs[6].text.replace(',', ''))

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
            currency,
            sku=sku,
            ean=ean,
            part_number=part_number
        )

        return [p]

    @classmethod
    def _retrieve_page(cls, session, extra_args, refresh=False):
        cookies = cls._session_cookies(extra_args, refresh)
        response = session.get(
            'http://www.tecnoglobal.cl/default.asp', cookies=cookies)
        soup = BeautifulSoup(response.text, 'html.parser')

        if soup.find('input', {'name': 'lo_usuario'}):
            if refresh:
                raise Exception('Invalid username / password')
            else:
                return cls._retrieve_page(session, extra_args,
                                          refresh=True)
        else:
            return cookies

    @classmethod
    def _session_cookies(cls, extra_args, refresh=True):
        if not cls.SESSION_COOKIES or refresh:
            with PhantomJS() as driver:
                driver.get('http://www.tecnoglobal.cl/')

                driver.find_element_by_name('lo_usuario').send_keys(
                    extra_args['username'])
                driver.find_element_by_name('lo_passwd').send_keys(
                    extra_args['password'])

                driver.execute_script('login()')

                cookies = {}
                for cookie_entry in driver.get_cookies():
                    cookies[cookie_entry['name']] = cookie_entry['value']

                cls.SESSION_COOKIES = cookies

        return cls.SESSION_COOKIES

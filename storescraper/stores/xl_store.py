import time

from bs4 import BeautifulSoup
from decimal import Decimal

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, \
    StaleElementReferenceException

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import PhantomJS


class XlStore(Store):
    SESSION_COOKIES = None

    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'SolidStateDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['Almacenamiento/Subcategoria/Disco%20Duro',
             'ExternalStorageDrive'],
            ['Almacenamiento/Subcategoria/USB', 'UsbFlashDrive'],
            ['Almacenamiento/Subcategoria/Flash%20Card%20-%20SD',
             'MemoryCard'],
        ]

        discovery_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            discovery_url = 'https://xlstore.exel.com.mx/Productos/' \
                            'Categoria/' + category_path
            discovery_urls.append(discovery_url)

        return discovery_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        with PhantomJS() as driver:
            driver.get('https://xlstore.exel.com.mx/Acceso')

            driver.find_element_by_id(
                'MainContent_txtUsuario').send_keys(
                extra_args['username'])
            driver.find_element_by_id(
                'MainContent_txtPassword').send_keys(
                extra_args['password'])
            driver.find_element_by_id(
                'MainContent_btnAceptar').click()

            driver.get(url)

            products = []
            next_page = 1

            while True:
                if next_page >= 20:
                    raise Exception('Page overflow: ' + url)

                soup = BeautifulSoup(driver.page_source, 'html.parser')
                products_table = soup.find(
                    'table', {'id': 'MainContent_gvProductos'}).find('tbody')

                for product_row in products_table.findAll(
                        'tr', recursive=False)[1:]:
                    container = product_row.find('div', 'div-mostrar-detalle')
                    part_number = container['codigo']
                    picture_urls = [container['imagen']]
                    name = container['descripcion']
                    product_url = product_row.find('a')['href'].split('?')[0]
                    sku = product_url.split('/')[-1]
                    stock = int(container['existencia_nacional'])
                    price = Decimal(container['precio'].replace(
                        '$', '').replace(',', ''))

                    product = Product(
                        name,
                        cls.__name__,
                        category,
                        product_url,
                        url,
                        sku,
                        stock,
                        price,
                        price,
                        'MXN',
                        picture_urls=picture_urls,
                        sku=sku,
                        part_number=part_number
                    )

                    products.append(product)

                next_page += 1

                try:
                    next_page_link = driver.find_element_by_id(
                        'MainContent_lnkPagina{}'.format(next_page))
                    next_page_link.click()

                    page_change_waits = 20

                    while True:
                        time.sleep(1)
                        try:
                            next_page_link.text
                            page_change_waits -= 1
                            if not page_change_waits:
                                raise Exception('Page change wait exceeded')

                        except StaleElementReferenceException:
                            break
                except NoSuchElementException:
                    break

        return products

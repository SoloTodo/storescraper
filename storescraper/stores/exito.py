from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown, HeadlessChrome


class Exito(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 3

    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'StorageDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.exito.com'

        url_extensions = [
            ['Tecnologia-Celulares_y_accesorios-Accesorios_para_celular-'
             'Almacenamiento/_/N-2fzn', 'MemoryCard'],
            ['Tecnologia-Computadores-_impresoras_y_tablets-'
             'Accesorios_de_computador-Memorias/_/N-2gbg',
             'ExternalStorageDrive'],
        ]

        product_urls = []

        with HeadlessChrome() as driver:
            driver.get(base_url)

            for url_extension, local_category in url_extensions:
                if local_category != category:
                    continue

                catalog_url = base_url + '/browse/' + url_extension + \
                    '?No=0&Nrpp=80'
                print(catalog_url)
                driver.get(catalog_url)
                base_soup = BeautifulSoup(driver.page_source, 'html.parser')

                link_containers = base_soup.findAll('div', 'product')

                for link_container in link_containers:
                    url = base_url + link_container.find('a')['href']
                    url = url.replace('?nocity', '')
                    product_urls.append(url)

            return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        with HeadlessChrome() as driver:
            driver.get('https://www.exito.com/')
            driver.get(url)
            soup = BeautifulSoup(driver.page_source, 'html5lib')

            part_number = soup.find(
                'div', 'reference').text.replace(
                'REF:', '').strip()[:49]

            name = soup.find('h1', 'name').text.strip()
            sku = soup.find('div', 'product')['id'][3:]

            description = ''
            for panel in soup.findAll('div', 'tabs-pdp')[:-1]:
                description += html_to_markdown(str(panel)) + '\n\n'

            picture_urls = [tag['data-src'] for tag in soup.find(
                'div', {'id': 'slide-image-pdp'}).findAll('img')]

            price_container = soup.find('div', 'col-data').find(
                'span', 'money')
            if price_container:
                price = Decimal(price_container.text.replace(',', ''))
                stock = -1
            else:
                stock = 0
                price = Decimal(0)

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
                'COP',
                sku=sku,
                part_number=part_number,
                description=description,
                picture_urls=picture_urls
            )

            return [p]

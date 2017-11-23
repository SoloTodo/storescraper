from bs4 import BeautifulSoup
from decimal import Decimal
from selenium import webdriver

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import html_to_markdown


class Exito(Store):
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

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
        if category != 'MemoryCard':
            return []

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(chrome_options=options)
        base_url = 'https://www.exito.com'

        brand_paths = [
            'KINGSTON/_/N-1z13381',
            'SANDISK/_/N-1z12rza',
            'TOSHIBA/_/N-1z13cqe',
            'WESTERN_DIGITAL/_/N-1z12ruu',
            'SEAGATE/_/N-1z12qc2',
        ]

        product_urls = []

        print(base_url)
        driver.get(base_url)

        for brand_path in brand_paths:
            category_url = base_url + '/' + brand_path + '?No=0&Nrpp=80'
            print(category_url)
            driver.get(category_url)
            base_soup = BeautifulSoup(driver.page_source, 'html.parser')

            link_containers = base_soup.findAll('div', 'product')

            if not link_containers:
                raise Exception('Empty category: ' + category_url)

            for link_container in link_containers:
                if link_container.find('div', 'available'):
                    continue
                product_url = base_url + link_container.find('a')['href']
                product_url = product_url.replace('?nocity', '')
                product_urls.append(product_url)

        driver.close()

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(chrome_options=options)
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        part_number = soup.find(
            'div', 'reference').text.replace(
            'REF:', '').strip()

        name = soup.find('h1', 'name').text.strip()
        sku = soup.find('button', 'btn-add-cart')['data-prd'].strip()

        description = ''
        for panel in soup.findAll('div', 'tabs-pdp')[:-1]:
            description += html_to_markdown(str(panel)) + '\n\n'

        picture_urls = [tag['data-src'] for tag in soup.find(
            'div', {'id': 'slide-image-pdp'}).findAll('img')]

        price_container = soup.find('span', 'money')
        if price_container:
            price = Decimal(price_container.text)
            stock = -1
        else:
            stock = 0
            price = Decimal(0)

        driver.close()

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

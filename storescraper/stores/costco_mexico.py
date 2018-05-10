import re

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class CostcoMexico(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.costco.com.mx'

        category_paths = [
            ['negocios-y-papeleria/accesorios-de-escritorio/'
             'unidades-de-almacenamiento', 'MemoryCard'],
            ['electronica-y-computo/computacion/discos-duros-y-memorias',
             'ExternalStorageDrive'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            url_webpage = '{}/view/c/{}'.format(base_url, category_path)

            page_source = session.get(url_webpage).text
            page_source = re.sub(r'(<!--\[if.[\s|\S]*<!\[endif\]-->)', '',
                                 page_source)

            soup = BeautifulSoup(page_source, 'html.parser')

            link_containers = soup.findAll('div', 'productList_item')

            for link_container in link_containers:
                product_url = base_url + link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        page_source = session.get(url).text
        page_source = re.sub(r'(<!--\[if.[\s|\S]*<!\[endif\]-->)', '',
                             page_source)

        soup = BeautifulSoup(page_source, 'html.parser')

        part_number = soup.find(
            'div', 'productDescriptionText').text.split(':')[-1].strip()

        if not part_number:
            part_number = None

        name = soup.find('h1', 'txtlrg').text.strip()
        sku = soup.find('input', {'name': 'productCode'})['value'].strip()

        price_container = soup.find('div', 'productdetail_inclprice')

        if price_container:
            price_container = price_container.find('span', 'txtlrg')
        else:
            price_container = soup.find('div', 'productdetail_exclprice')
            price_container = price_container.findAll('span', 'right')[-1]

        price = Decimal(price_container.text.replace(',', '').replace('$', ''))

        description = html_to_markdown(
            str(soup.find('div', {'id': 'productDetailInfo'})))

        picture_containers = soup.findAll('li', 'ql_product_thumbnail')
        picture_urls = ['https://www.costco.com.mx' + tag.find('a')['href']
                        for tag in picture_containers]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            -1,
            price,
            price,
            'MXN',
            sku=sku,
            part_number=part_number,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

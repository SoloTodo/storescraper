from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Hiraoka(Store):
    @classmethod
    def categories(cls):
        return [
            'Notebook',
            'UsbFlashDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_base = 'http://www.hiraoka.com.pe/'

        category_paths = [
            # ['029', 'Notebook'],      # Notebooks
            # ['031', 'Notebook'],      # Convertibles
            ['123', 'UsbFlashDrive'],
        ]

        session = session_with_proxy(extra_args)
        product_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            category_url = '{}productlist.php?ss={}'.format(
                url_base, category_path)
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            p_paragraphs = soup.findAll('div', 'proditem')

            for p in p_paragraphs:
                product_url = url_base + p.find('a')['href']
                product_url = product_url.split('&n')[0]

                product_urls.append(product_url)
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)

        soup = BeautifulSoup(session.get(url).content, 'html.parser')

        brand = soup.findAll('div', 'vpmodelo')[0].contents[1]
        model = soup.findAll('div', 'vpmodelo')[1].contents[1]
        sku = soup.findAll('div', 'vpmodelo')[2].contents[1]
        stock = int(soup.findAll('div', 'vpmodelo')[-1].find('b').text)

        name = '{} {}'.format(brand, model)

        description = html_to_markdown(
            str(soup.find('div', {'id': 'contarea'})))

        picture_urls = ['http://www.hiraoka.com.pe/' + tag['data-image']
                        for tag in soup.find(
                'div', {'id': 'gallery_01'}).findAll('a')]

        price_container = soup.findAll('span', 'precio')[1]
        price = Decimal(price_container.text.split('/.')[1].replace(',', ''))

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
            'PEN',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

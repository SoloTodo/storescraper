import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown, \
    check_ean13


class Ibyte(Store):
    @classmethod
    def categories(cls):
        return [
            'StorageDrive',
            'ExternalStorageDrive',
            'MemoryCard',
            'UsbFlashDrive',
            'SolidStateDrive',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['hardware/armazenamento/hds-e-ssds.html', 'StorageDrive'],
            ['hardware/armazenamento/pen-drive.html', 'UsbFlashDrive'],
            ['hardware/armazenamento/cartao-de-memoria.html', 'MemoryCard'],
            ['tablets/acessorios/cartao-microsd.html', 'MemoryCard'],
            ['pc-s-e-notebooks/acessorios/cartao-de-memoria.html',
             'MemoryCard'],
        ]

        product_urls = []
        session = session_with_proxy(extra_args)

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            page = 1
            local_product_urls = []

            while True:
                category_url = 'http://www.ibyte.com.br/{}?limit=60&p={}' \
                               ''.format(category_path, page)

                soup = BeautifulSoup(session.get(category_url).text,
                                     'html.parser')

                containers = soup.findAll('li', 'item')

                if not containers:
                    raise Exception('Empty category: ' + category_url)

                done = False

                for container in containers:
                    product_url = container.find('a')['href']
                    if product_url in local_product_urls:
                        done = True
                        break
                    local_product_urls.append(product_url)

                if done:
                    break

                page += 1

            product_urls.extend(local_product_urls)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('meta', {'itemprop': 'name'})['content'].strip()
        sku = re.search(r'(\d+)', soup.find(
            'span', 'view-sku').text).groups()[0]

        ean_container = soup.find('th', text='EAN')

        if ean_container:
            ean = ean_container.parent.find('td', 'data').text.strip()
            if len(ean) == 12:
                ean = '0' + ean
            if not check_ean13(ean):
                ean = None
        else:
            ean = None

        description_ids = ['descricao', 'atributos']

        description = ''

        for description_id in description_ids:
            panel = soup.find('div', {'id': description_id})
            description += html_to_markdown(str(panel) + '\n\n')

        picture_urls = [tag['href'] for tag in
                        soup.findAll('a', 'cloud-zoom-gallery')]

        normal_price = Decimal(soup.find('meta', {
            'itemprop': 'price'})['content'])

        availability = soup.find('button', 'btn-cart')

        if not availability:
            stock = 0
            offer_price = normal_price
        else:
            stock = -1

            offer_price_text = soup.find('span', 'priceAvista')
            offer_price_text = offer_price_text.find('span').text.replace(
                'R$', '').replace('.', '').replace(',', '.')
            offer_price = Decimal(offer_price_text)

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
            'BRL',
            sku=sku,
            ean=ean,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

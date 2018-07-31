import re
from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class SpDigital(Store):
    @classmethod
    def categories(cls):
        return [
            'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Tablet',
            'Notebook',
            'StereoSystem',
            'OpticalDiskPlayer',
            'PowerSupply',
            'ComputerCase',
            'Motherboard',
            'Processor',
            'VideoCard',
            'CpuCooler',
            'Printer',
            'Ram',
            'Monitor',
            'MemoryCard',
            'Mouse',
            'Cell',
            'UsbFlashDrive',
            'Television',
            'Camera',
            'Projector',
            'AllInOne',
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        session = session_with_proxy(extra_args)

        url_extensions = [
            ['351', 'ExternalStorageDrive'],
            ['348', 'ExternalStorageDrive'],
            ['352', 'StorageDrive'],
            ['350', 'SolidStateDrive'],
            ['475', 'Tablet'],
            ['369', 'Tablet'],
            ['365', 'Notebook'],
            ['474', 'Notebook'],
            ['556', 'Notebook'],
            # ['362', 'StereoSystem'],
            # ['359', 'OpticalDiskPlayer'],
            ['376', 'PowerSupply'],
            ['375', 'ComputerCase'],
            ['377', 'Motherboard'],
            ['378', 'Processor'],
            ['379', 'VideoCard'],
            ['484', 'CpuCooler'],
            ['396', 'Printer'],
            ['398', 'Printer'],
            ['394', 'Printer'],
            ['409', 'Ram'],
            ['410', 'Ram'],
            ['415', 'Monitor'],
            ['411', 'MemoryCard'],
            ['341', 'Mouse'],
            ['459', 'Cell'],
            ['412', 'UsbFlashDrive'],
            ['417', 'Television'],
            ['387', 'Camera'],
            ['416', 'Projector'],
            ['370', 'AllInOne'],
            ['342', 'Keyboard'],
            ['339', 'KeyboardMouseCombo'],
            ['337', 'Headphones'],
        ]

        product_urls = []
        for category_id, local_category in url_extensions:
            if local_category != category:
                continue

            p = 1

            local_product_urls = []

            while True:
                if p >= 50:
                    raise Exception('Page overflow for: {}'.format(
                        category_id))

                url = 'https://www.spdigital.cl/categories/view/{}/page:' \
                      '{}?o=withstock'.format(category_id, p)
                print(url)
                soup = BeautifulSoup(session.get(url).text, 'html5lib')

                product_containers = soup.findAll('div', 'product-item-mosaic')

                if not product_containers:
                    if p == 1:
                        raise Exception('Empty category: {}'.format(
                            category_id))
                    else:
                        break

                done = False

                for container in product_containers:
                    product_url = 'https://www.spdigital.cl' + \
                           container.find('a')['href']
                    if product_url in local_product_urls:
                        done = True
                        break

                    product_urls.append(product_url)
                    local_product_urls.append(product_url)

                if done:
                    break

                p += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        part_number = soup.find('span', {'id': '_sku'})

        if not part_number:
            return []

        if soup.find('span', 'product-view-price-a-pedido'):
            return []

        part_number = part_number.text.strip()

        name = soup.find('h1').text.strip()
        sku = [x for x in url.split('/') if x][-1]

        if soup.find('a', 'stock-amount-cero'):
            stock = 0
        else:
            stock_text = soup.find('div', 'product-view-stock').find(
                'span').text
            stock_overflow, stock_value = re.match(r'(.*?)(\d+) UNIDADES',
                                                   stock_text).groups()

            if stock_overflow:
                stock = -1
            else:
                stock = int(stock_value)

        containers = soup.findAll('span', 'product-view-cash-price-value')

        offer_price = Decimal(remove_words(containers[0].text))
        normal_price = Decimal(remove_words(containers[1].text))

        tabs = [
            soup.find('div', 'product-description-tab'),
            soup.find('div', {'data-tab': 'specifications'})
        ]

        description = ''

        for tab in tabs:
            if not tab:
                continue
            description += html_to_markdown(
                str(tab), 'https://www.spdigital.cl') + '\n\n'

        picture_containers = soup.findAll('a', {'rel': 'lightbox'})

        picture_urls = []
        for container in picture_containers:
            picture_url = container.find('img')['src'].replace(' ', '%20')
            if 'http' not in picture_url:
                picture_url = 'https://www.spdigital.cl' + picture_url
            picture_urls.append(picture_url)

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
            part_number=part_number,
            description=description,
            cell_plan_name=None,
            cell_monthly_payment=None,
            picture_urls=picture_urls
        )

        return [p]

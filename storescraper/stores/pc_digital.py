from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import CPU_COOLER
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class PcDigital(Store):
    @classmethod
    def categories(cls):
        return [
            # 'ExternalStorageDrive',
            'StorageDrive',
            'SolidStateDrive',
            'Motherboard',
            'Processor',
            CPU_COOLER,
            'Ram',
            'VideoCard',
            'PowerSupply',
            'ComputerCase',
            'Mouse',
            'Keyboard',
            'KeyboardMouseCombo',
            'Monitor',
            'Tablet',
            'Notebook',
            # 'Printer',
            'Cell',
            'Television',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['hardware/almacenamiento?filter=480&', 'StorageDrive'],
            ['hardware/almacenamiento?filter=481&', 'SolidStateDrive'],
            ['hardware/tarjetas-madre?', 'Motherboard'],
            ['hardware/procesadores?', 'Processor'],
            ['hardware/enfriamiento?filter=1023%2C1186&', CPU_COOLER],
            ['hardware/memorias-ram?', 'Ram'],
            ['hardware/tarjetas-de-video?', 'VideoCard'],
            ['hardware/energia?filter=993&', 'PowerSupply'],
            ['hardware/gabinetes?', 'ComputerCase'],
            ['hardware/teclados-y-mouse?filter=25&', 'Mouse'],
            ['hardware/teclados-y-mouse?filter=24&', 'Keyboard'],
            ['hardware/teclados-y-mouse?filter=23&', 'KeyboardMouseCombo'],
            ['electronica/monitores-y-televisores?filter=41%2C33%2C36&',
             'Monitor'],
            ['gadgets/tablets?', 'Tablet'],
            ['index.php?route=product/category&path=60_175&', 'Cell'],
            ['electronica/televisores?', 'Television']
        ]

        base_url = 'https://www.pcdigital.com.mx/{}'
        product_urls = []
        session = session_with_proxy(extra_args)

        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            page = 1

            while True:
                url = base_url.format(url_extension) + 'page={}'.format(page)

                if page >= 15:
                    raise Exception('Page overflow', url)

                soup = BeautifulSoup(session.get(url).text, 'html.parser')
                product_containers = soup.findAll('div', 'product')

                if not product_containers:
                    if page == 1:
                        raise Exception('Empty category: ' + url)
                    break

                for product in product_containers:
                    product_urls.append(product.find('a')['href'])

                page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)

        response = session.get(url)

        if response.status_code == 404:
            return []

        page_source = response.text
        soup = BeautifulSoup(page_source, 'html.parser')

        name = soup.find('h1', {'id': 'title-page'}).text.strip()
        sku = soup.find('input', {'id': 'hiddenModel'})['value']

        price = Decimal(
            soup.find('span', 'price-new').contents[1]
                .replace('$', '').replace(',', ''))

        images = soup.find('div', 'owl-carousel').findAll('div', 'item')
        picture_urls = []

        for image in images:
            if not image.find('a')['href']:
                continue
            picture_urls.append(image.find('a')['href'])

        description = html_to_markdown(
            str(soup.find('div', {'id': 'tab-description'})))

        stock_id = soup.find('a', {'id': 'stock_tiendas'})['pid']
        stock_url = 'https://www.pcdigital.com.mx/existencias.php'

        session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        data = 'pid={}'.format(stock_id)
        stock_source = session.post(stock_url, data=data).text
        stock_soup = BeautifulSoup(stock_source, 'html.parser')

        table_trs = stock_soup.findAll('tr')[1:]
        stock = 0

        for tr in table_trs:
            stock += int(tr.findAll('td')[1].text)

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
            'MXN',
            sku=sku,
            picture_urls=picture_urls,
            description=description,
        )

        return [p]

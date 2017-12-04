from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class AllTec(Store):
    preferred_products_for_url_concurrency = 3

    @classmethod
    def categories(cls):
        return [
            'VideoCard',
            'Processor',
            'Monitor',
            'Motherboard',
            'Ram',
            'StorageDrive',
            'SolidStateDrive',
            'PowerSupply',
            'ComputerCase',
            'CpuCooler',
            'Mouse',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'http://www.alltec.cl/'

        category_urls = [
            ['16-gabinetes', 'ComputerCase'],
            ['55-tarjetas-de-video', 'VideoCard'],
            ['17-placas-madre', 'Motherboard'],
            ['20-procesadores', 'Processor'],
            ['24-mouse', 'Mouse'],
            ['43-impresoras', 'Printer'],

        ]

        url_extensions = [
            ['33-mecanicos-rigidos', 'StorageDrive'],
            ['34-ssd', 'SolidStateDrive'],
            ['36-ddr3', 'Ram'],
            ['37-ddr4', 'Ram'],
            ['27-monitores', 'Monitor'],
            ['93-cpu-cooler', 'CpuCooler'],
            ['92-water-cooling', 'CpuCooler'],
            ['80-potencia-realcertificadas', 'PowerSupply'],
        ]

        session = session_with_proxy(extra_args)
        for category_path, local_category in category_urls:
            if local_category != category:
                continue

            category_url = base_url + category_path
            soup = BeautifulSoup(session.get(category_url).text, 'html.parser')

            subcategory_containers = soup.findAll('div', 'subcategory-image')

            if not subcategory_containers:
                raise Exception('Empty category: ' + category_url)

            for container in subcategory_containers:
                subcategory_url = \
                    container.find('a')['href'].replace(base_url, '')
                url_extensions.append((subcategory_url, category))

        product_urls = []

        for subcategory_path, local_category in url_extensions:
            if local_category != category:
                continue

            subcategory_url = '{}{}?n=1000'.format(base_url, subcategory_path)
            soup = BeautifulSoup(session.get(subcategory_url).text,
                                 'html.parser')
            link_containers = soup.findAll('div', 'product-container')

            if not link_containers:
                raise Exception('Empty subcategory: ' + subcategory_url)

            for link_container in link_containers:
                product_url = link_container.find('a')['href']
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('input', {'name': 'id_product'})['value'].strip()

        part_number = None
        part_number_container = soup.find('span', {'itemprop': 'sku'})
        if part_number_container.text:
            part_number = part_number_container['content'].strip()

        condition = soup.find('link',
                              {'itemprop': 'itemCondition'})['href'].strip()

        description = html_to_markdown(str(soup.find(
            'section', 'page-product-box')))

        add_to_card_button = soup.find('p', {'id': 'add_to_cart'})
        stock = -1
        try:
            if 'unvisible' in add_to_card_button.parent['class']:
                stock = 0
        except KeyError:
            pass

        offer_price_string = soup.find(
            'span', {'id': 'our_price_display'}).text
        offer_price = Decimal(remove_words(offer_price_string))

        normal_price_string = soup.find(
            'span', {'id': 'unit_price_display'})

        if normal_price_string:
            normal_price = Decimal(remove_words(normal_price_string.text))
        else:
            normal_price = offer_price

        picture_urls = [link['href'] for link in
                        soup.find('ul', {'id': 'thumbs_list_frame'}).findAll(
                            'a')]

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
            condition=condition,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

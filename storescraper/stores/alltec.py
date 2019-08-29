import demjson
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
            'Keyboard',
            'KeyboardMouseCombo',
            'Headphones',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        base_url = 'https://www.alltec.cl/'

        category_urls = [
            ['16-gabinetes', 'ComputerCase'],
            ['18-fuentes-de-poder', 'PowerSupply'],
            ['17-placas-madre', 'Motherboard'],
            ['20-procesadores', 'Processor'],
            ['19-memorias', 'Ram'],
            ['24-mouse', 'Mouse'],
            ['43-impresoras', 'Printer'],
            ['55-tarjetas-de-video', 'VideoCard'],
            ['23-teclados', 'Keyboard'],
            ['62-gamer', 'Keyboard'],
        ]

        url_extensions = [
            ['33-mecanicos-rigidos', 'StorageDrive'],
            ['34-ssd', 'SolidStateDrive'],
            ['27-monitores', 'Monitor'],
            ['93-cpu-cooler', 'CpuCooler'],
            ['92-water-cooling', 'CpuCooler'],
            ['25-auriculares', 'Headphones'],
            ['26-parlantes', 'StereoSystem'],
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

            page = 1

            while True:
                subcategory_url = '{}{}?p={}'.format(
                    base_url, subcategory_path, page)
                print(subcategory_url)
                response = session.get(subcategory_url)

                if response.url != subcategory_url:
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                link_containers = soup.findAll('div', 'product-container')

                if not link_containers and page == 1:
                    break

                for link_container in link_containers:
                    product_url = link_container.find('a')['href']
                    product_urls.append(product_url)

                page += 1

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
                              {'itemprop': 'itemCondition'})

        if condition:
            condition = condition['href'].strip()
        else:
            condition = 'https://schema.org/NewCondition'

        description = '{}\n\n{}'.format(
            html_to_markdown(str(soup.find(
                'div', {'itemprop': 'description'}))),
            html_to_markdown(str(soup.find('section', 'page-product-box')))
        )

        add_to_card_button = soup.find('p', {'id': 'add_to_cart'})

        stock = -1
        try:
            if 'unvisible' in add_to_card_button.parent['class']:
                stock = 0
        except KeyError:
            pass

        if 'NOTA: ' in description:
            stock = 0

        offer_price_string = soup.find(
            'span', {'id': 'our_price_display'}).text
        offer_price = Decimal(remove_words(offer_price_string))

        normal_price_string = soup.find(
            'span', {'id': 'unit_price_display'})

        if normal_price_string:
            normal_price = Decimal(remove_words(normal_price_string.text))
        else:
            normal_price = offer_price

        if offer_price > normal_price:
            offer_price = normal_price

        picture_urls = [soup.find('img', {'itemprop': 'image'})['src']]

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

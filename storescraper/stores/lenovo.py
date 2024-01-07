import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import MONITOR, NOTEBOOK, TABLET, ALL_IN_ONE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Lenovo(Store):
    base_domain = 'https://www.lenovo.com'
    currency = 'USD'
    region_extension = ''

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            MONITOR,
            ALL_IN_ONE,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []
        product_urls.extend(cls._discover_urls_for_category_old(category,
                                                                extra_args))
        product_urls.extend(cls._discover_urls_for_category_new(category,
                                                                extra_args))
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'
        response = session.get(url)

        if response.url != url:
            return []

        soup = BeautifulSoup(response.text, 'html5lib')

        if soup.find('div', {'id': 'product-details-variant-notavailable'}):
            return []

        gallery_tag = soup.find('div', 'gallery-image-slider')

        if gallery_tag:
            picture_urls = ['https://www.lenovo.com' + tag['src']
                            for tag in gallery_tag.findAll('img')]
        else:
            picture_urls = ['https://www.lenovo.com' +
                            soup.find('meta', {'name': 'thumbnail'}
                                      )['content']]

        model_containers = soup.findAll(
            'li', 'tabbedBrowse-productListing-container')
        products = []

        if soup.find('div', 'singleModelView'):
            # Notebook, Tablet or AIO without variants
            name = soup.find('h2', 'tabbedBrowse-title singleModelTitle')\
                .text.strip()
            if soup.find('div', 'partNumber'):
                sku = soup.find('div', 'partNumber').text \
                    .replace('Modelo:', '').strip()
            else:
                sku = soup.find('meta', {'name': 'bundleid'})['content']

            price_tag = soup.find('meta', {'name': 'productsaleprice'})

            if not price_tag:
                price_tag = soup.find('meta', {'name': 'productprice'})

            if not price_tag:
                price = Decimal(remove_words(
                    soup.find('dd',
                              'saleprice pricingSummary-details-final-price')
                    .text.split(',')[0]))
            else:
                price = Decimal(remove_words(price_tag['content']
                                             .split(',')[0]))

            description = html_to_markdown(str(soup.find(
                'div', 'configuratorItem-accordion-content')))

            stock_msg = soup.find('span', 'stock_message').text

            if 'agotado' in stock_msg.lower():
                stock = 0
            else:
                stock = -1

            p = Product(
                '{} ({})'.format(name, sku),
                cls.__name__,
                category,
                url,
                url,
                sku,
                stock,
                price,
                price,
                'CLP',
                sku=sku,
                part_number=sku,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)
        elif model_containers:
            # Notebook with variants
            products = []

            for model_container in model_containers:
                name = model_container.find(
                    'h3', 'tabbedBrowse-productListing-title'
                ).contents[0].strip()
                sku = model_container['data-code']
                price_tag = model_container.find(
                    'dd', 'pricingSummary-details-final-price')
                if not price_tag:
                    price_tag = model_container.find(
                        'dd', 'webPriceValue')
                if not price_tag:
                    price_tag = model_container.find(
                        'span', 'bundleDetail_youBundlePrice_value')
                price = Decimal(remove_words(price_tag.text))
                description = html_to_markdown(str(model_container.find(
                    'div', 'tabbedBrowse-productListing-featureList')))

                p = Product(
                    '{} ({})'.format(name, sku),
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    -1,
                    price,
                    price,
                    cls.currency,
                    sku=sku,
                    part_number=sku,
                    description=description,
                    picture_urls=picture_urls
                )
                products.append(p)
        else:
            # Case for https://www.lenovo.com/cl/es/laptops/ideapad/
            # serie-flex/IdeaPad-Flex-5-15ITL-05/p/88IPF501454

            name_tag = soup.find('div', 'titleSection')
            if not name_tag:
                return []

            # Monitor most likely

            name = name_tag.text.strip()
            sku = soup.find('meta', {'name': 'productid'})['content']

            sale_price = soup.find('meta', {'name': 'productsaleprice'})
            if sale_price:
                price = Decimal(remove_words(sale_price['content']))
            else:
                price = Decimal(remove_words(
                    soup.find('meta', {'name': 'productprice'})['content']))
            description = html_to_markdown(
                str(soup.find('ul', 'tabs-content-items')))

            p = Product(
                '{} ({})'.format(name, sku),
                cls.__name__,
                category,
                url,
                url,
                sku,
                -1,
                price,
                price,
                cls.currency,
                sku=sku,
                part_number=sku,
                description=description,
                picture_urls=picture_urls
            )
            products.append(p)

        return products

    @classmethod
    def _discover_urls_for_category_new(cls, category, extra_args=None):
        category_paths = [
            ('LAPTOPS', NOTEBOOK),
            ('TABLETS', TABLET),
            ('DESKTOPS', ALL_IN_ONE),
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.68.0'

        products_urls = []
        sorters = ['price-asc', 'price-desc', 'selling-desc', '']

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            for sorter in sorters:
                nb_path = \
                    cls.base_domain + cls.region_extension + \
                    '/api/product/graph?categories={}' \
                    '&sort={}&src=splitter&page='.format(
                        category_path, sorter)
                page = 0

                while True:
                    if page >= 10:
                        raise Exception('Page overflow')

                    url = nb_path + str(page)
                    print(url)
                    response = session.get(url)

                    data = json.loads(response.text)

                    if not data['results']:
                        break

                    for product_entry in data['results']:
                        product_url = cls.base_domain + \
                            cls.region_extension + \
                            product_entry['url']
                        if product_url not in products_urls:
                            products_urls.append(product_url)

                    page += 1

        return products_urls

    @classmethod
    def _discover_urls_for_category_old(cls, category, extra_args=None):
        category_paths = [
            ('Monitors', MONITOR),
        ]

        sorters = ['sortBy', 'price-asc', 'price-desc', 'selling-desc']

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.68.0'
        session.headers['Content-Type'] = 'application/json'

        products_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            for sorter in sorters:
                nb_path = cls.base_domain + cls.region_extension + \
                    '/search/facet/query/v3?categoryCode={}' \
                    '&categories=ACCESSORY&pageSize=20' \
                    '&sort={}&page='.format(category_path, sorter)
                page = 0

                while True:
                    if page >= 10:
                        raise Exception('Page overflow')

                    url = nb_path + str(page)
                    print(url)
                    response = session.get(url)

                    if response.status_code == 500:
                        break

                    data = json.loads(response.text)

                    if 'results' not in data:
                        break

                    for product_entry in data['results']:
                        product_url = cls.base_domain + \
                            cls.region_extension + \
                            product_entry['url']
                        if product_url not in products_urls:
                            products_urls.append(product_url)

                    page += 1

        return products_urls

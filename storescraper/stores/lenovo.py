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
        response = session.get(url,  allow_redirects=False)
        if response.status_code == 301:
            return []

        soup = BeautifulSoup(response.text, 'html5lib')
        models_containers = soup.findAll('div', 'tabbedBrowse-productListing')
        products = []

        if models_containers:
            for model_container in models_containers:
                name = model_container\
                    .find('h3', 'tabbedBrowse-productListing-title')\
                    .contents[0].strip()
                if model_container.find('div', 'partNumber'):
                    sku = model_container.find('div', 'partNumber').text\
                        .replace('Modelo:', '').strip()
                else:
                    sku = soup.find('meta', {'name': 'bundleid'})['content']

                price_tag = model_container\
                    .find('dd', 'pricingSummary-details-final-price')

                if price_tag:
                    price = price_tag.text\
                        .replace('.', '').replace('$', '').replace(',', '.')
                else:
                    price = model_container.find(
                        'span', 'bundleDetail_youBundlePrice_value').text \
                        .replace('.', '').replace('$', '').replace(',', '.')

                price = Decimal(price)

                description = html_to_markdown(str(
                    model_container
                    .find('div', 'tabbedBrowse-productListing-featureList')))

                picture_urls = ['https://www.lenovo.com' +
                                soup.find('img', 'subSeries-Hero')['src']]

                stock_msg = model_container.find('span', 'stock_message').text

                if stock_msg == 'Agotado':
                    stock = 0
                else:
                    stock = -1

                products.append(Product(
                    '{} ({})'.format(name, sku),
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    stock,
                    price,
                    price,
                    cls.currency,
                    sku=sku,
                    part_number=sku,
                    description=description,
                    picture_urls=picture_urls
                ))
        elif soup.find('div', 'singleModelView'):
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

            picture_urls = ['https://www.lenovo.com' +
                            soup.find('img', 'subSeries-Hero')['src']]

            stock_msg = soup.find('span', 'stock_message').text
            stock = -1

            if stock_msg == 'Agotado':
                stock = 0

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
        else:
            name_tag = soup.find('div', 'titleSection')

            if not name_tag:
                return []

            name = name_tag.text.strip()
            sku = soup.find('input', {'name': 'productCode'})['value'].strip()
            price_tag = soup.find('meta', {'name': 'productsaleprice'})

            if not price_tag:
                price_tag = soup.find('meta', {'name': 'productprice'})

            price = Decimal(remove_words(price_tag['content']))
            description = html_to_markdown(str(soup.find(
                'div', 'tabbed-browse-content-wrapper')))

            picture_urls = [
                'https://www.lenovo.com' +
                soup.find('meta', {'name': 'thumbnail'})['content']
            ]

            stock_tag = soup.find('span', 'stock_message')

            if stock_tag and stock_tag.text.strip() == 'Agotado':
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
                    cls.base_domain + '/api/product/graph?src=splitter&' \
                                      'categories={}&currency={}&sort={}' \
                                      '&page='.format(category_path,
                                                      cls.currency, sorter)
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

                    if not data['results']:
                        break

                    for product_entry in data['results']:
                        product_url = cls.base_domain + product_entry['url']
                        if product_url not in products_urls:
                            products_urls.append(product_url)

                    page += 1

        return products_urls

    @classmethod
    def _discover_urls_for_category_old(cls, category, extra_args=None):
        # Yes, each category has its own required parameters
        category_paths = [
            ('ch=-926260695&categoryCode=Monitors&categories=ACCESSORY&'
             'pageSize=20&sort={}&currency=CLP&cmsFacets=facet_Price,'
             'facet_Type,facet_ScreenSize,facet_PanelType,facet_Group,'
             'facet_Resolution',
             MONITOR),
        ]

        sorters = ['sortBy', 'price-asc', 'price-desc', 'selling-desc']

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = 'curl/7.68.0'
        session.headers['Accept'] = 'text/html,application/xhtml+xml,' \
                                    'application/xml;q=0.9,image/avif,' \
                                    'image/webp,image/apng,*/*;q=0.8,' \
                                    'application/signed-exchange;v=b3;q=0.9'

        products_urls = []

        for category_path, local_category in category_paths:
            if local_category != category:
                continue

            for sorter in sorters:
                nb_path = cls.base_domain + '/search/facet/query/v3?' + \
                          category_path.format(sorter) + \
                          '&page={}'
                page = 0

                while True:
                    if page >= 10:
                        raise Exception('Page overflow')

                    url = nb_path.format(page)
                    print(url)
                    response = session.get(url)

                    if response.status_code == 500:
                        break

                    data = json.loads(response.text)

                    if 'results' not in data:
                        break

                    for product_entry in data['results']:
                        product_url = cls.base_domain + product_entry['url']
                        if product_url not in products_urls:
                            products_urls.append(product_url)

                    page += 1

        return products_urls

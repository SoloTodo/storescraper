from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Lenovo(Store):
    base_domain = 'https://www.lenovo.com'

    @classmethod
    def categories(cls):
        return [
            'Notebook'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        nb_path = cls.base_domain + "laptops/c/LAPTOPS/" \
                  "asyncProductListPage?q=%3Aprice-asc&page={}"

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/62.0.3202.62 Safari/537.36'

        products_urls = []

        if category != 'Notebook':
            return []

        page = 0

        while True:
            url = nb_path.format(page)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_containers = soup.findAll('div', 'facetedResults-item')

            if not product_containers:
                break

            for container in product_containers:
                product_url = 'https://www.lenovo.com{}'\
                    .format(container.find('a')['href'])
                products_urls.append(product_url)

            page += 1

        return products_urls

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
        soup = BeautifulSoup(response.text, 'html.parser')

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

                price = model_container\
                    .find('dd', 'pricingSummary-details-final-price').text\
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
                    'CLP',
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

        return products

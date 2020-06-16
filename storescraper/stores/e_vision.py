from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.store import Store
from storescraper.product import Product
from storescraper.utils import session_with_proxy, html_to_markdown


class EVision(Store):
    @classmethod
    def categories(cls):
        return [
            'Television',
            'StereoSystem',
            'Cell',
            'AirConditioner',
            'Refrigerator',
            'WashingMachine',
            'Oven',
            'Stove',
            'Monitor'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('410', 'Television'),
            ('321', 'StereoSystem'),
            ('340', 'StereoSystem'),
            ('810', 'Cell'),
            ('911', 'AirConditioner'),
            ('912', 'AirConditioner'),
            # "Para empezar la decada", contains other categories too
            ('1400', 'AirConditioner'),
            # ('913', 'AirConditioner'),
            ('921', 'Refrigerator'),
            ('922', 'Refrigerator'),
            ('923', 'Refrigerator'),
            ('931', 'WashingMachine'),
            ('932', 'WashingMachine'),
            ('933', 'WashingMachine'),
            ('934', 'WashingMachine'),
            ('935', 'WashingMachine'),
            ('970', 'Oven'),
            # ('980', 'Oven'),
            ('990', 'Oven'),
            ('950', 'Stove'),
            ('620', 'Monitor'),
        ]

        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        product_urls = []

        for section_id, local_category in category_filters:
            if local_category != category:
                continue

            url = 'https://www.evisionstore.com/?ipp=All' \
                  '&categoria=catalogo&codfamilia={}'.format(section_id)

            soup = BeautifulSoup(session.get(url, timeout=30).text,
                                 'html.parser')

            product_containers = soup.findAll('div', 'product-items')

            if not product_containers:
                raise Exception('Empty section {}'.format(section_id))

            for container in product_containers:
                if 'LG' not in container.find('h4').text.upper():
                    continue
                product_url = 'https://www.evisionstore.com/{}'\
                    .format(container.find('a')['href'])
                product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['User-Agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, ' \
            'like Gecko) Chrome/66.0.3359.117 Safari/537.36'
        response = session.get(url, timeout=30)

        soup = BeautifulSoup(response.text, 'html5lib')

        if not soup.find('section', 'product-details'):
            return []

        name = soup.find('meta', {'itemprop': 'name'})['content']
        sku = soup.find('input', {'id': 'productId'})['value']

        if soup.find('a', {'id': 'addtocart'}):
            stock = -1
        else:
            stock = 0

        price = Decimal(
            soup.find('meta', {'property': 'product:price:amount'})['content']
                .replace('$', '').replace(',', '').strip())

        picture_urls = [soup.find('meta', {'itemprop': 'image'})['content']]

        description = html_to_markdown(
            str(soup.find('div', 'pro-description')))

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
            'USD',
            sku=sku,
            picture_urls=picture_urls,
            description=description
        )

        return [p]

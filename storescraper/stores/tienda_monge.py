from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class TiendaMonge(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Television',
            'OpticalDiskPlayer',
            'AirConditioner',
            'Stove',
            'Oven',
            'WashingMachine',
            'Refrigerator',
            'StereoSystem',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('125', 'Cell'),
            ('162', 'Television'),
            ('171', 'OpticalDiskPlayer'),
            ('112', 'AirConditioner'),
            ('127', 'Stove'),
            ('138', 'Oven'),
            ('146', 'WashingMachine'),
            ('170', 'Refrigerator'),
            ('152', 'StereoSystem'),
            ('163', 'StereoSystem'),
            ('174', 'StereoSystem')
        ]

        post_data = {'manufacturerId': '0',
                     'vendorId': '0',
                     'orderby': 0,
                     'pagesize': '24',
                     'queryString': '',
                     'shouldNotStartFromFirstPage': 'true',
                     'keyword': '',
                     'searchCategoryId': '0',
                     'searchManufacturerId': '0',
                     'searchVendorId': '0',
                     'priceFrom': '',
                     'priceTo': '',
                     'includeSubcategories': 'False',
                     'searchInProductDescriptions': 'False',
                     'advancedSearch': 'False',
                     'isOnSearchPage': 'False'}

        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        product_urls = []

        for category_id, local_category in category_filters:
            if local_category != category:
                continue

            page_number = 1
            post_data['categoryId'] = category_id
            url = 'https://www.tiendamonge.com/getFilteredProducts'

            while True:
                if page_number >= 20:
                    raise Exception('Page overflow')

                post_data['pageNumber'] = page_number
                result = session.post(url, data=post_data)
                soup = BeautifulSoup(result.text, 'html.parser')
                items = soup.findAll('div', 'item-box')
                for item in items:
                    if item.find('button', 'product-box-add-to-cart-button'):
                        product_url = 'https://www.tiendamonge.com{}'\
                            .format(item.find('a')['href'])
                        product_urls.append(product_url)
                if not items:
                    if page_number == 1:
                        raise Exception('Empty Category')
                    break
                page_number += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        session.headers['user-agent'] = \
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 ' \
            '(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36'
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        name = soup.find('h1', {'itemprop': 'name'}).text.strip()
        sku = soup.find('span', {'itemprop': 'sku'}).text.strip()

        if soup.find('button', 'add-to-cart-button'):
            stock = -1
        else:
            stock = 0

        price = Decimal(soup.find('span', {'itemprop': 'price'}).text
                        .replace('₡', '').replace(',', '').strip())

        pictures = soup.findAll('div', 'picture-thumb')
        picture_urls = []

        for picture in pictures:
            picture_url = picture.find('a')['data-full-image-url']
            picture_urls.append(picture_url)

        if not pictures:
            picture_url = soup.find('a', 'picture-link')['data-full-image-url']
            picture_urls = [picture_url]

        description = html_to_markdown(
            str(soup.find('div', {'id': 'quickTab-specifications'}))
        )

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
            'CRC',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

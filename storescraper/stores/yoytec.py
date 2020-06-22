from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown


class Yoytec(Store):
    @classmethod
    def categories(cls):
        return [
            'Cell',
            'Monitor',
            'Projector',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_filters = [
            ('monitores-proyectores-monitores-lcd-c-212_27_49.html',
             'Monitor'),
            ('monitores-proyectores-proyectores-c-212_27_113.html',
             'Projector'),
            ('celulares-tablets-celulares-smartphones-c-198_166.html',
             'Cell')
        ]

        session = session_with_proxy(extra_args)
        product_urls = []
        lg_product_urls = []

        for category_path, local_category in category_filters:
            if local_category != category:
                continue

            page = 1
            done = False

            while not done:
                if page >= 10:
                    raise Exception('Page overflow')

                url = 'https://www.yoytec.com/{}?page={}'\
                    .format(category_path, page)
                response = session.get(url)
                soup = BeautifulSoup(response.text, 'html5lib')
                container = soup.find('div', {'id':  'tabs-2'})
                items = container.findAll('div', 'product_block')

                for item in items:
                    product_url = item.find('a', 'product_img')['href']

                    if product_url in product_urls:
                        done = True
                        break

                    product_urls.append(product_url)
                    if item.find(
                            'div', 'manufacturer_logo').find('img')['src'] == \
                            'images/manufacturers_lg-01.gif':
                        lg_product_urls.append(product_url)

                page += 1

        return lg_product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html5lib')

        name = soup.find('h1', 'name').text.strip()
        info_table = soup.find('div', 'listing')
        rows = info_table.findAll('tr')

        sku = rows[0].find('td', 'td_right').text.strip()

        stock = 0

        for i in range(0, len(rows)-1):
            left_text = rows[i].find('td', 'td_left').text
            if 'Cantidad' not in left_text:
                continue
            right_text = rows[i].find('td', 'td_right').text
            if '+' in right_text:
                stock = -1
                break
            if 'Agotado' not in right_text:
                stock += int(right_text)

        price = Decimal(rows[-1].find('td', 'td_right').text.split('$')[-1]
                        .replace(',', ''))

        description = html_to_markdown(str(soup.find('div', 'description')))

        image_containers = soup.findAll('li', 'wrapper_pic_div')
        picture_urls = []

        for image in image_containers:
            picture_url = image.find('a')['href'].replace(' ', '%20')
            picture_urls.append(picture_url)

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
            description=description,
            picture_urls=picture_urls
        )

        return [p]

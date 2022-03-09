from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, html_to_markdown
from storescraper.categories import CELL, MONITOR, PROJECTOR


class Yoytec(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != MONITOR:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page = 1
        done = False

        while not done:
            if page >= 10:
                raise Exception('Page overflow')

            url = 'https://www.yoytec.com/lg-m-32.html?page={}'.format(page)
            response = session.get(url)
            soup = BeautifulSoup(response.text, 'html5lib')
            container = soup.find('div', {'id':  'tabs-2'})
            items = container.findAll('div', 'product_block')

            for item in items:
                product_url = item.find(
                    'a', 'product_img')['href'].split('?')[0]

                if product_url in product_urls:
                    done = True
                    break

                product_urls.append(product_url)

            page += 1

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)

        if response.status_code == 404:
            return []

        soup = BeautifulSoup(response.text, 'html5lib')

        name = soup.find('h1', 'name').text.strip()
        sku = soup.find('div', 'listing').find('td', 'td_right').text.strip()
        stock_cells = soup.find('div', 'listing').findAll(
            'table')[1].findAll('td', 'td_right')[1::2]

        stock = 0

        for stock_cell in stock_cells:
            if 'Agotado' in stock_cell.text:
                continue

            if stock_cell.text == '10+':
                stock = -1
                break

            stock += int(stock_cell.text.split()[0])

        price = Decimal(soup.find('span', 'productSpecialPrice').text
                        .replace(',', '').replace('$', ''))
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

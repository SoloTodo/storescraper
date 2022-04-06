from bs4 import BeautifulSoup
from decimal import Decimal
from urllib.parse import urlparse, parse_qs
from storescraper.categories import MONITOR

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Dell(Store):
    @classmethod
    def categories(cls):
        return [
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            ['professional-monitors', MONITOR],
            ['home-monitors', MONITOR],
            ['gaming-monitors', MONITOR],
            ['ultrasharp-monitors', MONITOR],
            ['day-to-day-monitors', MONITOR],
            ['promo-monitors', MONITOR],
            ['LARGE-FORMAT', MONITOR],
        ]

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue

            url_webpage = 'https://accessories.la.dell.com/sna/sna.aspx?c=cl' \
                '&l=es&cs=cldhs1&s=dhs&~topic={}'.format(url_extension)

            product_urls.append(url_webpage)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        container = soup.findAll('span', 'para')[3]
        trs = container.findAll('tr')
        products = []
        for tr in trs:
            if tr.find('td', 'gridCell'):
                tds = tr.findAll('td', 'gridCell')
                name = tds[0].text.strip()
                p_url = tds[-1].find('a')['href']
                query = parse_qs(urlparse(p_url).query)
                if 'sku' in query:
                    sku = query['sku'][0]
                elif 'oc' in query:
                    sku = query['oc'][0]
                else:
                    continue
                sku = str(sku)
                picture_urls = [tds[0].find('img')['src']]
                price_span_sale = tds[-1].find('span', 'pricing_sale_price')
                price_span_nodiscount = tds[-1].find(
                    'span', 'pricing_retail_nodiscount_price')
                if price_span_sale:
                    price = Decimal(price_span_sale.text.replace(
                        'CLP$', '').replace('.', ''))
                elif price_span_nodiscount:
                    price = Decimal(price_span_nodiscount.text.replace(
                        'CLP$', '').replace('.', ''))
                else:
                    continue

                stock = -1

                p = Product(
                    name,
                    cls.__name__,
                    category,
                    p_url,
                    p_url,
                    sku,
                    stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls
                )
                products.append(p)
        return products

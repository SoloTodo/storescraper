import json

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.categories import MONITOR, NOTEBOOK, TABLET
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import remove_words, html_to_markdown, \
    session_with_proxy


class Lenovo(Store):
    base_domain = 'https://www.lenovo.com'

    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            TABLET,
            MONITOR,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Yes, each category has its own required parameters
        category_paths = [
            ('ch=-488288442&categories=LAPTOPS&pageSize=20&sort=price-asc&'
             'currency=CLP&cmsFacets=facet_Processor,facet_OperatingSystem,'
             'facet_Series,facet_Graphics,facet_Price,facet_ScreenSize,'
             'facet_Brand,facet_HardDriveSize,facet_Memory,facet_leadTime,'
             'facet_Category,facet_ProductType',
             NOTEBOOK),
            ('ch=-76155580&categories=TABLETS&pageSize=20&sort=price-asc&'
             'currency=CLP&cmsFacets=facet_OperatingSystem,facet_Price,'
             'facet_Color,facet_leadTime,facet_ScreenSize,facet_Software,'
             'facet_ScreenResolution,facet_HardDriveSize', TABLET),
            ('ch=-926260695&categoryCode=Monitors&categories=ACCESSORY&'
             'pageSize=20&sort=price-asc&currency=CLP&cmsFacets=facet_Price,'
             'facet_Type,facet_ScreenSize,facet_PanelType,facet_Group,'
             'facet_Resolution',
             MONITOR),
        ]

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

            nb_path = cls.base_domain + '/search/facet/query/v3?' + \
                category_path + \
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
                'CLP',
                sku=sku,
                part_number=sku,
                description=description,
                picture_urls=picture_urls
            )

            products.append(p)

        return products

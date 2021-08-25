import json
from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import NOTEBOOK, CELL, TABLET, \
    WEARABLE, HEADPHONES
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class HuaweiShop(Store):
    @classmethod
    def categories(cls):
        return [
            NOTEBOOK,
            CELL,
            TABLET,
            WEARABLE,
            HEADPHONES
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        url_extensions = [
            # Notebooks
            ['notebooks', NOTEBOOK],
            # Cells
            ['smartphones', CELL],
            # Tablets
            ['tablets', TABLET],
            # Wearables
            ['wearables', WEARABLE],
            # Headphones
            ['audio', HEADPHONES]
        ]

        session = session_with_proxy(extra_args)

        product_urls = []
        for url_extension, local_category in url_extensions:
            if local_category != category:
                continue
            url_webpage = 'https://consumer.huawei.com/cl/offer' \
                          '/{}/'.format(url_extension)

            data = session.get(url_webpage).text
            soup = BeautifulSoup(data, 'html.parser')
            product_containers = soup.findAll('div', {
                'card-wcm-mode': 'DISABLED'})

            if not product_containers:
                continue

            for container in product_containers:
                try:
                    urls_container = \
                        json.loads(container['card-instance'])['props'][
                            'configuration']['custom']['cardParameter'][
                            'editModelParameter']['specialZone'][
                            'productSets']
                    for product_url in urls_container:
                        product_urls.append(
                            'https://consumer.huawei.com' + product_url[
                                'linkUrl'])
                except Exception:
                    continue

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        product_id = soup.find('span', {'id': 'productId'}).text
        query_url = 'https://itrinity-sg.c.huawei.com/eCommerce/queryPrd' \
                    'DisplayDetailInfo?productId={}&siteCode=CL'.format(
                        product_id)
        product_json = json.loads(session.get(query_url).text)

        products_price = json.loads(session.get('https://itrinity-sg.c'
                                                '.huawei.com/eCommerce'
                                                '/queryMinPriceAndInv'
                                                '?productIds={}&siteCode'
                                                '=CL'.format(product_id)).
                                    text)['data']['minPriceAndInvList'][0][
            'minPriceByColors']
        products_id = [product_id['sbomCode'] for product_id in
                       product_json['data']['sbomList']]
        products_id = "%2C".join(products_id)
        json_stock = json.loads(session.get('https://itrinity-sg.c.huawei.'
                                            'com/eCommerce/querySkuInventory?'
                                            'skuCodes={}&siteCode=CL'.format(
                                                products_id)).text)
        products = []

        for product in product_json['data']['sbomList']:
            name = product['name']
            sku = product['sbomCode']
            stock = 0
            for product_stock in json_stock['data']['inventoryReqVOs']:
                if product_stock['skuCode'] == sku:
                    stock = product_stock['inventoryQty']
                    break
            ean = product['gbomCode']
            price_value = product['gbomAttrList'][0]['attrValue']
            price = Decimal([price['unitPrice'] for price in products_price if
                             price_value in price.values()][0])
            picture_urls = [
                'https://img01.huaweifile.com/sg/ms/cl/pms' + photo[
                    'photoPath'] + '800_800_' + photo['photoName'] for photo in
                product['groupPhotoList']]

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
                'CLP',
                sku=sku,
                picture_urls=picture_urls,
                ean=ean

            )
            products.append(p)

        return products

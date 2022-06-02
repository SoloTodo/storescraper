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
                    for product_url_container in urls_container:
                        product_url = product_url_container['linkUrl']
                        if 'https' not in product_url:
                            product_url = 'https://consumer.huawei.com' + \
                                          product_url
                        product_urls.append(product_url)
                except Exception:
                    continue

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        product_id_tag = soup.find('span', {'id': 'productId'})

        if product_id_tag:
            product_id = product_id_tag.text.strip()
        else:
            product_id_tag = soup.find('input', {'id': 'productId'})
            if product_id_tag:
                product_id = product_id_tag['value']
            else:
                return []

        if not product_id:
            return []

        query_url = 'https://itrinity-sg.c.huawei.com/eCommerce/queryPrd' \
                    'DisplayDetailInfo?productId={}&siteCode=CL'.format(
                        product_id)
        product_json = json.loads(session.get(query_url).text)
        sbom_codes = []
        for product_entry in product_json['data']['sbomList']:
            sbom_codes.append(product_entry['sbomCode'])
            for subvariant in product_entry['sbomPackageList'] or []:
                for package in subvariant['packageList']:
                    sbom_codes.append(package['sbomCode'])

        products_id = "%2C".join(sbom_codes)
        json_stock = json.loads(session.get('https://itrinity-sg.c.huawei.'
                                            'com/eCommerce/querySkuInventory?'
                                            'skuCodes={}&siteCode=CL'.format(
                                                products_id)).text)

        if 'inventoryReqVOs' not in json_stock['data']:
            return []

        stock_dict = {x['skuCode']: x['inventoryQty']
                      for x in json_stock['data']['inventoryReqVOs']}

        prices_endpoint = 'https://itrinity-sg.c.huawei.com/convert/' \
                          'querySkuDetailDispAndInv?skuCodes={}&' \
                          'groupFlag=true&siteCode=CL&loginFrom=1'.format(
                              products_id)
        prices_res = session.get(prices_endpoint).json()
        price_per_sbom = {x['skuPriceInfo']['sbomCode']:
                          Decimal(x['skuPriceInfo']['salePrice'])
                          for x in prices_res['data']['detailDispInfos']}

        products = []

        for product in product_json['data']['sbomList']:
            base_stock = stock_dict[product['sbomCode']]
            name = product['name']
            picture_urls = [
                'https://img01.huaweifile.com/sg/ms/cl/pms' + photo[
                    'photoPath'] + '800_800_' + photo['photoName'] for photo in
                product['groupPhotoList']]

            if product['sbomPackageList']:
                for subvariant in product['sbomPackageList']:
                    sku = subvariant['packageCode']
                    subvariant_name = '{} {}'.format(name, subvariant['name'])
                    packages_stock = [stock_dict[package['sbomCode']]
                                      for package in subvariant['packageList']]
                    subvariant_stock = min(packages_stock + [base_stock])
                    price = Decimal(subvariant['packageTotalPrice'])
                    p = Product(
                        subvariant_name,
                        cls.__name__,
                        category,
                        url,
                        url,
                        sku,
                        subvariant_stock,
                        price,
                        price,
                        'CLP',
                        sku=sku,
                        picture_urls=picture_urls

                    )
                    products.append(p)

            else:
                sku = product['sbomCode']
                price = price_per_sbom[sku]

                p = Product(
                    name,
                    cls.__name__,
                    category,
                    url,
                    url,
                    sku,
                    base_stock,
                    price,
                    price,
                    'CLP',
                    sku=sku,
                    picture_urls=picture_urls
                )
                products.append(p)

        return products

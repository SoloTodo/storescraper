import json
import re

import requests
from bs4 import BeautifulSoup


def main():
    stores_id = {}
    category_stores = ['MLC1051', 'MLC1648', 'MLC1144', 'MLC5726']
    for category_store in category_stores:
        url_category_store = 'https://www.mercadolibre.cl/tiendas-oficiales/' \
                             'show?category={}'.format(category_store)
        response = requests.get(url_category_store)
        # import ipdb
        soup = BeautifulSoup(response.text, 'html.parser')
        store_containers = soup.findAll('div', 'item-grid-show')
        for stores in store_containers:
            store_urls = stores.findAll('a')
            for store_url in store_urls:
                print(store_url['href'])
                store_response = requests.get(store_url['href'])
                json_container = re.search(
                    r'window.__PRELOADED_STATE__ =([\S\s]+?);\n',
                    store_response.text)
                if not json_container:
                    continue
                product_json = json.loads(json_container.groups()[0])
                if 'initialState' in product_json:
                    products_container = \
                        product_json['initialState']['results']
                    for product in products_container:
                        if product['seller_info'][
                            'official_store_verbose_text'] == 'Vendido por OZONE':
                            import ipdb
                            ipdb.set_trace()
                        if 'seller_info' in product and not \
                        product['seller_info']['id'] in stores_id:
                            stores_id[product['seller_info']['id']] = \
                                product['seller_info'][
                                    'official_store_verbose_text']


                else:
                    print("no id: " + store_url['href'])
    print(stores_id)
    with open('stores_id.json', 'w', encoding='utf-8') as fp:
        json.dump(stores_id, fp, ensure_ascii=False)


if __name__ == '__main__':
    main()

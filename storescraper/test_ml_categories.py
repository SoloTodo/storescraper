import json
import re

import requests
from bs4 import BeautifulSoup


def main():
    all_categories = {}
    category_stores = ['MLC1051','MLC1648', 'MLC1144', 'MLC5726']
    sub_categories = []
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
                # ipdb.set_trace()

                if not json_container:
                    continue
                product_json = json.loads(json_container.groups()[0])
                if 'initialState' in product_json:
                    categories_container = \
                    product_json['initialState']['sidebar'][
                        'components']

                    for container in categories_container:
                        if container['type'] == 'AVAILABLE_FILTERS':
                            filters = container['filters']
                            break
                    categories = []
                    for filter in filters:
                        if filter['id'] == 'category':
                            categories = filter['values']
                            break

                    for category in categories:
                        sub_categories.append(category['url'])
                        if category['id'] not in all_categories:
                            print(category['name'])
                            all_categories[category['id']] = category['name']
                else:
                    categories_url_container = product_json['dataLanding'][
                        'components']
                    for component in categories_url_container:
                        if component['items']:
                            for item in component['items']:
                                if 'link' not in item['data']:
                                    continue
                                link = item['data']['link']
                                if link['component'] == 'Special-normal':
                                    sub_categories.append(link['url'])

                while len(sub_categories) > 0:
                    sub_category = requests.get(sub_categories.pop())
                    json_container = re.search(
                        r'window.__PRELOADED_STATE__ =([\S\s]+?);\n',
                        sub_category.text)
                    if not json_container:
                        continue
                    product_json = json.loads(json_container.groups()[0])
                    categories_container = \
                        product_json['initialState']['sidebar'][
                            'components']
                    for container in categories_container:
                        if container['type'] == 'AVAILABLE_FILTERS':
                            filters = container['filters']
                            break
                    categories = []
                    for filter in filters:
                        if filter['id'] == 'category':
                            categories = filter['values']
                            break
                    for category in categories:
                        sub_categories.append(category['url'])
                        if category['id'] not in all_categories:
                            print(category['name'])
                            all_categories[category['id']] = category['name']
    print(all_categories)
    with open('mc_categories.json', 'w', encoding='utf-8') as fp:
        json.dump(all_categories, fp, ensure_ascii=False)


if __name__ == '__main__':
    main()

import json

import re
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy


class Easy(Store):
    @classmethod
    def categories(cls):
        return [
            'Refrigerator',
            'Television',
            'Oven',
            'VacuumCleaner',
            'WashingMachine',
            'Cell',
            'StereoSystem',
            'OpticalDiskPlayer',
            'Lamp',
            'LightTube'
            'LightProjector',
            'WaterHeater',
            'SpaceHeater',
            'AirConditioner',
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        category_paths = [
            ['frio-directo', 'Refrigerator'],
            ['no-frost', 'Refrigerator'],
            ['freezer', 'Refrigerator'],
            ['frigobar', 'Refrigerator'],
            ['side-by-side', 'Refrigerator'],
            ['hornos-electricos', 'Oven'],
            ['hornos-empotrables', 'Oven'],
            ['microondas', 'Oven'],
            ['aspiradoras', 'VacuumCleaner'],
            ['lavadoras', 'WashingMachine'],
            ['lavadora-secadora', 'WashingMachine'],
            ['secadoras', 'WashingMachine'],
            ['reproductores', 'OpticalDiskPlayer'],
            ['iluminación-led', 'Lamp'],
            ['reflectores-exterior', 'LightProjector'],
            ['calefont-gas-licuado', 'WaterHeater'],
            ['calefont-gas-natural', 'WaterHeater'],
            ['termos', 'WaterHeater'],
            ['calefactores-a-leña', 'SpaceHeater'],
            # ['estufas-infrarrojas', 'SpaceHeater'],
            ['estufas-a-gas', 'SpaceHeater'],
            ['estufas-a-parafina', 'SpaceHeater'],
            # ['chimeneas-electricas', 'SpaceHeater'],
            # ['paneles-calefactores', 'SpaceHeater'],
            # ['calefactores-a-pellet', 'SpaceHeater'],
            # ['termoventiladores', 'SpaceHeater'],
            ['estufas-electrica', 'SpaceHeater'],
            ['aire-acondicionado-y-enfriadores-de-aire', 'AirConditioner'],
            ['audio', 'StereoSystem'],
        ]

        base_prod_url = 'https://www.easy.cl/tienda/producto/{}'
        cat_url = 'https://www.easy.cl/api/cateasy/_search'
        prods_url = 'https://www.easy.cl/api//prodeasy/_search'
        product_urls = []
        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'

        for category_id, local_category in category_paths:
            if local_category != category:
                continue

            cat_data = {
                "query": {
                    "term":
                        {"seo_url.keyword": category_id}
                }
            }

            cat_response = session.post(cat_url, data=json.dumps(cat_data))
            cat_json = json.loads(cat_response.text)
            cat_hits = cat_json['hits']['hits']

            if not cat_hits:
                raise Exception('Bad cat id {}'.format(category_id))

            cat_value = cat_hits[0]['_source']['value']
            cat_field = cat_hits[0]['_source']['field'] + ".raw"

            prods_data = {
                "query": {
                    "function_score": {
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {cat_field: cat_value}},
                                    {"match_all": {}}]}}}},
                "size": 450,
                "from": 0}

            prods_response = session.post(prods_url,
                                          data=json.dumps(prods_data))
            prods_json = json.loads(prods_response.text)
            prods_hits = prods_json['hits']['hits']

            if not prods_hits:
                raise Exception('Empty section {}'.format(category_id))

            for prods_hit in prods_hits:
                product_urls.append(
                    base_prod_url.format(prods_hit['_source']['url']))

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        prod_url = 'https://www.easy.cl/api/prodeasy*/_search'
        prod_keyword = url.split('/')[-1]
        prod_data = {
            "query": {
                "bool": {
                    "minimum_should_match": 1,
                    "should": [
                        {"term": {"url.keyword": prod_keyword}},
                        {"term": {"children.url.keyword": prod_keyword}}]}}}

        session = session_with_proxy(extra_args)
        session.headers['Content-Type'] = 'application/json'

        prod_response = session.post(prod_url, data=json.dumps(prod_data))
        prod_json = json.loads(prod_response.text)
        prod_hit = prod_json['hits']['hits'][0]

        name = prod_hit['_source']['name'].strip()
        sku = prod_hit['_source']['partNumber']
        stock = prod_hit['_source']['stock']
        normal_price = Decimal(prod_hit['_source']['price_internet'])
        offer_price = prod_hit['_source']['price_tc']

        if not offer_price:
            offer_price = normal_price
        else:
            offer_price = Decimal(offer_price)

        description = '| Caracteristica | Valor | \n' \
                      '| -------------- | ----- | \n'

        for spec in prod_hit['_source']['specs_open']:
            description += '| {} | {} |\n'.format(spec['key'], spec['value'])

        images_base_url = 'https://s7d2.scene7.com/is/image/EasySA/{}?' \
                          'req=set,json&callback=s7jsonResponse'

        images_key = sku.replace('P', '')
        images_response = session.get(images_base_url.format(images_key))

        picture_urls = []

        if 's7jsonResponse' in images_response.text:
            images_json = json.loads(
                re.search(r's7jsonResponse\((.+),""\);',
                          images_response.text).groups()[0])
            picture_entries = images_json['set']['item']
            if not isinstance(picture_entries, list):
                picture_entries = [picture_entries]

            for picture_entry in picture_entries:
                if 'i'in picture_entry:
                    picture_url = 'https://s7d2.scene7.com/is/image/' \
                                  '{}?scl=1.0'.format(picture_entry['i']['n'])
                    picture_urls.append(picture_url)

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            sku,
            stock,
            normal_price,
            offer_price,
            'CLP',
            sku=sku,
            description=description,
            picture_urls=picture_urls
        )

        return [p]

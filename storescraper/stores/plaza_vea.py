from decimal import Decimal
import json
import logging

from bs4 import BeautifulSoup
from storescraper.categories import AIR_CONDITIONER, ALL_IN_ONE, CELL, \
    HEADPHONES, NOTEBOOK, OVEN, REFRIGERATOR, STEREO_SYSTEM, TELEVISION, \
    WASHING_MACHINE
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import check_ean13, html_to_markdown, \
    session_with_proxy


class PlazaVea(Store):
    @classmethod
    def categories(cls):
        return [
            TELEVISION
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        # Only returns LG products

        if category != TELEVISION:
            return []

        session = session_with_proxy(extra_args)
        product_urls = []
        page_size = 50
        page = 0
        while True:
            if page > 12:
                raise Exception('Page overflow')
            url_webpage = 'https://www.plazavea.com.pe/api/io/_v/public/' \
                'graphql/v1?workspace=master'
            payload = {
                "query": "query productSearch($fullText: String, $selected"
                "Facets: [SelectedFacetInput], $from: Int, $to: Int, $orde"
                "rBy: String) {\n    productSearch(fullText: $fullText, se"
                "lectedFacets: $selectedFacets, from: $from, to: $to, orde"
                "rBy: $orderBy, hideUnavailableItems: true, productOriginV"
                "tex:true) @context(provider: \"vtex.search-graphql\") {\n"
                "      products {\n        cacheId\n        productId\n   "
                "     categoryId\n        description\n        productName"
                "\n        properties {\n          name\n          values"
                "\n        }\n        categoryTree{\n          id\n       "
                "   name\n          href\n          hasChildren\n         "
                " children {\n            id\n            name\n          "
                "  href\n          }\n        }\n        linkText\n       "
                " brand\n        link\n        clusterHighlights {\n      "
                "    id\n          name\n        }\n        skuSpecificati"
                "ons {\n          field {\n            name\n          }\n"
                "          values {\n            name\n          }\n      "
                "  }\n        items {\n          itemId\n          name\n "
                "         nameComplete\n          complementName\n        "
                "  ean\n          referenceId {\n            Key\n        "
                "    Value\n          }\n          measurementUnit\n      "
                "    unitMultiplier\n          images {\n            cache"
                "Id\n            imageId\n            imageLabel\n        "
                "    imageTag\n            imageUrl\n            imageText"
                "\n          }\n          sellers {\n            sellerId"
                "\n            sellerName\n            addToCartLink\n    "
                "        commertialOffer {\n              discountHighligh"
                "ts {\n                name\n              }\n            "
                "  Price\n              ListPrice\n              Tax\n    "
                "          taxPercentage\n              spotPrice\n       "
                "       PriceWithoutDiscount\n              RewardValue\n "
                "             PriceValidUntil\n              AvailableQuan"
                "tity\n              giftSkuIds\n              teasers {\n"
                "                name\n                conditions {\n     "
                "             minimumQuantity\n                  parameter"
                "s {\n                    name\n                    value"
                "\n                  }\n                }\n               "
                " effects {\n                  parameters {\n             "
                "       name\n                    value\n                 "
                " }\n                }\n              }\n            }\n  "
                "        }\n          variations{\n            name\n     "
                "       values\n          }\n        }\n        productClu"
                "sters{\n          id\n          name\n        }\n        "
                "itemMetadata {\n          items {\n            id\n      "
                "      assemblyOptions {\n              name\n            "
                "  required\n            }\n          }\n        }\n      "
                "}\n      redirect\n      recordsFiltered\n      operator"
                "\n      fuzzy\n      correction {\n        misspelled\n  "
                "    }\n    }\n  }",
                "variables": {
                    "fullText": "lg",
                    "selectedFacets": [{"key": "brand", "value": "lg"}],
                    "from": page * page_size,
                    "to": (page + 1) * page_size - 1,
                    "orderBy": "OrderByScoreDESC"
                }
            }
            data = session.post(url_webpage, json=payload).json()
            product_containers = data['data']['productSearch']['products']
            if not product_containers:
                if page == 1:
                    logging.warning('Empty category')
                break
            for container in product_containers:
                link = "https://www.plazavea.com.pe/" + \
                    container['linkText'] + "/p"
                product_urls.append(link)
            page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        session = session_with_proxy(extra_args)
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        key_input = soup.find('input', {'id': '___rc-p-id'})
        if not key_input:
            return []

        categories_json = {
            'parlantes': STEREO_SYSTEM,
            'soundbar': STEREO_SYSTEM,
            'equipos de sonido': STEREO_SYSTEM,
            'laptops': NOTEBOOK,
            'celulares y smartphones': CELL,
            'all in one': ALL_IN_ONE,
            'refrigeradoras': REFRIGERATOR,
            'lavadoras': WASHING_MACHINE,
            'lavaseca': WASHING_MACHINE,
            'secadoras': WASHING_MACHINE,
            'cocinas de pie': OVEN,
            'hornos microondas': OVEN,
            'aire acondicionado': AIR_CONDITIONER,
            'audífonos': HEADPHONES,
        }

        key = key_input['value']
        product_info = session.get('https://www.plazavea.com.pe/api/catalog_'
                                   'system/pub/products/search/'
                                   '?fq=productId:' + key).json()[0]

        category_path = product_info['categories'][0].split('/')[-2].lower()
        category = categories_json.get(category_path, category)
        name = product_info['productName']
        sku = product_info['items'][0]['itemId']

        if '10178' in product_info['productClusters']:
            # Producto internacional
            stock = 0
        else:
            stock = product_info['items'][0]['sellers'][0]['commertialOffer'][
                'AvailableQuantity']

        normal_price = Decimal(str(
            product_info['items'][0]['sellers'][0]['commertialOffer'][
                'Price']))

        item_id = product_info['items'][0]['itemId']
        payload = {
            "items": [{"id": item_id, "quantity": 1, "seller": "1"}],
            "country": "PER",
        }
        offer_info = session.post('https://www.plazavea.com.pe/api/checkout/pu'
                                  'b/orderforms/simulation?sc=1', json=payload
                                  ).json()
        if offer_info['ratesAndBenefitsData']:
            teaser = offer_info['ratesAndBenefitsData']['teaser']
            if len(teaser) != 0:
                discount = teaser[0]['effects']['parameters'][-1]['value']

                list_price = Decimal(str(
                    product_info['items'][0]['sellers'][0]['commertialOffer'][
                        'ListPrice']))
                offer_price = (list_price - Decimal(discount)).quantize(0)
            else:
                offer_price = normal_price
        else:
            offer_price = normal_price

        picture_urls = [
            product_info['items'][0]['images'][0]['imageUrl'].split('?')[0]]
        if check_ean13(product_info['items'][0]['ean']):
            ean = product_info['items'][0]['ean']
        else:
            ean = None

        description = product_info.get('description', None)
        if description:
            description = html_to_markdown(description)

        part_number = product_info.get('Modelo', None)
        if part_number:
            part_number = part_number[0]

        p = Product(
            name,
            cls.__name__,
            category,
            url,
            url,
            key,
            stock,
            normal_price,
            offer_price,
            'PEN',
            sku=sku,
            picture_urls=picture_urls,
            ean=ean,
            description=description,
            part_number=part_number,
        )
        return [p]

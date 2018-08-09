import json
import urllib
from collections import OrderedDict

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Wom(Store):
    prepago_url = 'http://www.wom.cl/prepago/'
    planes_url = 'https://www.wom.cl/planes/'

    @classmethod
    def categories(cls):
        return [
            'CellPlan',
            'Cell'
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        product_urls = []

        if category == 'CellPlan':
            product_urls.extend([
                cls.prepago_url,
                cls.planes_url
            ])
        elif category == 'Cell':
            session = session_with_proxy(extra_args)
            session.headers[
                'Content-Type'] = 'application/x-www-form-urlencoded'
            equipos_url = 'http://www.wom.cl/equipos/inc/func.savedata.php'

            page = 1

            while True:
                params = {
                    'action': '1',
                    'page_number': page
                }
                data = urllib.parse.urlencode(params)
                response = session.post(equipos_url, data=data)

                json_response = json.loads(response.text)
                soup = BeautifulSoup(json_response['msg'], 'html.parser')

                cell_containers = soup.findAll('article')

                if not cell_containers:
                    if page == 1:
                        raise Exception('No cell found')
                    break

                for cell_container in cell_containers:
                    cell_url = 'http://www.wom.cl/equipos/' + \
                               cell_container.find('a')['href']
                    product_urls.append(cell_url)

                page += 1
        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        products = []
        if url == cls.prepago_url:
            # Plan Prepago
            p = Product(
                'WOM Prepago',
                cls.__name__,
                category,
                url,
                url,
                'WOM Prepago',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)

            # Plan PVP Portabilidad (compra equipo al portarse)
            p = Product(
                'WOM PVP Portabilidad',
                cls.__name__,
                category,
                url,
                url,
                'WOM PVP Portabilidad',
                -1,
                Decimal(0),
                Decimal(0),
                'CLP',
            )
            products.append(p)
        elif url == cls.planes_url:
            # Plan Postpago
            products.extend(cls._plans(url, extra_args))
        elif '/equipos/' in url:
            # Equipo postpago
            products.extend(cls._celular_postpago(url, extra_args))
        else:
            raise Exception('Invalid URL: ' + url)
        return products

    @classmethod
    def _plans(cls, url, extra_args):
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')
        products = []

        plan_prices = {
            'ver-plan-5': Decimal(9990),
            'ver-plan-15': Decimal(12990),
            'ver-plan-25': Decimal(15990),
            'ver-plan-35': Decimal(19990),
            'ver-plan-ilimitado': Decimal(25990),
            'ver-plan-55': Decimal(29990),
        }

        plan_containers = soup.findAll('article', 'box_plan')

        for container in plan_containers:
            plan_name = container['id']
            plan_price = plan_prices[container['id']]

            for suffix in ['', ' Portabilidad']:
                adjusted_plan_name = plan_name + suffix

                product = Product(
                    adjusted_plan_name,
                    cls.__name__,
                    'CellPlan',
                    url,
                    url,
                    adjusted_plan_name,
                    -1,
                    plan_price,
                    plan_price,
                    'CLP',
                )

                products.append(product)

        return products

    @classmethod
    def _celular_postpago(cls, url, extra_args):
        print(url)
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        name = soup.find('div', 'name_phone').text.replace('\n', ' ').strip()
        description = html_to_markdown(
            str(soup.find('div', 'box_detalles_tecnicos')))

        picture_urls = []
        for tag in soup.findAll('span', 'vista-minuatura'):
            image_url = 'http://www.wom.cl' + tag.find('img')['data-img']
            picture_urls.append(image_url)

        products = []

        rent_prices = OrderedDict()
        rent_prices_container = soup.find(
            'section', {'data-modal': 'plan_arriendalo'})

        for plan_container in rent_prices_container.findAll(
                'div', 'bolsa_modal'):
            plan_name = plan_container.find(
                'p', 'bolsa_modal-title').text.strip()
            plan_price = Decimal(remove_words(plan_container.findAll(
                'span', 'precio')[1].text))
            rent_prices[plan_name] = plan_price

        # Plan con número nuevo

        modalities = [
            {
                'suffix': '',
                'selector': 'plannumero'
            },
            {
                'suffix': ' Portabilidad',
                'selector': 'portate'
            }
        ]

        for modality in modalities:
            container = soup.find('div', {'data-tab': modality['selector']})
            initial_prices = container.findAll('span', 'body_precio')

            combinations = [
                {
                    'suffix': '',
                    'use_monthly_payment': False
                },
                {
                    'suffix': ' Cuotas',
                    'use_monthly_payment': True
                }
            ]

            for idx, combination in enumerate(combinations):
                initial_price = Decimal(remove_words(initial_prices[idx].text))

                for plan_name, monthly_payment in rent_prices.items():
                    if combination['use_monthly_payment']:
                        cell_monthly_payment = monthly_payment
                    else:
                        cell_monthly_payment = Decimal(0)

                    products.append(Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {}{}{}'.format(name, plan_name,
                                           modality['suffix'],
                                           combination['suffix']),
                        -1,
                        initial_price,
                        initial_price,
                        'CLP',
                        cell_plan_name='{}{}'.format(plan_name,
                                                     modality['suffix']),
                        picture_urls=picture_urls,
                        description=description,
                        cell_monthly_payment=cell_monthly_payment
                    ))

        prepago_container = soup.find('div', {'data-tab': 'equipoprepago'})
        prepago_price = Decimal(remove_words(prepago_container.find(
            'span', 'body_precio').text))

        products.append(Product(
            name,
            cls.__name__,
            'Cell',
            url,
            url,
            '{} WOM Prepago'.format(name),
            -1,
            prepago_price,
            prepago_price,
            'CLP',
            cell_plan_name='WOM Prepago',
            picture_urls=picture_urls,
            description=description,
            cell_monthly_payment=Decimal(0)
        ))

        return products

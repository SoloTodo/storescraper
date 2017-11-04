import urllib

from bs4 import BeautifulSoup
from decimal import Decimal

from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words, \
    html_to_markdown


class Wom(Store):
    prepago_url = 'http://www.wom.cl/prepago/'
    planes_url = 'http://www.wom.cl/planes/'

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
            equipos_url = 'http://www.wom.cl/equipos/include/filtro/' \
                          'filtro2.php'

            orderings = ['menor', 'mayor']

            for ordering in orderings:
                print(ordering)
                page = 1

                while True:
                    print(page)
                    params = {
                        u'busqueda': '',
                        u'orden': ordering,
                        'page': page
                    }
                    data = urllib.parse.urlencode(params)
                    response = session.post(equipos_url, data=data)
                    soup = BeautifulSoup(response.text, 'html.parser')

                    cell_links = soup.findAll('a', 'btn-fb')

                    if not cell_links:
                        break

                    for cell_link in cell_links:
                        cell_url = 'http://www.wom.cl/equipos/{0}'.format(
                            cell_link['href']
                        )
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
            'plan 5 gigas': Decimal(9990),
            'plan 15 gigas': Decimal(15990),
            'plan 25 gigas': Decimal(19990),
            'plan 35 gigas': Decimal(25990),
            'plan gigas ilimitados': Decimal(29990),
            'plan minutos 4 gigas': Decimal(9990),
            'plan minutos 10 gigas': Decimal(15990),
            'plan minutos 14 gigas': Decimal(19990),
            'plan minutos 20 gigas': Decimal(29990),
        }

        plan_containers = soup.findAll('article', 'new-plan')

        for container in plan_containers:
            plan_img = container.find('img', 'img-plan-mob')
            plan_name = plan_img['alt']

            plan_price = plan_prices[plan_name]

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
        session = session_with_proxy(extra_args)
        soup = BeautifulSoup(session.get(url).text, 'html.parser')

        try:
            cell_brand = soup.find('h2').string.strip()
            cell_model = soup.find('h1').string.strip()

            name = '{0} {1}'.format(cell_brand, cell_model)
        except AttributeError:
            name = soup.find('h2').string.strip()

        products = []

        plan_association_containers = soup.findAll(
            'div', 'info-planes-equipo')
        plan_association_containers += soup.findAll(
            'div', 'info-planes-equipo2')

        for idx, container in enumerate(plan_association_containers):
            plan_name = container.find('h3').contents[0].strip()

            if container.find('p', 'sin-port-dos'):
                # Cell

                picture_urls = ['http://www.wom.cl' + tag['src'] for tag in
                                soup.find('div', 'equipo').findAll('img')]
                description = html_to_markdown(
                    str(soup.find('ul', 'descripcion')))

                cell_monthly_payment = Decimal(remove_words(
                    container.find('strong', 'valor').text))

                portability_price = Decimal(
                    remove_words(
                        container.findAll(
                            'p', 'valor-cuota')[1].contents[1].replace(
                            '*', '')))

                portability_plan_name = plan_name + ' Portabilidad'

                product = Product(
                    name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} {}'.format(name, portability_plan_name),
                    -1,
                    portability_price,
                    portability_price,
                    'CLP',
                    cell_plan_name=portability_plan_name,
                    picture_urls=picture_urls,
                    description=description,
                    cell_monthly_payment=cell_monthly_payment
                )

                products.append(product)

                normal_price = Decimal(
                    remove_words(
                        container.find('p', 'sin-port-dos').contents[1]))

                product = Product(
                    name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} {}'.format(name, plan_name),
                    -1,
                    normal_price,
                    normal_price,
                    'CLP',
                    cell_plan_name=plan_name,
                    picture_urls=picture_urls,
                    description=description,
                    cell_monthly_payment=cell_monthly_payment
                )
                products.append(product)

                prepago_container = soup.find('span', 'm-b-40')
                if prepago_container:
                    price = Decimal(
                        remove_words(
                            prepago_container.string
                        )
                    )

                    product = Product(
                        name,
                        cls.__name__,
                        'Cell',
                        url,
                        url,
                        '{} {}'.format(name, 'WOM Prepago'),
                        -1,
                        price,
                        price,
                        'CLP',
                        cell_plan_name='WOM Prepago',
                        picture_urls=picture_urls,
                        description=description
                    )
                    products.append(product)
            else:
                # Modem
                price = Decimal(remove_words(
                    container.find('p', 'valor-cuota').text))

                cell_monthly_payment = Decimal(remove_words(
                    soup.findAll('strong', 'valor')[1::2][idx].text))

                product = Product(
                    name,
                    cls.__name__,
                    'Cell',
                    url,
                    url,
                    '{} {}'.format(name, plan_name),
                    -1,
                    price,
                    price,
                    'CLP',
                    cell_plan_name=plan_name,
                    cell_monthly_payment=cell_monthly_payment
                )
                products.append(product)

        return products

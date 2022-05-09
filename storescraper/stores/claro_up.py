from decimal import Decimal

from bs4 import BeautifulSoup

from storescraper.categories import CELL
from storescraper.product import Product
from storescraper.store import Store
from storescraper.utils import session_with_proxy, remove_words


class ClaroUp(Store):
    @classmethod
    def categories(cls):
        return [
            CELL,
        ]

    @classmethod
    def discover_urls_for_category(cls, category, extra_args=None):
        if category != CELL:
            return []

        session = session_with_proxy(extra_args)
        res = session.get('https://digital.clarochile.cl/wcm-inyect/'
                          'landing-claroup/index.php')
        soup = BeautifulSoup(res.text, 'html.parser')
        product_urls = []
        for product_box in soup.findAll('li', 'equipo_slider'):
            product_url = product_box.find('a')['href'].replace(
                '=contactar', '=ofertas')
            product_urls.append(product_url)

        return product_urls

    @classmethod
    def products_for_url(cls, url, category=None, extra_args=None):
        print(url)
        session = session_with_proxy(extra_args)
        endpoint = 'https://digital.clarochile.cl/wcm-inyect/' \
                   'landing-claroup/mas-ofertas/index.php?' + url.split('?')[1]
        res = session.get(endpoint)

        soup = BeautifulSoup(res.text, 'html.parser')
        cell_name_tag = soup.find('h4')

        if not cell_name_tag:
            return []

        cell_name = cell_name_tag.text.strip()
        plan_rows = soup.find('table', {'id': 'tabla-ofertas'}).findAll(
            'tr')[1:]
        products = []

        for plan_row in plan_rows:
            cell_plan_name = 'Claro ' + plan_row.find('td').text.strip() + \
                             ' con cuota de arriendo'
            price = Decimal(remove_words(plan_row.findAll('td')[2].text))
            cell_monthly_payment = Decimal(remove_words(plan_row.findAll(
                'td')[3].text))

            product = Product(
                cell_name,
                cls.__name__,
                'Cell',
                url,
                url,
                '{} - {}'.format(cell_name, cell_plan_name),
                -1,
                price,
                price,
                'CLP',
                cell_plan_name=cell_plan_name.upper(),
                cell_monthly_payment=cell_monthly_payment
            )
            products.append(product)

        return products

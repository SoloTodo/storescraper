from storescraper.stores.siman import Siman


class SimanElSalvador(Siman):
    country_url = 'sv'
    currency_iso = 'USD'
    category_filters = [
        ['tecnologia/pantallas', 'Television'],
        ['linea-blanca/Lavadoras', 'WashingMachine'],
        ['linea-blanca/secadoras', 'WashingMachine'],
        ['linea-blanca/cocinas-y-barbacoas', 'Oven'],
        ['linea-blanca/refrigeradoras', 'Refrigerator'],
        ['linea-blanca/aires-acondicionados', 'AirConditioner']
    ]

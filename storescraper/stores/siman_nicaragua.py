from storescraper.stores.siman import Siman


class SimanNicaragua(Siman):
    country_url = 'ni'
    currency_iso = 'USD'
    category_filters = [
        ['tecnologia/pantallas', 'Television'],
        ['linea-blanca/Lavadoras', 'WashingMachine'],
        ['linea-blanca/secadoras', 'WashingMachine'],
        ['linea-blanca/cocinas-y-barbacoas', 'Oven'],
        ['linea-blanca/refrigeradoras', 'Refrigerator'],
        ['linea-blanca/aires-acondicionados', 'AirConditioner']
    ]

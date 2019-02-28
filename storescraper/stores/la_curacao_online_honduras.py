from storescraper.stores.la_curacao_online import LaCuracaoOnline


class LaCuracaoOnlineHonduras(LaCuracaoOnline):
    country = 'honduras'
    currency = 'L'
    currency_iso = 'HNL'
    category_filters = [
        ('electronica/celulares.html', 'Cell'),
        ('audio-y-video/televisores.html', 'Television'),
        ('audio-y-video/equipos-de-sonido.html', 'StereoSystem'),
        ('hogar/aires-acondicionados.html', 'AirConditioner'),
        ('refrigeracion/refrigeradoras.html', 'Refrigerator'),
        ('refrigeracion/congeladores.html', 'Refrigerator'),
        ('lavadoras-y-secadoras/lavadoras.html', 'WashingMachine'),
        ('cocina/microondas.html', 'Oven'),
    ]

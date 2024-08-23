from storescraper.stores.la_curacao_online import LaCuracaoOnline


class LaCuracaoOnlineElSalvador(LaCuracaoOnline):
    country = "elsalvador"
    currency = "$"
    currency_iso = "USD"

    @classmethod
    def format_url(cls, page):
        return f"https://www.lacuracaonline.com/{cls.country}/search/lg?p={page}"

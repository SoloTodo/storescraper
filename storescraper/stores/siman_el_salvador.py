from storescraper.stores.siman import Siman


class SimanElSalvador(Siman):
    country_url = 'sv'
    currency_iso = 'USD'
    preferred_discover_urls_concurrency = 1
    preferred_products_for_url_concurrency = 1

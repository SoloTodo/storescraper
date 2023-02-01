from storescraper.stores.peru_stores import PeruStores


class Metro(PeruStores):
    base_url = 'https://www.metro.pe'
    params = 'ft=lg&PS=18&sl=19ccd66b-b568-43cb-a106-b52f9796f5cd&cc=18&sm=0' \
        '&O=OrderByScoreDESC'
    product_container_class = 'product-item'

    seller_id = 'metrope'
    sku_is_item_id = False

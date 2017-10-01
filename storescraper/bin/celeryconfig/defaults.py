import sys
sys.path.append('../..')

broker_url = 'amqp://storescraper:storescraper@localhost/storescraper'
result_backend = 'rpc://'

imports = (
    'storescraper.store'
)

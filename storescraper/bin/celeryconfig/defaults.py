import sys
sys.path.append('../..')

broker_url = 'amqp://storescraper:storescraper@localhost/storescraper'
result_backend = 'rpc://'

imports = (
    'storescraper.store'
)

task_time_limit = 300

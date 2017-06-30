import sys
sys.path.append('../..')

enable_utc = True
timezone = 'America/Santiago'

broker_url = 'amqp://storescraper:storescraper@localhost/storescraper'
result_backend = 'rpc://'

imports = (
    'storescraper.store'
)

task_time_limit = 300

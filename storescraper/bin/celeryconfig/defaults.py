import sys

sys.path.append("../..")

broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/0"

imports = "storescraper.store"

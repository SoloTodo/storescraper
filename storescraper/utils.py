import importlib

CLP_BLACKLIST = ['CLP$', 'precio', 'internet', 'normal',
                 '$', '.', ',', '&nbsp;', '\r', '\n', '\t']


def remove_words(text, blacklist=CLP_BLACKLIST):
    for word in blacklist:
        text = text.replace(word, '')

    return text


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def get_store_class_by_name(store_class_name):
    store_module = importlib.import_module('storescraper.stores')
    return getattr(store_module, store_class_name)

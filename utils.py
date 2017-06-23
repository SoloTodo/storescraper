import importlib

CLP_BLACKLIST = ['CLP$', 'precio', 'internet', 'normal',
                 '$', '.', ',', '&nbsp;', '\r', '\n', '\t']


def remove_words(text, blacklist=CLP_BLACKLIST):
    for word in blacklist:
        text = text.replace(word, '')

    return text


def get_store_class_by_name(store_path):
    store_module, store_class_name = store_path.split('.')
    store_module = importlib.import_module(
        'stores.{}'.format(store_module))
    return getattr(store_module, store_class_name)

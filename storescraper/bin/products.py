import argparse
import json
import logging
import sys
sys.path.append('../..')

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='products.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Retrieves the products of the given store.')

    parser.add_argument('store', type=str,
                        help='The name of the store to be parsed')

    parser.add_argument('--product_types', type=str, nargs='*',
                        help='Specific product types to be parsed')

    parser.add_argument('--sync', type=bool, nargs='?', default=False,
                        const=True,
                        help='Set to force synchronous parsing '
                             '(without using celery tasks)')

    parser.add_argument('--extra_args', type=json.loads, nargs='?', default={},
                        help='Optional arguments to pass to the parser '
                             '(usually username/password) for private sites)')

    args = parser.parse_args()
    store = get_store_class_by_name(args.store)

    available_products = 0
    unavailable_products = 0

    products = store.products(
        product_types=args.product_types,
        async=not args.sync,
        extra_args=args.extra_args,
        queue='us')

    for product in products:
        if product.is_available():
            available_products += 1
        else:
            unavailable_products += 1
        print(product, '\n')

    print('Available: {}'.format(available_products))
    print('Unavailable: {}'.format(unavailable_products))
    print('Total: {}'.format(available_products + unavailable_products))

if __name__ == '__main__':
    main()

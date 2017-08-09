import argparse
import json
import logging
import sys
sys.path.append('../..')

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='discover_urls_for_product_types.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Discovers the URLs of the given store and (optional) '
                    'product types')

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

    result = store.discover_urls_for_product_types(
        product_types=args.product_types,
        use_async=not args.sync,
        extra_args=args.extra_args,
        queue='us')

    for entry in result:
        print('{0} ({1})'.format(entry['url'], entry['product_type']))
    print('Total: {0} URLs'.format(len(result)))

if __name__ == '__main__':
    main()

import argparse
import json
import logging
import sys
sys.path.append('../..')

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='discover_urls_for_categories.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Discovers the URLs of the given store and (optional) '
                    'categories')

    parser.add_argument('store', type=str,
                        help='The name of the store to be parsed')

    parser.add_argument('--category', type=str, nargs='*',
                        help='Specific categories to be parsed')

    parser.add_argument('--sync', type=bool, nargs='?', default=False,
                        const=True,
                        help='Set to force synchronous parsing '
                             '(without using celery tasks)')

    parser.add_argument('--extra_args', type=json.loads, nargs='?', default={},
                        help='Optional arguments to pass to the parser '
                             '(usually username/password) for private sites)')

    args = parser.parse_args()
    store = get_store_class_by_name(args.store)

    result = store.discover_urls_for_categories(
        categories=args.categories,
        use_async=not args.sync,
        extra_args=args.extra_args,
        queue='us')

    for entry in result:
        print('{} ({})'.format(entry['url'], entry['category']))
    print('Total: {0} URLs'.format(len(result)))

if __name__ == '__main__':
    main()

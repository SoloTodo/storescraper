import argparse
import json
import logging
import sys
sys.path.append('../..')

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='discover_urls_for_keyword.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Discovers the URLs of the given store and keyword')

    parser.add_argument('store', type=str,
                        help='The name of the store to be parsed')

    parser.add_argument('keyword', type=str, nargs='*',
                        help='Specific keyword to be searched')

    parser.add_argument('threshold', type=int,
                        help='The amount of urls to retrieve')

    parser.add_argument('--extra_args', type=json.loads, nargs='?', default={},
                        help='Optional arguments to pass to the parser '
                             '(usually username/password) for private sites)')

    args = parser.parse_args()
    store = get_store_class_by_name(args.store)
    keyword = args.keyword[0]
    threshold = args.threshold

    results = store.discover_urls_for_keyword(
        keyword, threshold,
        extra_args=args.extra_args)

    for url in results:
        print('\n{}'.format(url))

    print('Total: {} URLs'.format(len(results)))


if __name__ == '__main__':
    main()

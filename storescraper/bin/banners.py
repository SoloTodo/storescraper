import argparse
import json
import logging
import sys
sys.path.append('../..')

from storescraper.utils import get_store_class_by_name  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='banners.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Retrieves the Banners of the given store')

    parser.add_argument('store', type=str,
                        help='The name of the store to be parsed')

    parser.add_argument('--extra_args', type=json.loads, nargs='?', default={},
                        help='Optional arguments to pass to the parser '
                             '(usually username/password) for private sites)')

    args = parser.parse_args()
    store = get_store_class_by_name(args.store)

    banners = store.banners(extra_args=args.extra_args)

    if banners:
        for banner in banners:
            if "picture" in banner:
                banner.pop('picture')
            print(json.dumps(banner, indent=4), '\n')
            if len(banner.pop('picture_url', '')) > 250:
                raise Exception(
                    'Picture URLs must be less than 250 characters long')
    else:
        print('No banners found')


if __name__ == '__main__':
    main()

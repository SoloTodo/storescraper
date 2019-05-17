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
        description='Discovers the URLs of the given store and keyword')

    parser.add_argument('store', type=str,
                        help='The name of the store to be parsed')

    parser.add_argument('keyword', type=str, nargs='*',
                        help='Specific keyword to be searched')

    parser.add_argument('threshold', type=int,
                        help='The amount of urls to retrieve')

    parser.add_argument('--with_async', type=bool, nargs='?', default=False,
                        const=True,
                        help='Use async tasks (celery)')

    parser.add_argument('--extra_args', type=json.loads, nargs='?', default={},
                        help='Optional arguments to pass to the parser '
                             '(usually username/password) for private sites)')

    args = parser.parse_args()
    store = get_store_class_by_name(args.store)
    keyword = args.keyword[0]
    threshold = args.threshold

    available_products = 0
    unavailable_products = 0

    products_data = store.products_for_keyword(
        keyword, threshold,
        use_async=args.with_async,
        extra_args=args.extra_args)

    for product in products_data['products']:
        if product.is_available():
            available_products += 1
        else:
            unavailable_products += 1
        print(product, '\n')

    urls_with_error = products_data['discovery_urls_without_products']
    print('Discovery URLs without products:')
    if not urls_with_error:
        print('* No empty URLs found')
    for url_with_error in urls_with_error:
        print('* {}'.format(url_with_error))

    print()
    print('Available: {}'.format(available_products))
    print('Unavailable: {}'.format(unavailable_products))
    print('With error: {}'.format(len(urls_with_error)))
    print('Total: {}'.format(available_products + unavailable_products +
                             len(urls_with_error)))


if __name__ == '__main__':
    main()

import argparse
import json
import logging
import sys
sys.path.append('../..')

from storescraper.utils import get_store_class_by_name, HeadlessChrome  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='discover_urls_for_categories.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Generates the Cloudflare cookies for certain stores')

    parser.add_argument('proxy', type=str,
                        help='Proxy to use')

    args = parser.parse_args()
    proxy = args.proxy

    with HeadlessChrome(proxy=proxy, headless=False, images_enabled=True) \
            as driver:
        driver.get('https://simple.ripley.cl')
        input('Please complete the CAPTCHA, then press ENTER')

        cfduid_cookie = None
        cf_clearance_cookie = None

        for cookie in driver.get_cookies():
            if cookie['name'] == '__cfduid':
                cfduid_cookie = cookie['value']
            if cookie['name'] == 'cf_clearance':
                cf_clearance_cookie = cookie['value']

        assert cfduid_cookie and cf_clearance_cookie

        print('Use the following parameters as "extra args" for scraping')

        d = {
            "proxy": proxy,
            "cf_clearance": cf_clearance_cookie,
            "__cfduid": cfduid_cookie
        }
        print(json.dumps(d))


if __name__ == '__main__':
    main()

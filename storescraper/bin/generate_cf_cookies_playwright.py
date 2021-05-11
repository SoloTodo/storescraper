import argparse
import json
import logging
import time

import sys

from playwright import sync_playwright

sys.path.append('../..')

from storescraper.utils import CF_REQUEST_HEADERS  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='discover_urls_for_categories.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Generates the Cloudflare cookies for certain stores')

    parser.add_argument('--proxy_ip', type=str)
    parser.add_argument('--proxy_port', type=str)
    parser.add_argument('--proxy_username', type=str)
    parser.add_argument('--proxy_password', type=str)

    args = parser.parse_args()

    with sync_playwright() as p:
        proxy = {
            'server': 'http://{}:{}'.format(args.proxy_ip, args.proxy_port),
            'username': args.proxy_username,
            'password': args.proxy_password
        }

        print(proxy)

        browser = p.firefox.launch(proxy=proxy, headless=False)
        context = browser.newContext(
            userAgent=CF_REQUEST_HEADERS['User-Agent']
        )

        page = context.newPage()
        page.goto('https://simple.ripley.cl')

        input('Please complete the CAPTCHA, then press ENTER')

        cf_clearance_cookie = None
        cf_clearance_expiration = None

        for cookie in context.cookies():
            print(cookie['name'])
            if cookie['name'] == 'cf_clearance':
                print(cookie)
                cf_clearance_cookie = cookie['value']
                cf_clearance_expiration = cookie['expires']

        assert cf_clearance_cookie

        print('Use the following parameters as "extra args" for scraping')
        print('Cookie expires on:',
              time.strftime('%Y-%m-%d %H:%M:%S',
                            time.localtime(cf_clearance_expiration)))

        proxy_string = 'http://{}:{}@{}:{}'.format(
            args.proxy_username, args.proxy_password, args.proxy_ip,
            args.proxy_port)

        d = {
            "proxy": proxy_string,
            "cf_clearance": cf_clearance_cookie,
        }
        print(json.dumps(d))

        return d


if __name__ == '__main__':
    main()

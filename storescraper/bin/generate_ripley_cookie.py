import argparse
import json
import logging

import requests
import time

import sys
from bs4 import BeautifulSoup

sys.path.append('../..')

from storescraper.utils import HeadlessChrome, CF_REQUEST_HEADERS  # noqa


def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename='discover_urls_for_categories.log',
                        filemode='w')

    parser = argparse.ArgumentParser(
        description='Generates the Cloudflare cookie for Ripley')

    parser.add_argument('client_key', type=str,
                        help='anti-captcha.com client key')
    parser.add_argument('proxy_ip', type=str, help='Proxy IP to use')
    parser.add_argument('proxy_port', type=int, help='Proxy port to use')
    parser.add_argument('proxy_username', type=str,
                        help='Proxy username to use')
    parser.add_argument('proxy_password', type=str,
                        help='Proxy password to use')

    args = parser.parse_args()
    proxy = 'http://{}:{}@{}:{}'.format(
        args.proxy_username, args.proxy_password, args.proxy_ip,
        args.proxy_port
    )
    with HeadlessChrome(images_enabled=True, proxy=proxy, headless=True) as driver:
        driver.get('https://simple.ripley.cl')
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        hcaptcha_script_tag = soup.find('script', {'data-type': 'normal'})
        website_key = hcaptcha_script_tag['data-sitekey']

        # Anti captcha request
        request_body = {
            "clientKey": args.client_key,
            "task":
                {
                    "type": "HCaptchaTask",
                    "websiteURL": "https://simple.ripley.cl/",
                    "websiteKey": website_key,
                    "proxyType": "http",
                    "proxyAddress": args.proxy_ip,
                    "proxyPort": args.proxy_port,
                    "proxyLogin": args.proxy_username,
                    "proxyPassword": args.proxy_password,
                    "userAgent": CF_REQUEST_HEADERS['User-Agent']
                }
        }
        print('Sending anti-captcha task')
        print(json.dumps(request_body, indent=2))
        anticaptcha_session = requests.Session()
        anticaptcha_session.headers['Content-Type'] = 'application/json'
        response = json.loads(anticaptcha_session.post(
            'http://api.anti-captcha.com/createTask',
            json=request_body).text)

        print('Anti-captcha task request response')
        print(json.dumps(response, indent=2))

        assert response['errorId'] == 0

        task_id = response['taskId']
        print('TaskId', task_id)

        # Wait until the task is ready...
        get_task_result_params = {
            "clientKey": args.client_key,
            "taskId": task_id
        }
        print('Querying for anti-captcha response (wait 10 secs per retry)')
        print(json.dumps(get_task_result_params, indent=4))
        retries = 1
        hcaptcha_response = None
        while not hcaptcha_response:
            if retries > 20:
                raise Exception('Failed to get a token in time')
            print('Retry #{}'.format(retries))
            time.sleep(10)
            res = json.loads(anticaptcha_session.post(
                'https://api.anti-captcha.com/getTaskResult',
                json=get_task_result_params).text)

            assert res['errorId'] == 0, res
            assert res['status'] in ['processing', 'ready'], res
            if res['status'] == 'ready':
                print('Solution found')
                hcaptcha_response = res['solution']['gRecaptchaResponse']
                break
            retries += 1

        print(hcaptcha_response)
        for field in ['g-recaptcha-response', 'h-captcha-response']:
            driver.execute_script("document.querySelector('[name=\""
                                  "{0}\"]').remove(); "
                                  "var foo = document.createElement('input'); "
                                  "foo.setAttribute('name', "
                                  "'{0}'); "
                                  "foo.setAttribute('value','{1}'); "
                                  "document.getElementsByTagName('form')"
                                  "[0].appendChild(foo);".format(
                                    field, hcaptcha_response))
        driver.execute_script("document.getElementsByTagName('form')"
                              "[0].submit()")

        d = {
            "proxy": proxy,
            "cf_clearance": driver.get_cookie('cf_clearance')['value'],
            "__cfduid": driver.get_cookie('__cfduid')['value']
        }
        print(json.dumps(d))


if __name__ == '__main__':
    main()

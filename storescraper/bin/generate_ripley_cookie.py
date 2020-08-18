import argparse
import json
import logging

import requests
import time

import sys
from bs4 import BeautifulSoup

sys.path.append('../..')

from storescraper.utils import get_store_class_by_name, HeadlessChrome, \
    session_with_proxy, CF_REQUEST_HEADERS  # noqa


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
    parser.add_argument('proxy_username', type=str, help='Proxy username to use')
    parser.add_argument('proxy_password', type=str, help='Proxy password to use')

    args = parser.parse_args()
    proxy = 'http://{}:{}@{}:{}'.format(
        args.proxy_username, args.proxy_password, args.proxy_ip,
        args.proxy_port
    )
    ripley_session = session_with_proxy({'proxy': proxy})
    for header_name, header_value in CF_REQUEST_HEADERS.items():
        ripley_session.headers[header_name] = header_value

    response = ripley_session.get('https://simple.ripley.cl')
    soup = BeautifulSoup(response.text, 'html.parser')

    hcaptcha_script_tag = soup.find('script', {'data-type': 'normal'})
    website_key = hcaptcha_script_tag['data-sitekey']
    request_id = hcaptcha_script_tag['data-ray']

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
    while retries <= 20:
        print('Retry #{}'.format(retries))
        time.sleep(10)
        res = json.loads(anticaptcha_session.post(
            'https://api.anti-captcha.com/getTaskResult',
            json=get_task_result_params).text)

        assert res['errorId'] == 0
        assert res['status'] in ['processing', 'ready']
        if res['status'] == 'ready':
            print('Solution found')
            hcaptcha_response = res['solution']['gRecaptchaResponse']
            break
        retries += 1
    else:
        raise Exception('Failed to get a token in time')

    print(hcaptcha_response)

    # Assemble the request to get the clearance cookie
    form = soup.find('form')
    action = form['action']
    r = form.find('input', {'name': 'r'})['value']
    cf_captcha_kind = form.find('input', {'name': 'cf_captcha_kind'})['value']

    request_params = {
        'r': r,
        'cf_captcha_kind': cf_captcha_kind,
        'vc': '',
        'id': request_id,
        'g-recaptcha-response': hcaptcha_response,
        'h-captcha-response': hcaptcha_response,
    }

    print('https://simple.ripley.cl{}'.format(action))
    print(request_params)
    ripley_session.headers['Content-Type'] = 'application/x-www-form-urlencoded'
    ripley_session.headers['Accept'] = '*/*'
    ripley_session.headers['accept-encoding'] = 'gzip, deflate, br'
    ripley_session.headers['Upgrade-Insecure-Requests'] = '1'

    res = ripley_session.post('https://simple.ripley.cl{}'.format(action),
                              json=request_params)
    import ipdb
    ipdb.set_trace()
    print(res.data)




if __name__ == '__main__':
    main()

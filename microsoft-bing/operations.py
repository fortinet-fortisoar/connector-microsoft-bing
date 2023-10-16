"""
Copyright start
MIT License
Copyright (c) 2023 Fortinet Inc
Copyright end
"""

import requests, json
from .constants import *
from connectors.core.connector import get_logger, ConnectorError

logger = get_logger('microsoft-bing')


class MicrosoftBing(object):
    def __init__(self, config, *args, **kwargs):
        self.api_key = config.get('api_key')
        url = config.get('server_url').strip('/')
        if not url.startswith('https://') and not url.startswith('http://'):
            self.url = 'https://{0}/v7.0/'.format(url)
        else:
            self.url = url + '/v7.0/'
        self.verify_ssl = config.get('verify_ssl')

    def make_rest_call(self, url, method, data=None, params=None):
        try:
            url = self.url + url
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key
            }
            logger.debug("Endpoint {0}".format(url))
            response = requests.request(method, url, data=data, params=params, headers=headers, verify=self.verify_ssl)
            logger.debug("response_content {0}:{1}".format(response.status_code, response.content))
            if response.ok or response.status_code == 204:
                logger.info('Successfully got response for url {0}'.format(url))
                if 'json' in str(response.headers):
                    return response.json()
                else:
                    return response
            else:
                logger.error("{0}".format(response.status_code))
                raise ConnectorError("{0}:{1}".format(response.status_code, response.text))
        except requests.exceptions.SSLError:
            raise ConnectorError('SSL certificate validation failed')
        except requests.exceptions.ConnectTimeout:
            raise ConnectorError('The request timed out while trying to connect to the server')
        except requests.exceptions.ReadTimeout:
            raise ConnectorError(
                'The server did not send any data in the allotted amount of time')
        except requests.exceptions.ConnectionError:
            raise ConnectorError('Invalid Credentials')
        except Exception as err:
            raise ConnectorError(str(err))


def check_payload(payload):
    updated_payload = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            nested = check_payload(value)
            if len(nested.keys()) > 0:
                updated_payload[key] = nested
        elif value != '' and value is not None:
            updated_payload[key] = value
    return updated_payload


def create_multiple_values(values):
    result = []
    for value in values:
        result.append(COUNTRY_CODES.get(value))
    return ",".join(result)


def web_search(config, params):
    try:
        mb = MicrosoftBing(config)
        endpoint = 'search'
        cc = params.get('cc')
        if cc:
            cc = create_multiple_values(cc)
        payload = {
            "q": params.get('q'),
            "textFormat": "RAW",
            "answerCount": params.get('answerCount'),
            "promote": ",".join(params.get('promote')) if params.get('promote') else '',
            "cc": cc,
            "setLang": LANGUAGES.get(params.get('setLang')) if params.get('setLang') else "",
            "freshness": params.get('freshness'),
            "responseFilter": ",".join(params.get('responseFilter')) if params.get('responseFilter') else '',
            "safeSearch": params.get('safeSearch'),
            "textDecorations": params.get('textDecorations'),
            "count": params.get('count'),
            "offset": params.get('offset')
        }
        additional_fields = params.get('additional_fields')
        if additional_fields:
            payload.update(additional_fields)
        payload = check_payload(payload)
        response = mb.make_rest_call(endpoint, 'GET', params=payload)
        return response
    except Exception as err:
        raise ConnectorError(str(err))


def check_health(config):
    try:
        response = web_search(config, params={"q": "Hello Bing"})
        if response:
            return True
    except Exception as err:
        logger.info(str(err))
        raise ConnectorError(str(err))


operations = {
    'web_search': web_search
}

"""
Reference: https://developers.google.com/civic-information/docs/v2/representatives/representativeInfoByAddress
"""

import json
import urllib.request
import urllib.parse
from configparser import ConfigParser


def _get_google_civic_governer(address):
    config = ConfigParser()
    config.read('config.ini')

    # For google civic api params
    url = 'https://www.googleapis.com/civicinfo/v2/representatives?'
    KEY = config.get('main', 'google_civic_key')
    ROLES = 'headOfGovernment'

    query_strings_dict = {
        'key': KEY,
        'roles': ROLES,
        'address': address,
    }
    query_string = urllib.parse.urlencode(query_strings_dict)

    req = urllib.request.Request(
        url + query_string,
        headers={
            'User-Agent': 'Jackys Lob Test Agent',
        }
    )
    resp = urllib.request.urlopen(req)

    if resp.code == 200:
        content = urllib.request.urlopen(req).read()
        return json.loads(content.decode('utf-8'))
    else:
        raise urllib.error.HTTPError("Error from Google Civic API: Expected status code 200, but got {}".format(resp.code))


def _parse_governer_info(json):
    """ Returns a info map containing name, address, party, phones, urls, channels"""
    # Get office index
    index = -1
    for office in json['offices']:
        if office['name'] == 'Governor':
            index = office['officialIndices'][0]
            break

    # Get governer name via index from
    if index != -1:
        info = json['officials'][index]
        return info
    else:
        raise ValueError("Could not find governor info in json response")

def get_governer(address):
    """ Returns a info map containing name, address, party, phones, urls, channels """
    address = "Gardena, CA"

    json = _get_google_civic_governer(address)

    if json:
        return _parse_governer_info(json)
    else:
        print('Error using google civic api')







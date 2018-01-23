import google_civic_wrapper
import json
import lob
import urllib.error
from configparser import ConfigParser
import sys


# Setups
args = sys.argv
if len(args) > 1:                   # Get input file name from sys.argv or default to inputs.json from root folder
    INPUT_FILENAME = sys.argv[1]
else:
    INPUT_FILENAME = 'inputs.json'

# Set lob key from config file. Or use environment variables but not possible when delivering this app via zip file.
config = ConfigParser()
config.read('config.ini')
lob.api_key = config.get('main', 'lob_key')


# Helpers here can be put in separate module but keeping it here for brevity
def _is_valid(input_map):
    """ Raise errors if user inputs are not valid """
    if 'address2' not in input_map:
        raise ValueError("Missing 'address2' param from input file. Leave as empty string if not applicable.")

    for key in ['name','address1','city','state','zipcode','message']:
        if key not in input_map:
            raise ValueError("User input file must contain: 'name','address1','address2','city','state','zipcode','message'")
        if input_map[key].strip() == "":
            raise ValueError("All params must contain strings except for address2")


def _is_deliverable(input_map):
    """
    Raise errors if Lob API indicate from address is not deliverable
    I think the API key needs to be live and not a test version for non-dummy response
    """
    verification = lob.USVerification.create(
        primary_line    = input_map['address1'],
        secondary_line  = input_map['address2'],
        city            = input_map['city'],
        state           = input_map['state'],
        zip_code        = input_map['zipcode'],
    )

    if not verification.deliverability:
        raise ValueError('Lob API indicated from address is not deliverable')


def _get_from_address(filename):
    """ Returns a map of input paramters """
    input_map = json.load(open(filename))

    # Raise errors to main if not valid or deliverable
    _is_valid(input_map)
    _is_deliverable(input_map)

    return input_map


# Main driver, prints to console
def main():
    # Get input for FROM address parameters
    print("Reading user input file...")
    input_map = _get_from_address(INPUT_FILENAME)

    from_name =     input_map['name']
    from_address1 = input_map['address1']
    from_address2 = input_map['address2']
    from_city =     input_map['city']
    from_state =    input_map['state']
    from_zip =      input_map['zipcode']
    address_string = '{} {}, {} {} {}, {}'.format(from_address1, from_address2, from_city, from_state, from_zip, 'US')

    # Use google civic api to find the governer and office address based on from address.
    # Generates necessary TO address parameters
    print("Fetching Governer info from Google Civic API...")
    governor_info = google_civic_wrapper.get_governer(address_string)

    # Create letter and send via lob api
    print("Generating letter via Lob API...")
    letter = lob.Letter.create(
        description='Demo Letter',
        to_address={
            'name':             governor_info['name'],
            'address_line1':    governor_info['address'][0]['line1'].replace('c/o', '').strip(),
            'address_line2':    governor_info['address'][0]['line2'],
            'address_city':     governor_info['address'][0]['city'],
            'address_state':    governor_info['address'][0]['state'],
            'address_zip':      governor_info['address'][0]['zip'],
            'address_country': 'US'
        },
        from_address={
            'name':             from_name,
            'address_line1':    from_address1,
            'address_line2':    from_address2,
            'address_city':     from_city,
            'address_state':    from_state,
            'address_zip':      from_zip,
            'address_country':  'US'
        },
        file='<html style="padding-top: 3in; margin: .5in;">'   # Keeping it simple with embed html.
             '<p>Dear Governor {{governer}},</p>'
             '<p>{{letter_content}}</p>'
             '</html>',
        merge_variables={
            'governer'      : governor_info['name'],
            'letter_content': input_map['message']
        },
        color=False
    )

    if letter:
        print('Letter generated susccessfully')
        print('View at: {}'.format(letter.url))
    else:
        print('Failed to generate letter.')


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print("Error: Cannot find input file")
    except ValueError as e:
        print("Error from reading Input file: {}".format(e))
    except urllib.error.HTTPError as e:
        print("Error from Google Civic API: {}".format(e))
    except lob.error.AuthenticationError as e:
        print("Error from Lob API: {} - {}".format(e.http_status, e.args[0]))
    except lob.error.InvalidRequestError as e:
        print("Error from Lob API: {} - {}".format(e.http_status, e.args[0]))


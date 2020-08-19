""" Author:       hraleig@amazon.com
    Versions:     python v. 3.x

    Creates an alters objects holding test result data, used by tests.py
"""

import web_interact as wi


def key_url(key, endpoint, region):
    """Build URLs given necessary input, store in json format

        :param key: key associated with url
        :param endpoint: stack name for reusable solution
        :param region: region reusable solution was deployed in
        :return: outputs from stack as json object
    """
    url = "http://" + endpoint + "." + region + ".elasticbeanstalk.com"
    kv = {"OutputKey": key,
          "OutputValue": url}

    return kv


def new_test(tag, name):
    """Create default, empty sub-test result objects

        :param tag: tag for resource being tested
        :param name: name of sub-test
        :return: sub-test object
    """
    # init all status message to 'could not be executed' failures
    test = {'tag': tag,
            'test': name,
            'status': 'UNEXECUTED',
            'message': 'Test could not be executed',
            'extra': []
            }

    return test


def add_response(test, link, driver=None):
    """Append response information dict to extra info of test

        :param test: test object to append response info to
        :param link: url for page yielding response
        :param driver: optional driver for receiving additional response info
        :return: updated test dict
    """
    test['extra'].append(response_info(link, driver))
    return test


def set_http_sts(test, sts):
    """Set http status code

        :param test: test object to append response info to
        :param sts: http status code as String
        :return: updated test dict
    """
    test['extra'][0]['http status'] = sts
    return test


def get_sts(test):
    return test['status']


def get_tag(test):
    return test['tag']


def response_info(link, driver=None):
    """Create and populate response information dict

        :param link: url for page yielding response
        :param driver: optional driver for receiving additional response info
        :return: response information dict
    """
    page_info = pg_info(link)

    if driver is None:
        page_info['http status'] = wi.http_status('', link)
        return page_info
    else:
        page_info['title'] = driver.title
        front, back = wi.response(driver)
        page_info['http status'] = wi.http_status('', link)
        page_info['front end response time (ms)'] = front
        page_info['back end response time (ms)'] = back

    return page_info


def pg_info(link):
    """Populate page test info

        :param link: url for page being tested as String
        :return: object containing information for page being tested
    """

    page_info = {
        'tag': 'response',
        'url': link,
        'title': 'Not tested',
        'http status': '---',
        'front end response time (ms)': 'Not tested',
        'back end response time (ms)': 'Not tested'
    }

    return page_info


def success(test, msg=None):
    """Create success status and message object

        :param test: test with status to be altered
        :param msg: optional message for success reason
        :return: updated test object
    """
    if msg is None:
        msg = 'Test entirely succeeded'

    test['status'] = 'SUCCESS'
    test['message'] = msg

    return test


def fail(test, msg=None):
    """Create failure status and message object

        :param test: test with status to be altered
        :param msg: optional message for failure reason
        :return: updated test object
    """
    if msg is None:
        msg = 'Test failed'

    test['status'] = 'FAILURE'
    test['message'] = msg

    return test


def resolve_sts(test, sts_msg):
    """Resolve status and message object, populate test with success/fail accordingly

        :param test: test with status to be altered
        :param sts_msg: optional message for status reason
        :return: updated test object
    """
    if sts_msg[0] is 'FAILURE':
        return fail(test, sts_msg[1])
    elif sts_msg[0] is 'SUCCESS':
        return success(test, sts_msg[1])
    else:
        print('Script error - test status unresolved for test ' + str(test))
        exit(-1)

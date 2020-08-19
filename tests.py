""" Author:       hraleig@amazon.com
    Versions:     python v. 3.x

    Testing OHDSI-on-AWS or REDCap solution functionality. Record test info as JSON file and store in S3.
    The tests check that the webpages can be accessed, profiles can be signed into, and for OHDSI that a cohort
    can be created in ATLAS.

    usage: python3 tests.py <endpoint> <region> <username> <password> -test=<test>
"""

import argparse
import boto3
import getpass
import json
import os
import shutil
import sys
import web_interact as wi
import test_objects as tob
from botocore.exceptions import ClientError
from datetime import datetime

BUCKET = "solutions-test-output"


def test_pages(outputs, user, passw, filename):
    """Test all ohdsi web page functionality

        :param outputs: list of urls and keys as dicts for pages being tested
        :param user: username as string
        :param passw: password as string
        :param filename: name of file to store test results in
        :return: list containing all test result dicts
    """

    driver = wi.chrome_driver()

    all_tests = []

    for output in outputs:
        link = output["OutputValue"]
        key = output["OutputKey"]

        # Deployment logs unchecked
        if "Deployment" not in key:
            # attempt to connect to the page and record
            if "RStudio" in key:
                all_tests = test_page(driver, user, passw, link, all_tests, key, "//button[@type='submit']")
            elif "Jupyter" in key:
                all_tests = test_page(driver, user, passw, link, all_tests, key, "//input[@id='login_submit']")
            elif "ATLAS" in key:
                all_tests = test_page(driver, user, passw, link, all_tests, key, "ATLAS")
            else:
                all_tests.append(tob.new_test('UNKNOWN PAGE', 'N/A'))

    upload_to_s3(all_tests, filename, "odshi-on-aws/" + filename)

    driver.close()
    return all_tests


def red_test(output, user, passw, filename):
    """Test redcap web page functionality

        :param output: url and key as dict for page being tested
        :param user: username as string
        :param passw: password as string
        :param filename: name of file to store test results in
        :return: list containing all test result dicts
    """

    driver = wi.chrome_driver()

    link = output["OutputValue"]
    key = output["OutputKey"]

    all_tests = test_page(driver, user, passw, link, [], key, "//button[@id='login_btn']")
    upload_to_s3(all_tests, "red_" + filename, "redcap/" + filename)

    driver.close()
    return all_tests


def test_page(driver, user, passw, link, all_tests, key, btn_path):
    """Ensure proper, expected page is loaded for specific link and test page functionality

        :param driver: webdriver for Chrome page
        :param user: username as String
        :param passw: password as String
        :param key: keyword to search for in page title
        :param all_tests: list of all test dictionaries
        :param btn_path: xpath to submit button
        :return: populated test info object
    """

    test = tob.new_test(key, 'get page attempt')
    all_tests.append(test)
    driver.get(link)

    if key in driver.title:
        test = tob.success(test, 'Page retrieved successfully')
    else:
        test = tob.fail(test, 'Page could not be retrieved properly')

    # populate page info for test and record in overall test info
    test = tob.add_response(test, link, driver)

    all_tests.pop()
    all_tests.append(test)
    
    # test sign in upon tob.successful access to page
    if tob.get_sts(test) is 'SUCCESS':
        test = tob.new_test(key, 'sign in attempt')
        all_tests.append(test)
        all_tests = sign_in(driver, user, passw, link, btn_path, test, all_tests)

    return all_tests


def sign_in(driver, user, passw, link, btn_path, test, all_tests):
    """Test sign in for page

        :param driver: webdriver for Chrome page
        :param user: username as String
        :param passw: password as String
        :param link: url for page being tested as String
        :param test: test associated with sign in
        :param all_tests: list of all test dictionaries
        :param btn_path: xpath to submit button
        :return: populated test info object
    """

    if "ATLAS" not in btn_path:
        tag = tob.get_tag(test)
        if "Jupyter" in tag:
            tag = tag + "Lab"
        test = tob.resolve_sts(test, wi.log_in(driver, user, passw, link, btn_path, tag))
        # perform second sign in attempt if first fails
        if tob.get_sts(test) == 'FAILURE':
            test = tob.resolve_sts(test, wi.log_in(driver, user, passw, link, btn_path, tag))
        test = tob.add_response(test, link, driver)
        all_tests.pop()
        all_tests.append(test)
    else:
        all_tests = atlas_test(user, passw, link, all_tests, test)

    return all_tests


def atlas_test(user, passw, link, all_tests, test):
    """Enter username and password then submit to log in, if sign in successful test cohort creation

        :param user: username as String
        :param passw: password as String
        :param link: url for page being tested as String
        :param all_tests: list of all test dictionaries
        :param test: default sign in test object
        :return: success String if log in completed, failure description String otherwise
    """
    full_link = link + "/WebAPI/user/login/db"
    command = ("curl -c cookies.txt -v -s " + full_link + " 2>&1 -X POST -d \"rememberMe=true\" "
               "-d \"login=" + user + "\" --data-urlencode \"password=" + passw + "\"")

    sts = wi.curl_http(command)

    test = tob.add_response(test, link)
    test = tob.set_http_sts(test, sts)

    if sts != '200':
        if sts == '401':
            test = tob.fail(test, 'Incorrect username or password')
        elif sts == '403':
            test = tob.fail(test, 'Forbidden')
        else:
            test = tob.fail(test, 'Unusual failure, see HTTP status code')
    else:
        test = tob.success(test, 'Sign in complete')

    all_tests.pop()
    all_tests.append(test)
   
    cohort_test = tob.new_test('ATLAS', 'create cohort attempt')
    all_tests.append(cohort_test)

    # attempt to create cohort if sign in is successful
    if tob.get_sts(test) == 'SUCCESS':
        cohort_test = create_cohort(command, user, link, cohort_test)
        all_tests.pop()
        all_tests.append(cohort_test)

    return all_tests


def create_cohort(command, user, link, test):
    """Enter username and password then submit to log in, if sign in successful test cohort creation

        :param command: curl command to sign in to page
        :param user: username as String
        :param link: url for page being tested as String
        :param test: test dict associated with creating cohort
        :return: success String if log in completed, failure description String otherwise
    """

    filename = 'cohort.json'
    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M")

    with open(filename, 'r') as file:
        cohort = json.load(file)
        # ensure file isn't empty
        if os.path.getsize(filename) == 0:
            print("ERROR: Empty cohort definition file.. cannot create cohort")
            exit(-1)
        name = cohort['name']
        cohort['name'] = name + " " + dt_string
        cohort['createdBy'] = user
        cohort['createdDate'] = dt_string
        cohort['modifiedBy'] = user
        cohort['modifiedDate'] = dt_string

    # save backup of cohort file before removing
    backup = 'backup-' + filename
    shutil.copyfile(filename, backup)
    os.remove(filename)

    with open(filename, 'w+') as file:
        json.dump(cohort, file)

    bearer = "TOKEN=`" + command + " | grep -i bearer | cut -d ' ' -f 3` ; "
    dest = link + "/WebAPI/cohortdefinition -H \"Authorization: Bearer $TOKEN\""
    cohort_command = (bearer + "curl -v -b cookies.txt -H \"Content-Type: application/json\" -X POST -d @cohort.json " +
                      dest)
    ret = wi.curl_cmd(cohort_command)

    if name in str(ret):
        test = tob.success(test, 'Cohort created')
    else:
        test = tob.fail(test, 'Unable to create cohort')

    # include page response info
    test = tob.add_response(test, link + "/WebAPI/cohortdefinition")
    test = tob.set_http_sts(test, wi.http_status(bearer, "-b cookies.txt " + dest))

    return test


def upload_to_s3(objs, file, path):
    """Create json file to be uploaded to s3

        :param objs: dictionary of test output
        :param file: name of file to write json to
        :param path: path to object in s3 bucket
    """

    output = {'Page Access Info': objs}

    # create json file for test output info
    with open(file, "w+") as write_file:
        json.dump(output, write_file)

    upload_file(file, path)


def upload_file(file_name, object_name=None):
    """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param object_name: Object to upload
        :return: True if file was uploaded, else False
    """

    if object_name is None:
        object_name = file_name

    # Upload the file
    s3_client = boto3.client('s3')
    s3_client.upload_file(file_name, BUCKET, object_name, ExtraArgs={'ACL': 'public-read'})


def build_outputs(endpoint, region):
    """Create list of dicts for each url needed in ohdsi test

        :param endpoint: endpoint name for parent stack as String
        :param region: region for parent stack as String
        :return: list of dicts for each url
    """

    r_output = tob.key_url("RStudio", "rstudio." + endpoint, region)
    j_output = tob.key_url("Jupyter", "jupyter." + endpoint, region)
    a_output = tob.key_url("ATLAS", endpoint, region)

    return [r_output, j_output, a_output]


def parse_args():
    """Parse arguments for running test

        :return: parser for args
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("endpoint", type=str, help="endpoint name for parent stack (str)")
    parser.add_argument("region", type=str, help="region deployed in (str) [default: us-east-1]", default="us-east-1")
    parser.add_argument("user", type=str, help="username for accessing resources")
    parser.add_argument("passw", type=str, help="password for accessing resources")
    parser.add_argument("-test", type=str, help="test being performed (str) from set {\"ohdsi\", \"redcap\"} [default: "
                        "ohdsi]", default="ohdsi")

    return parser.parse_args()


def main(args):
    args = parse_args()
    filename = "test_output_" + args.region + ".json"

    # exceptions occurring during testing will be caught here before exiting
    try:
        # perform proper test specified and print output to terminal
        if args.test == "redcap":
            output = tob.key_url("REDCap", args.endpoint, args.region)
            print(red_test(output, args.user, args.passw, filename))
        elif args.test == "ohdsi":
            outputs = build_outputs(args.endpoint, args.region)
            print(test_pages(outputs, args.user, args.passw, filename))
        else:
            print("ERROR - Unknown test \"" + args.test + "\" (run with -h for help)")
            exit(-1)
    except EnvironmentError as ee:
        print("ERROR occurred creating cohort: ")
        print(ee)
        exit(-1)
    except ClientError as ce:
        print("ERROR uploading to S3: ")
        print(ce)
        exit(-1)
    except Exception as e:
        print(e)
        exit(-1)


if __name__ == "__main__":
    main(sys.argv)

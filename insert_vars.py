""" Author:       hraleig@amazon.com
    Versions:     python v. 3.x

    File used to insert variables into template files for security purposes.
"""

import argparse
import os
import sys
import yaml


def insert_creds(filename, user, passw):
    """Enter username and password then submit to log in, if sign in successful test cohort creation

            :param filename: name of yaml file to be altered
            :param user: username as String
            :param passw: password as String
    """

    try:
        with open(filename, 'r') as f:
            doc = yaml.load(f, Loader=yaml.FullLoader)

            # alter credentials for each test scenario
            scenarios = []
            for scenario in doc['tests']:
                scenarios.append(scenario)
            for i in range (0, len(scenarios)):
                doc['tests'][scenarios[i]]['parameters']['RStudioUserList'] = user + "," + passw

            # overwrite previous file
            os.remove(filename)
            with open(filename, 'w+') as f:
                yaml.dump(doc, f)
    except FileNotFoundError:
        print("File \'" + filename + "\' could not be found. Upcoming tests may fail.")
        exit(-1)


def parse_args():
    """Parse arguments for running test

        :return: parser for args
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", type=str, help="name of template file to be altered")
    parser.add_argument("user", type=str, help="username for accessing resources")
    parser.add_argument("passw", type=str, help="password for accessing resources")

    return parser.parse_args()


def main(args):
    args = parse_args()
    insert_creds(args.filename, args.user, args.passw)


if __name__ == "__main__":
    main(sys.argv)

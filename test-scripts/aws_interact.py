""" Editor:       hraleig@amazon.com
    Versions:     python v. 3.x

    Includes logic for tests to interact with AWS services, used by tests.py.
    Enables secrets manager access and uploading files to S3.
"""

import boto3
import base64
from botocore.exceptions import ClientError


def get_secret(secret_name, region_name):
    """Upload a file to an S3 bucket

        :param secret_name: name of secret to be retrieved
        :param region_name: name of region where secret is stored
        :return: secret payload
    """

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    secret = ""

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        print(str(e))
        exit(-1)
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    return secret


def upload_file(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

        :param file_name: File to upload
        :param bucket: Bucket name to upload to
        :param object_name: Object to upload
        :return: True if file was uploaded, else False
    """

    if object_name is None:
        object_name = file_name

    # Upload the file
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_name, bucket, object_name, ExtraArgs={'ACL': 'public-read'})
    except ClientError as e:
        print(str(e))
        exit(-1)

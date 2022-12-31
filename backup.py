#!/usr/bin/python

import boto3
import os
import requests
import sys
import tarfile
import time

from botocore.config import Config
from botocore.exceptions import NoCredentialsError
from datetime import datetime

DAYS = 7 # Number of days to backup

def check_args():
    if len(sys.argv) != 5:
        print("No valid args found. Leaving...", os.linesep)
        sys.exit(1)

    source = sys.argv[1]

    if os.path.exists(source) is False:
        print("Folder " + source + " not found", os.linesep)
        sys.exit(1)

    dest = sys.argv[2]
    now = datetime.now()
    backup_file = "/tmp/" + \
        now.strftime("%Y-%m-%d_%H-%M-%S_") + dest + ".tar.gz"
    s3_filename = now.strftime("%Y-%m-%d_%H-%M-%S_") + dest + ".tar.gz"

    if os.path.isfile(backup_file):
        print("File already exists. Leaving...", os.linesep)
        sys.exit(1)

    bucket_name = sys.argv[3]

    healthcheck_url = sys.argv[4]

    return source, backup_file, s3_filename, bucket_name, healthcheck_url

def delete_old_files(source):
    current_timestamp = time.time()
    max_timestamp = (60 * 60 * 24 * DAYS)

    # Loop over all files and folders in provided directory
    for root, dirs, files in os.walk(source):

        # Remove files older than DAYS
        for file_name in files:
            file_path = os.path.join(root, file_name)
            created_at = os.path.getctime(file_path)
            if (current_timestamp - created_at) >= max_timestamp:
                print("REMOVE:", file_path, os.linesep)
                os.remove(file_path)
            else:
                print("BACKUP:", file_path, os.linesep)

        # Remove empty folders
        for folder_name in dirs:
            folder_path = os.path.join(root, folder_name)
            if len(os.listdir(folder_path)) == 0:
                print("EMPTY DIR:", folder_path, os.linesep)
                os.rmdir(folder_path)


def create_backup(source, backup_file):
    print("Adding files to %s...\n" % backup_file)

    with tarfile.open(backup_file, "w:gz") as tar:
        tar.add(source)
    tar.close()

def upload_to_aws(local_file, bucket, s3_file):
    def_config = Config(
        region_name='eu-west-3',
        signature_version='v4',
        retries={
            'max_attempts': 3,
            'mode': 'standard'
        }
    )

    s3 = boto3.client('s3', config=def_config)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful", os.linesep)
        os.remove(local_file)
    except FileNotFoundError:
        print("The file was not found", os.linesep)
    except NoCredentialsError:
        print("Credentials not available", os.linesep)


def main():
    source, backup_file, s3_filename, bucket_name, healthcheck_url = check_args()

    try:
        requests.get(healthcheck_url + "/start", timeout=5)
    except requests.exceptions.RequestException:
        pass

    delete_old_files(source)
    create_backup(source, backup_file)
    upload_to_aws(backup_file, bucket_name, s3_filename)

    requests.get(healthcheck_url)

main()

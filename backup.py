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
from subprocess import run

DAYS = 7 # Number of days to backup
PASS_ENV = "ENCRYPTION_PASS"

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

    if os.getenv(PASS_ENV) is None:
        print("No encryption password provided. Leaving...", os.linesep)
        sys.exit(1)

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

    os.chdir(source)
    with tarfile.open(backup_file, "w:gz") as tar:
        tar.add(".")
    tar.close()


def encrypt_file(backup_file):
    print("Encrypting backup file %s...\n" % backup_file)

    encrypted_file = backup_file + ".encrypted"

    result = run([
        "openssl",
        "enc", "-aes-256-cbc", "-md", "sha512",
        "-pbkdf2", "-iter", "100000",
        "-pass", "env:" + PASS_ENV, "-salt",
        "-in", backup_file,
        "-out", encrypted_file
    ])

    if result.returncode != 0:
        print("Error when encrypting backup file. Returning unencrypted file", os.linesep)
        return backup_file

    print("Encryption successful!", os.linesep)
    return encrypted_file

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
    backup_file = encrypt_file(backup_file)
    upload_to_aws(backup_file, bucket_name, s3_filename)

    requests.get(healthcheck_url)

main()

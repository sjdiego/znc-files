# ZNC config files

Repository of files to have a ZNC instance and backup log files into S3 bucket.

## Requirements
- Python3
- Docker
- aws-cli
- AWS account with S3 permissions
- [Healthchecks.io](https://www.healthchecks.io) account

## How to start ZNC
Just start it with docker using the following command:
- `docker-compose up`

## Deployment of S3 bucket using Cloudformation
Execute the following command:
- `aws cloudformation deploy --stack-name <your-desired-stack-name> --template-file stack.yml --capabilities CAPABILITY_IAM`

## How to backup log files
Before using this script you should have aws-cli already configured and authenticated, and a ping endpoint in healthchecks.io

The backup script performs the following operations:
- Checks for the required parameters
- Removes old log files (it should be already backup'd) and empty directories
- Looks for newest log files and creates a tar.gz file in /tmp
- Encrypts tar file with password provided in env var
- Uploads tar.gz file to S3 bucket
- Confirms operation to Healthchecks.io

## Create a cronjob for backup
Rename cronjob.example.sh, modify it with encryption password, chmod +x it and add an entry into your cron file like this:
- `0 2 * * MON ~/znc/cronjob.sh >> ~/znc/backup.log 2>&1`

## How to decrypt file
Execute the following commands:

```
$ export ENCRYPTION_PASS=<your_password>

$ openssl enc -aes-256-cbc \
    -md sha512 -iter 100000 \
    -pbkdf2 -salt \
    -d \
    -in <file.tar.gz.encrypted> \
    -out unencrypted.tar.gz \
    -pass env:ENCRYPTION_PASS

$ unset ENCRYPTION_PASS
```

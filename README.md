# ZNC config files

Repository of files to have a ZNC instance and backup log files into S3 bucket.

## Requirements
- Python3
- Docker
- aws-cli
- AWS account with S3 permissions
- Healtchecks.io account

## How to start ZNC
Just start it with docker using the following command:
- `docker-compose up`

## How to backup log files

Before using this script you should have aws-cli already configured and authenticated, and a ping endpoint in healthchecks.io

The backup script performs the following operations:
- Checks for the required parameters
- Removes old log files (it should be already backup'd) and empty directories
- Looks for newest log files and creates a tar.gz file in /tmp
- Uploads tar.gz file to S3 bucket
- Confirms operation to Healtchecks.io

## Create a cronjob for backup
Just add an entry into your cron file like this:
- `0 2 * * MON python3 backup.py ./config/users/<your-user>/networks/<your-network>/moddata/log znclogs <your-s3-bucket-name> https://hc-ping.com/<endpoint-uuid> >> ./backup.log 2>&1`

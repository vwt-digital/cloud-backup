import os

# Google Storage Bucket
GOOGLE_STORAGE_BUCKET = "{}-{}-backup-stg".format(os.environ['BACKUP_PROJECT_ID'], os.environ['PROJECT_ID'])
# Base path of blobs stored
GIT_BACKUP_BASE_PATH = 'git-backup'
#Expected Location of data catalog.
DATA_CATALOG = 'config/data_catalog.json'
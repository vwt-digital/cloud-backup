import logging
import base64
import json

import datetime
import shutil
import tarfile

import git
import os
import tempfile

import config

from google.cloud import storage
from google.cloud import kms_v1


def receive_pubsub_backup_trigger_func(data, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         data (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    logging.basicConfig(level=logging.info)

    if 'data' in data:
        pubsub_message = base64.b64decode(data['data']).decode('utf-8')
        logging.info('Python Pub/Sub receive_pubsub_backup_trigger_func function received message %s.', pubsub_message)

        git_list = get_list_of_gits(config.DATA_CATALOG)
        for github in git_list:
            dump_repo(github)
        now = datetime.datetime.utcnow()
        destination_path = '%s/%d/%d/%d/%s' % (config.GIT_BACKUP_BASE_PATH,
                                               now.year,
                                               now.month,
                                               now.day,
                                               config.DATA_CATALOG)
        upload_blob(config.GOOGLE_STORAGE_BUCKET, config.DATA_CATALOG, destination_path)


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    logging.info('File {} uploaded to {}.'.format(source_file_name, destination_blob_name))


def get_list_of_gits(json_file_name):
    json_file = open(json_file_name, 'r')
    catalog = json.load(json_file)

    download_urls = []
    for entry in catalog['dataset']:
        if 'distribution' in entry:
            for dist in entry['distribution']:
                if 'downloadURL' in dist and dist['downloadURL'].endswith('.git'):
                    download_urls.append(dist['downloadURL'])
    json_file.close()
    return download_urls


def get_project_name_from_git_url(url):
    return url.split("/")[-1]


def dump_repo(repo_url):
    if get_project_name_from_git_url(repo_url) == 'odoo.git':
        logging.info('Skipping repo {} as it is too big'.format(get_project_name_from_git_url(repo_url)))
        return ''

    tmpdir = tempfile.mkdtemp()
    temp_repo_path = os.path.join(tmpdir, get_project_name_from_git_url(repo_url))
    tar_name = temp_repo_path + ".tar.bz2"

    now = datetime.datetime.utcnow()
    destinationpath = '%s/%d/%d/%d/%s%s' % (config.GIT_BACKUP_BASE_PATH,
                                            now.year,
                                            now.month,
                                            now.day,
                                            get_project_name_from_git_url(repo_url),
                                            ".tar.bz2")

    github_access_token = get_access_token()

    if github_access_token:
        authenticated_repo_url = "https://%s:x-oauth-basic@%s" % (github_access_token,
                                                                  repo_url.split("://")[-1])
    else:
        authenticated_repo_url = repo_url

    git.Repo.clone_from(authenticated_repo_url, temp_repo_path, mirror=True)

    tar = tarfile.open(tar_name, "w:bz2")
    tar.add(temp_repo_path, arcname=get_project_name_from_git_url(repo_url))
    tar.close()

    try:
        upload_blob(config.GOOGLE_STORAGE_BUCKET, tar_name, destinationpath)
    finally:
        shutil.rmtree(tmpdir)

    return destinationpath


def get_access_token():
    github_access_token_encrypted = open(config.GITHUB_ACCESS_TOKEN_ENCRYPTED, "rb").read()
    kms_client = kms_v1.KeyManagementServiceClient()
    crypto_key_name = kms_client.crypto_key_path_path(os.environ['PROJECT_ID'], 'europe-west1', 'github',
                                                      'github-access-token')
    decrypt_response = kms_client.decrypt(crypto_key_name, github_access_token_encrypted)
    return decrypt_response.plaintext.decode("utf-8").replace('\n', '')

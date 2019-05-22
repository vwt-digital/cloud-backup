import logging
import base64
import json

import datetime
import shutil
import tarfile

import git

import config

from google.cloud import storage



def receive_pubsub_backup_trigger_func(data, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
    Args:
         message (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """

    logging.basicConfig(level=logging.info)

    if 'data' in data:
        pubsub_message = base64.b64decode(data['data']).decode('utf-8')
        logging.info('Python Pub/Sub receive_pubsub_backup_trigger_func function received message %s.', pubsub_message)

        git_list = get_list_of_gits(pubsub_message)
        for github in git_list:
            dump_repo(github)


def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    logging.info('File {} uploaded to {}.'.format(source_file_name, destination_blob_name))


def get_list_of_gits(json_string):
    catalog = json.loads(json_string)

    download_urls = []
    for entry in catalog['dataset']:
        if 'distribution' in entry:
            for dist in entry['distribution']:
                if 'downloadURL' in dist and dist['downloadURL'].endswith('.git'):
                    download_urls.append(dist['downloadURL'])
    return download_urls


def get_project_name_from_git_url(url):
    return url.split("/")[-1]


def dump_repo(repo_url):

    tmp_path = '/tmp/' + get_project_name_from_git_url(repo_url)
    tar_name = tmp_path + ".tar.bz2"

    now = datetime.datetime.utcnow()
    destinationpath = '%s/%d/%d/%d/%s' % (config.BASE_PATH,
                                          now.year,
                                          now.month,
                                          now.day,
                                          get_project_name_from_git_url(repo_url))

    git.Repo.clone_from(repo_url, tmp_path, mirror=True)

    tar = tarfile.open(tar_name, "w:bz2")
    tar.add(tmp_path, arcname=get_project_name_from_git_url(repo_url))
    tar.close()

    upload_blob(config.GOOGLE_STORAGE_BUCKET, tar_name, destinationpath)

    shutil.rmtree(tmp_path)

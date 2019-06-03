import logging
import shutil
import tarfile

import git
import os

from google.cloud import storage


def test_backup_func(data, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    bucket = data['bucket']
    file = data['name']
    logging.basicConfig(level=logging.info)

    test_backup_success(bucket, file, "/tmp/new_dir")


def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    blob.download_to_filename(destination_file_name)

    logging.info('Blob {} downloaded to {}.'.format(source_blob_name, destination_file_name))


def get_temp_dir(temp_dir_location, dir_name):
    temp_dir = '{}/{}/'.format(temp_dir_location, dir_name)
    os.makedirs(temp_dir)
    return temp_dir


def get_project_name(google_file_name, suffix=True):
    base_name = google_file_name.split("/")[-1]
    if not suffix:
        base_name = base_name.split(".")[0]
    return base_name


def test_backup_success(bucket, file, temp_location):
    try:
        tar_dir = get_temp_dir(temp_location, 'tar')
        bare_repo_dir = get_temp_dir(temp_location, 'repo')
        reconstructed_repo_dir = get_temp_dir(temp_location, 'work')

        tar_location = '%s/%s' % (tar_dir, get_project_name(file))

        download_blob(bucket, file, tar_location)

        tar = tarfile.open(tar_location, "r:bz2")
        tar.extractall(path=bare_repo_dir)
        tar.close()

        git_directory = get_project_name(file, False) + ".git"
        bare_repo_dir = '%s/%s' % (bare_repo_dir, git_directory)

        cloned_repo = git.Repo.clone_from(bare_repo_dir, reconstructed_repo_dir)

        assert os.path.isdir(cloned_repo.working_tree_dir)
        assert os.listdir(cloned_repo.working_tree_dir)

        file_string = ", ".join(os.listdir(cloned_repo.working_tree_dir))

        logging.info('Found the following files and directories at root level: {}'.format(file_string))
    finally:
        shutil.rmtree(temp_location)

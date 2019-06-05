import logging
import shutil
import tarfile

import git
import os

import config

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
    if file.startswith(config.GIT_BACKUP_BASE_PATH):
        test_backup_success(bucket, file, "/tmp")


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


def get_new_dir(base_dir):
    new_dir = "{}/{}".format(base_dir, 'temporary_dir')
    if not os.path.isdir(new_dir):
        return new_dir
    else:
        for i in range(100):
            new_path = "{}{}".format(new_dir, i)
            if not os.path.isdir(new_path):
                return new_path


def test_backup_success(bucket, file, location):
    temp_location = get_new_dir(location)
    try:
        tar_dir = get_temp_dir(temp_location, 'tar')
        bare_repo_dir = get_temp_dir(temp_location, 'repo')
        reconstructed_repo_dir = get_temp_dir(temp_location, 'work')

        base_tar_name = file.split("/")[-1]

        tar_location = '%s%s' % (tar_dir, base_tar_name)

        download_blob(bucket, file, tar_location)
        if not tar_location.endswith("data_catalog.json"):

            tar = tarfile.open(tar_location, "r:bz2")
            tar.extractall(path=bare_repo_dir)
            tar.close()

            try:
                git_directory = base_tar_name[:-len(".tar.bz2")]
                bare_repo_dir = '%s%s' % (bare_repo_dir, git_directory)

                try:
                    cloned_repo = git.Repo.clone_from(bare_repo_dir, reconstructed_repo_dir)

                    file_string = ", ".join(os.listdir(cloned_repo.working_tree_dir))

                    logging.info('Found the following files and directories at root level: {}'.format(file_string))
                except git.exc.GitError:
                    logging.error(RuntimeError("BACKUP FAILURE: Git {} could not be reconstructed.".format(file)))
            except tarfile.ReadError:
                logging.error(RuntimeError("BACKUP FAILURE: File {} is not a valid tar-file".format(file)))

    finally:
        shutil.rmtree(temp_location)

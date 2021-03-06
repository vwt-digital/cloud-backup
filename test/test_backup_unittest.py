import unittest
from test import test_config
import main
import mock
import os
import shutil


def fake_upload_blob(bucket_name, source_file_name, destination_blob_name):
    os.makedirs(destination_blob_name)
    shutil.copy(source_file_name, destination_blob_name)


def get_fake_access_token():
    return test_config.TESTING_TOKEN


class TestMain(unittest.TestCase):

    def test_get_list_of_gits(self):
        expected_git_list = test_config.GIT_LIST
        git_list = main.get_list_of_gits(test_config.TEST_DATA_CATALOG)

        self.assertCountEqual(expected_git_list, git_list,
                              "The expected Git List should contain the urls that are actually inside the data catalogue.")

    def test_get_project_name_from_git_url(self):
        git_url = "https://github.com/vwt-digital/example.git"
        expected_project_name = 'example.git'
        project_name = main.get_project_name_from_git_url(git_url)

        self.assertEqual(expected_project_name, project_name,
                         "The method should take the last part of the url {}".format(git_url))

    @mock.patch('main.get_access_token', side_effect=get_fake_access_token)
    @mock.patch('main.upload_blob', side_effect=fake_upload_blob)
    def test_dump_repo(self, upload_blob_function, access_token_function):
        git_url = "https://github.com/vwt-digital/restingest.git"
        file_location = main.dump_repo(git_url)
        file_name = "%s/%s.tar.bz2" % (file_location,
                                       main.get_project_name_from_git_url(git_url))

        file_exists = os.path.isfile(file_name)

        try:
            self.assertTrue(file_exists, "Method should create a file in {}.".format(file_location))
        finally:
            shutil.rmtree(file_location.split("/")[0])
            file_exists = os.path.isfile(file_name)
            self.assertFalse(file_exists, "Test method should be properly cleaned up.".format(file_location))

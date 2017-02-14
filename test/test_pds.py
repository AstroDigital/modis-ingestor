import os
import unittest
from modispds.pds import push_to_s3, exists, s3_list, del_from_s3, make_index, make_scene_list


class TestPDS(unittest.TestCase):
    """ Test utiltiies for publishing data on AWS PDS """

    metadata = [
        {'key1': 'val1', 'key2': 'val2', 'key3': 'val3'},
        {'key1': 'val4', 'key2': 'val5', 'key3': 'val6'},
    ]

    def test_make_index(self):
        """ Create HTML index of some files """
        fname = make_index('thumbnail.jpg', 'product', ['file1.tif', 'file2.tif'])
        self.assertTrue(os.path.exists(fname))

    def test_make_scene_list(self):
        """ Create a scene list """
        fout = make_scene_list(self.metadata)
        self.assertTrue(os.path.exists(fout))
        os.remove(fout)
        self.assertFalse(os.path.exists(fout))

    def test_exists(self):
        """ Check for existence of fake object """
        self.assertFalse(exists('s3://modis-pds/nothinghere'))

    def test_list_nothing(self):
        """ Get list of objects under a non-existent path on S3 """
        urls = s3_list('s3://modis-pds/nothinghere')
        self.assertEqual(len(urls), 0)

    def test_list(self):
        """ Get list of objects under a path on S3 """
        url = push_to_s3(__file__, 'modis-pds', 'testing/unittests')
        fnames = s3_list(os.path.dirname(url))
        self.assertEqual(len(fnames), 1)
        self.assertEqual(fnames[0], url)
        del_from_s3(url)

    def test_push_to_s3(self):
        """ Push file to S3 """
        url = push_to_s3(__file__, 'modis-pds', 'testing')
        self.assertTrue(exists(url))
        del_from_s3(url)

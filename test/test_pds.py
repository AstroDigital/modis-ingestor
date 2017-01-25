import os
import unittest
from modispds.pds import push_to_s3, exists, del_from_s3, make_index


class TestPDS(unittest.TestCase):
    """ Test utiltiies for publishing data on AWS PDS """

    def test_make_index(self):
        """ Create HTML index of some files """
        fname = make_index('thumbnail.jpg', 'product', ['file1.tif', 'file2.tif'])
        self.assertTrue(os.path.exists(fname))

    def test_push_to_s3(self):
        """ Push file to S3 """
        url = push_to_s3(__file__, 'modis-pds', 'testing')
        self.assertTrue(exists(url))
        del_from_s3(url)

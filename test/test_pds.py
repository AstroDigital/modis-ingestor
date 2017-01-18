import os
import unittest
from modispds.pds import push_to_s3, del_from_s3, make_index


class TestPDS(unittest.TestCase):
    """ Test utiltiies for publishing data on AWS PDS """

    def test_push_to_s3(self):
        """ Push file to S3 """
        url = push_to_s3(__file__, 'modis-pds', 'testing')
        del_from_s3(url)


    def test_make_index(self):
        """ Download a file from CMR """
        fname = make_index('thumbnail.jpg', 'product', ['file1.tif', 'file2.tif'])
        self.assertTrue(os.path.exists(fname))

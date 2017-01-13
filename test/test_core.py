import os
import unittest
from modispds.cmr import query, download
from modispds.core import convert_to_geotiff


class TestCore(unittest.TestCase):
    """ Test query and downloading from CMR """

    date1 = '2016-01-01'

    def test_main(self):
        """ Query CMR """
        q = query(self.date1, self.date1)[0]
        fname = download(q['url'], path=os.path.dirname(__file__))
        fnames = convert_to_geotiff(fname)
        for f in fnames:
            self.assertTrue(os.path.exists(f))

import os
import unittest
from modispds.cmr import query, download_granule
from modispds.core import convert_to_geotiff


class TestCore(unittest.TestCase):
    """ Test query and downloading from CMR """

    date1 = '2016-01-01'

    @classmethod
    def setUpClass(self):
        """ Setup class once by issuing a query """
        q = query(self.date1, self.date1)
        self.fnames = download_granule(q[0])

    def test_convert_to_geotiff(self):
        """ Convert hdf to individual GeoTIFF files """
        fnames = convert_to_geotiff(self.fnames[0], outdir=os.path.dirname(__file__))
        for f in fnames:
            self.assertTrue(os.path.exists(f))

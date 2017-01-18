import os
import unittest
from modispds.cmr import query, download_granule


class TestCMR(unittest.TestCase):
    """ Test query and downloading from CMR """

    date1 = '2016-01-01'
    url = 'http://e4ftl01.cr.usgs.gov//MODV6_Cmp_B/MOTA/MCD43A4.006/2016.01.01/MCD43A4.A2016001.h11v12.006.2016174075640.hdf'

    @classmethod
    def setUpClass(self):
        """ Setup class once by issuing a query """
        self.q = query(self.date1, self.date1)

    def test_query(self):
        """ Query CMR """
        self.assertEqual(len(self.q), 299)
        keys = self.q[0].keys()
        self.assertTrue('Granule' in keys)

    def test_download(self):
        """ Download a file from CMR """
        q = self.q[0]
        url = q['Granule']['OnlineAccessURLs']['OnlineAccessURL']['URL']
        self.assertEqual(url, self.url)
        fnames = download_granule(q, outdir=os.path.dirname(__file__))
        for f in fnames:
            self.assertTrue(os.path.exists(f))
            os.remove(f)

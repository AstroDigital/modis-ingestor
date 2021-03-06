import os
from dateutil.parser import parse
import unittest
from modispds.earthdata import query, download_granule


class TestCMR(unittest.TestCase):
    """ Test query and downloading from CMR """

    date1 = parse('2016-01-01').date()
    date2 = parse('2016-01-02').date()
    date3 = parse('2016-01-30').date()
    url = 'http://e4ftl01.cr.usgs.gov//MODV6_Cmp_B/MOTA/MCD43A4.006/2016.01.01/MCD43A4.A2016001.h11v12.006.2016174075640.hdf'

    @classmethod
    def setUpClass(self):
        """ Setup class once by issuing a query """
        self.q = query(self.date1, self.date1)

    def test_query(self):
        """ Query CMR """
        self.assertEqual(len(self.q), 299)
        keys = self.q[0].keys()
        self.assertTrue('links' in keys)

    def test_query_2days(self):
        """ Query CMR for two days """
        q = query(self.date1, self.date2)
        self.assertEqual(len(q), 598)

    def _test_query_30days(self):
        """ Query CMR for 30 days """
        q = query(self.date1, self.date3)
        self.assertEqual(len(q), 9272)

    def test_download(self):
        """ Download a file from CMR """
        q = self.q[0]
        url = q['links'][0]['href']
        self.assertEqual(url, self.url)
        fnames = download_granule(q, outdir=os.path.dirname(__file__))
        for f in fnames:
            self.assertTrue(os.path.exists(f))
            os.remove(f)

import os
import unittest
from modispds.cmr import query, download


class TestCMR(unittest.TestCase):
    """ Test query and downloading from CMR """

    date1 = '2016-01-01'

    def test_query(self):
        """ Query CMR """
        q = query(self.date1, self.date1)
        self.assertEqual(len(q), 1000)
        keys = q[0].keys()
        self.assertTrue('date' in keys)
        self.assertTrue('url' in keys)
        self.assertTrue('thumb' in keys)
        dates = [i['date'] for i in q]
        # print(dates)

    def test_download(self):
        """ Download a file from CMR """
        q = query(self.date1, self.date1)[0]
        fname = download(q['url'])
        self.assertTrue(os.path.exists(fname))

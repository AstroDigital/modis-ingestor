import os
import unittest
from modispds.cmr import query, download_granule
from modispds.core import get_s3_path, ingest_granule, convert_to_geotiff, parse_args
from modispds.pds  import del_from_s3


class TestCore(unittest.TestCase):
    """ Test query and downloading from CMR """

    date1 = '2016-01-01'
    fname = 'MCD43A4.A2015266.h12v07.006.2016168081200.hdf'

    @classmethod
    def setUpClass(self):
        """ Setup class once by issuing a query """
        self.q = query(self.date1, self.date1)
        self.fnames = download_granule(self.q[0])

    def test_parse_args(self):
        """ Parse arguments for CLI """
        args = '%s %s' % (self.date1, self.date1)
        args = parse_args(args.split(' '))
        self.assertEqual(args.start_date, self.date1)
        self.assertEqual(args.end_date, self.date1)

    def test_get_s3_path(self):
        """ Get S3 pathname from file """
        truth_path = 'MCD43A4.006/12/07/2015266'
        path = get_s3_path(self.fname)
        self.assertEqual(path, truth_path)
        prefix = 'test'
        path = get_s3_path(self.fname, prefix=prefix)
        self.assertEqual(path, os.path.join(prefix, truth_path))

    def test_convert_to_geotiff(self):
        """ Convert hdf to individual GeoTIFF files """
        fnames = convert_to_geotiff(self.fnames[0], outdir=os.path.dirname(__file__))
        for f in fnames:
            self.assertTrue(os.path.exists(f))

    def test_ingest_granule(self):
        """ Ingest granule (download and save to S3) """
        fnames = ingest_granule(self.q[0], prefix='testing')
        self.assertEqual(len(fnames), 18)
        for f in fnames:
            del_from_s3(f)

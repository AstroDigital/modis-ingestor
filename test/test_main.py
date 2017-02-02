import os
import logging
import unittest
import datetime
from modispds.cmr import query, download_granule
from modispds.main import get_s3_path, ingest_granule, get_date, granule_exists, convert_to_geotiff, parse_args
from modispds.pds import s3_list, del_from_s3
from modispds.products import products

# quiet these loggers
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('nose').setLevel(logging.CRITICAL)
logging.getLogger('requests').setLevel(logging.CRITICAL)


class TestMain(unittest.TestCase):
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

    def test_get_date(self):
        """ Parse date from granule id (filename) """
        d = get_date(os.path.splitext(self.fname)[0])
        self.assertTrue(isinstance(d, datetime.datetime))
        self.assertEqual(d, datetime.datetime(2015, 9, 23))

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
            ext = os.path.splitext(f)[1]
            suffix = os.path.splitext(f)[0].split('_')[1]
            self.assertTrue(os.path.exists(f))
            if ext != '.ovr':
                self.assertTrue(suffix in products['MCD43A4.006']['bandnames'])

    def test_ingest_granule(self):
        """ Ingest granule (download and save to S3) """
        result = ingest_granule(self.q[0], prefix='testing')
        # granuleid
        self.assertEqual(result['gid'], 'MCD43A4.A2016001.h11v12.006.2016174075640')
        self.assertEqual(result['date'], datetime.date(2016, 1, 1))
        # path
        path = get_s3_path(result['gid'], prefix='testing')
        self.assertEqual(path, 'MCD43A4.006/12/07/2015266')
        # download url
        url = os.path.join('https://modis-pds.s3.amazonaws.com', path, 'index.html')
        self.assertEqual(result['download_url'], url)

        # check remote files
        s3path = os.path.join('s3://modis-pds/', path)
        fnames = s3_list(s3path)
        self.assertTrue(len(fnames), 25)
        # test that granule exists
        # self.assertTrue(granule_exists(fname))
        for f in fnames:
            del_from_s3(f)
            # once one file has been removed the granule should not qualify as existing
            #self.assertFalse(granule_exists(fname))
        #self.assertFalse(granule_exists(fname))

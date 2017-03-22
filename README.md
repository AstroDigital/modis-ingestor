# modis-ingestor

This library and script is for the ingestion of MODIS data products from NASA Earthdata web resources into Amazon Web Services S3. Further information on this initiative, sponsored by AstroDigital and AWS, can be found here:

https://aws.amazon.com/public-datasets/modis/

There are 3 modules includes in this library:

	- modispds.cmr: Contains functions for querying NASA CMR (Common Metadata Repository) and for downloading data from Earthdata resources requiring authentication.

	- modispds.pds: Utility functions for working with Public Datasets on AWS, such as uploading, existence checks, and deletion of objects from S3.

	- modispds.main: Main ingestor functions that ingest a complete granule of MODIS data, convert to GeoTIFF, and upload to S3, creating an index file for each date.

Some environment variables are required, which can be provided in an '.env' file in the library directory. AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION must be provided to have access to AWS resources, and EARTHDATA_USER and EARTHDATA_PASS are needed to download data from NASA Earthdata resources.

The main module also includes a command line script to ingest data given a date range. A Dockerfile and docker-compose file are provided as well that can be used to run utility. First, the docker image must be built:

	$ docker-compose build

	# run tests, if desired
	$ docker-compose run test

	# run script to ingest data from Jan 2016
	$ docker-compose run ingest 2016-01-01 2016-01-31 


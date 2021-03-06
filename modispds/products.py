# MODIS product configuration

products = {
    'MCD43A4.006': {
        'day_offset': 8,
        'bandnames':
            ['B%sqa' % str(i).zfill(2) for i in range(1, 8)] +
            ['B%s' % str(i).zfill(2) for i in range(1, 8)],
        'overviews': ([False] * 7) + ([True] * 7)
    },
    'MOD09GA.006': {
        'day_offset': 0,
        'bandnames':
            ['numobs1km', 'state', 'senzen', 'senaz', 'range', 'solzen', 'solaz', 'geoflags', 'orbit', 'granule', 'numobs500m'] +
            ['B%s' % str(i).zfill(2) for i in range(1, 8)] +
            ['qc500m', 'obscov', 'obsnum', 'qscan'],
        'overviews': ([False] * 11) + ([True] * 7) + ([False] * 4)
    },
    'MYD09GA.006': {
        'day_offset': 0,
        'bandnames':
            ['numobs1km', 'state', 'senzen', 'senaz', 'range', 'solzen', 'solaz', 'geoflags', 'orbit', 'granule', 'numobs500m'] +
            ['B%s' % str(i).zfill(2) for i in range(1, 8)] +
            ['qc500m', 'obscov', 'obsnum', 'qscan'],
        'overviews': ([False] * 11) + ([True] * 7) + ([False] * 4)
    },
    'MOD09GQ.006': {
        'day_offset': 0,
        'bandnames': ['numobs', 'B01', 'B02', 'qc', 'obscov', 'obsnum', 'orbit', 'granule'],
        'overviews': [False, True, True, False, False, False, False, False]
    },
    'MYD09GQ.006': {
        'day_offset': 0,
        'bandnames': ['numobs', 'B01', 'B02', 'qc', 'obscov', 'obsnum', 'orbit', 'granule'],
        'overviews': [False, True, True, False, False, False, False, False]
    }
}

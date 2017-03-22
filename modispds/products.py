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
        'bandnames': [],
        'overviews': []
    },
    'MYD09GA.006': {
        'day_offset': 0,
        'bandnames': [],
        'overviews': []
    },
    'MOD09GQ.006': {
        'day_offset': 0,
        'bandnames': [],
        'overviews': []
    },
    'MYD09GQ.006': {
        'day_offset': 0,
        'bandnames': [],
        'overviews': []
    }
}

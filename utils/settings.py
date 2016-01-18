TABLE = 'bandc_items'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'cconsole': {
            'level': 'DEBUG',
            'class': 'project_runpy.ColorizingStreamHandler',
        },
    },
    'root': {
        'handlers': ['cconsole'],
        'level': 'DEBUG',
    },
    'loggers': {
        'sqlalchemy.engine.base.Engine': {
            'handlers': ['cconsole'],
            'propagate': False,
        },
    },
}

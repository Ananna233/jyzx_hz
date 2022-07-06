from logging.config import dictConfig

from flask import Flask

import config
from app.models import db
from app.utils import JSONEncoder

dict_conf = {'version': 1,
             'disable_existing_loggers': False,
             'formatters':
                 {
                     'simple': {
                         'format': '%(message)s'
                     },
                     'error': {
                         'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
                     }
                 },
             'handlers': {
                 'console': {'class': 'logging.StreamHandler', 'level': 'DEBUG', 'formatter': 'simple',
                             'stream': 'ext://flask.logging.wsgi_errors_stream'},
                 'info_file_handler': {'class': 'logging.handlers.RotatingFileHandler', 'level': 'INFO',
                                       'formatter': 'error',
                                       'filename': './logs/app_info.log', 'maxBytes': 10485760, 'backupCount': 20,
                                       'encoding': 'utf8'},
                 'error_file_handler': {'class': 'logging.handlers.RotatingFileHandler', 'level': 'ERROR',
                                        'formatter': 'error',
                                        'filename': './logs/app_errors.log', 'maxBytes': 10485760, 'backupCount': 20,
                                        'encoding': 'utf8'}
             },

             'root': {'level': 'INFO', 'handlers': ['console', 'info_file_handler', 'error_file_handler']}
             }
from flask_cors import *


def create_app():
    dictConfig(dict_conf)
    app = Flask(__name__)
    app.config.from_object(config)
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_MIMETYPE'] = "application/json;charset=utf-8"  # utf-8编码
    app.config["SECRET_KEY"] = "da3dn1=12n123ASVD6-52+*2413AA"
    app.json_encoder = JSONEncoder
    CORS(app, supports_credentials=True, resources='/*')
    from app.api import bp
    from app.inspur import gp
    app.register_blueprint(bp)
    app.register_blueprint(gp)
    db.init_app(app=app)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run()

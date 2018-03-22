import os
import logging
from flask import Flask
from flask import request, jsonify
from time import strftime


def create_app():
    from response import AutoJSONEncoder
    from search.search_engine import search_url
    from logging.handlers import RotatingFileHandler

    # Get the config name
    config_name = os.environ.get('FLASK_CONFIG', 'development')

    # Initialise the app from the config
    app = Flask(__name__, template_folder="../web/templates", static_folder="../web/static")
    app.config.from_object('config_' + config_name)

    # Set custom JSONEncoder
    app.json_encoder = AutoJSONEncoder

    # Setup logging
    file_handler = RotatingFileHandler(
        'dp-search-app.log', maxBytes=1024 * 1024 * 100, backupCount=3)
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

    app.logger.info("Initialising application from config '%s'" % config_name)

    # Import blueprints
    from .search import search as search_blueprint
    from .suggest import suggest as suggest_blueprint
    from .nlp import nlp as nlp_blueprint

    # Register blueprints
    app.register_blueprint(search_blueprint, url_prefix="/search")
    app.register_blueprint(suggest_blueprint, url_prefix="/suggest")
    app.register_blueprint(nlp_blueprint, url_prefix="/nlp")

    # Log some setup variables
    app.logger.info("Elasticsearch url: %s" % search_url)

    # Init suggest models using app config
    from suggest import word2vec_models, supervised_models
    word2vec_models.init(app)
    supervised_models.init(app)

    # Declare function to log each request
    @app.after_request
    def after_request(response):
        """ Logging after every request. """
        # This avoids the duplication of registry in the log,
        # since that 500 is already logged via @app.errorhandler.
        if response.status_code != 500:
            ts = strftime('[%Y-%b-%d %H:%M]')
            app.logger.info('%s %s %s %s %s %s %s',
                            ts,
                            request.remote_addr,
                            request.method,
                            request.scheme,
                            request.full_path,
                            request.cookies,
                            response.status)
        return response

    # Declare function to log all uncaught exceptions and return a 500 with info
    @app.errorhandler(Exception)
    def internal_server_error(exception):
        """ Define a custom error handler that guarantees exceptions are always logged. """
        # Log the exception
        import sys
        import traceback
        from utils import is_number

        type_, value_, traceback_ = sys.exc_info()
        err = {
            "type": str(type_),
            "value": str(value_),
            "traceback": traceback.format_tb(traceback_)
        }
        app.logger.error(str(err) + "\n")
        # Jsonify the exception and return a error response
        response = jsonify(err)
        if hasattr(exception, "status_code") and is_number(exception.status_code):
            response.status_code = int(exception.status_code)
        else:
            response.status_code = 500
        return response

    return app
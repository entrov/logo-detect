import os
from celery import Celery
from celery.signals import setup_logging, after_setup_logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logo_detect_api.settings')

app = Celery('logo_detect_api',backend='rpc://', broker='amqp://')
app.config_from_object('django.conf:settings', namespace='CELERY')

@setup_logging.connect
# @celery.signals.setup_logging.connect
def config_loggers(*args, **kwargs):
    from logging.config import dictConfig  # noqa
    from django.conf import settings  # noqa

    dictConfig(settings.LOGGING)
# @after_setup_logger.connect
# def setup_loggers(logger, *args, **kwargs):
#     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
#     # add filehandler
#     fh = logging.FileHandler('logs.log')
#     fh.setLevel(logging.DEBUG)
#     fh.setFormatter(formatter)
#     logger.addHandler(fh)
app.autodiscover_tasks()
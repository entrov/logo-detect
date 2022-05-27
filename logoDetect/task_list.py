import json
import logging
from celery import Task, current_app, app
import client
from logoDetect.models import TrainingResults, DatasetDownloadResults

logger = logging.getLogger('celery')

class APITask(Task):
    abstract = True
    ignore_result = False
    track_started = True

    name = 'logo_detect_api.apitask'

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info('in constructor ')

    def run(self, *args, **kwargs):
        logger.info('Training Start')
        logger.info(kwargs)
        how_many_training_steps = kwargs.get('how_many_training_steps', None)
        testing_percentage = kwargs.get('testing_percentage', None)
        learning_rate = kwargs.get('learning_rate', None)
        delete_checkpoint = kwargs.get('delete_checkpoint', None)

        logger.info('Training Start')

        response = client.train_model(how_many_training_steps, testing_percentage, learning_rate, delete_checkpoint)
        m_obj = TrainingResults.objects.get(task_id=self.request.id)
        m_obj.results= response
        m_obj.is_completed=True
        m_obj.save()
        logger.info('Training End')

        return response


class DatasetDownloadTask(Task):
    abstract = True
    ignore_result = False
    track_started = True

    name = 'logo_detect_api.DatasetDownloadTask'

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        logger.info('in constructor ')

    def run(self, *args, **kwargs):
        logger.info(kwargs)
        update_dataset = kwargs.get('update_dataset', False)
        logger.info('Downloading Start')
        response = client.download_dataset(update_dataset)
        m_obj = DatasetDownloadResults.objects.get(task_id=self.request.id)
        m_obj.results= response
        m_obj.is_completed=True
        m_obj.save()
        logger.info('Downloading Finish')
        return response


@app.shared_task
def add():
    logger.info('Found addition')
    logger.info('Added {0} and {1} to result, '.format(1,2))
    return 1

current_app.register_task(APITask())
current_app.register_task(DatasetDownloadTask())



#
# def upload_files(self, filenames):
#     for i, file in enumerate(filenames):
#         if not self.request.called_directly:
#             self.update_state(state='PROGRESS',
#                 meta={'current': i, 'total': len(filenames)})
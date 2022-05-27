import json
import os

from celery.result import AsyncResult
from celery.worker.control import revoke
from django.shortcuts import render

# Create your views here.
from rest_framework import permissions, serializers, status
from rest_framework.generics import GenericAPIView

# Create your views here.
from rest_framework.response import Response
import client
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

from logo_detect_api.settings import BASE_DIR
from .models import TrainingResults, DatasetDownloadResults
from .task_list import APITask, add, DatasetDownloadTask

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)


class LogoSerializer(serializers.Serializer):
    image = serializers.ImageField()

class LogoUrlSerializer(serializers.Serializer):
    url = serializers.CharField()

class UpdateDatasetSerializer(serializers.Serializer):
    update_dataset = serializers.BooleanField()

class TrainModelSerializer(serializers.Serializer):
    # image = Base64ImageField(max_length=None, use_url=True,)
    how_many_training_steps = serializers.IntegerField(default=1000)
    testing_percentage = serializers.IntegerField(default=10)
    learning_rate = serializers.FloatField(default=0.1)
    delete_checkpoint = serializers.BooleanField()

class TrainModelResult(serializers.Serializer):
    # image = Base64ImageField(max_length=None, use_url=True,)
    task_id = serializers.CharField(default=1000)


class LogoDetectView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LogoSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        image = serializer.validated_data.get('image')
        try:
            response = client.get_logo_image_clssify(image)
            return Response(response, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({}, status=status.HTTP_200_OK)

class LogoURLDetectView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LogoUrlSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data.get('url')
        response = client.get_logo_url_clssify(url)
        return Response(response, status=status.HTTP_200_OK)

class UpdateDatasetView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = UpdateDatasetSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_dataset = serializer.validated_data.get('update_dataset')

        try:
            previous_object = DatasetDownloadTask.objects.last()
            task_id = previous_object.task_id
            revoke(task_id, terminate=True)
        except Exception as e:
            pass

        r = DatasetDownloadTask().delay(update_dataset=update_dataset)
        # check if no object then create it
        last_obj = DatasetDownloadResults.objects.create(task_id=r.task_id)
        last_obj.save()
        if update_dataset == True:
            return Response(
                {'message': 'Dataset downloading has been started. To check status please use the dataset task id {}.'.format(r.task_id)},
            status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Download dataset is unchecked'},status=status.HTTP_200_OK)

class TrainModelView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TrainModelSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        how_many_training_steps = serializer.validated_data.get('how_many_training_steps')
        testing_percentage = serializer.validated_data.get('testing_percentage')
        learning_rate = serializer.validated_data.get('learning_rate')
        delete_checkpoint = serializer.validated_data.get('delete_checkpoint')
        m_obj = TrainingResults.objects.create()
        response = client.train_model(how_many_training_steps, testing_percentage, learning_rate, delete_checkpoint)
        m_obj.results = response
        m_obj.save()
        return Response(response, status=status.HTTP_200_OK)

class CeleryTestTask(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TrainModelSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        how_many_training_steps = serializer.validated_data.get('how_many_training_steps')
        testing_percentage = serializer.validated_data.get('testing_percentage')
        learning_rate = serializer.validated_data.get('learning_rate')
        delete_checkpoint = serializer.validated_data.get('delete_checkpoint')
        try:
            previous_object = TrainingResults.objects.last()
            task_id = previous_object.task_id
            revoke(task_id, terminate=True)
        except Exception as e:
            pass
        r = APITask().delay(how_many_training_steps=how_many_training_steps,testing_percentage=testing_percentage,learning_rate=learning_rate,delete_checkpoint=delete_checkpoint)
        # check if no object then create it
        last_obj = TrainingResults.objects.create(task_id=r.task_id)
        last_obj.save()
        return Response({'message':'Training has been started. To check status please use the training id {}.'.format(r.task_id)}, status=status.HTTP_200_OK)

class CheckTask(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TrainModelResult

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_id = serializer.validated_data.get('task_id',None)
        task = AsyncResult(status_id)
        last_obj = TrainingResults.objects.get(task_id=status_id)
        if last_obj:
            if last_obj.is_completed:
                if last_obj.results != None:
                    return Response({'results': last_obj.results}, status=status.HTTP_200_OK)
                else:
                    return Response({'message':'Error in training check log file for details'}, status=status.HTTP_200_OK)
            elif not last_obj.is_completed:
                with open(os.path.join(BASE_DIR,'celery.log'), 'r') as f:
                    last_line = f.readlines()[-1]
                return Response({'message': 'Training is continue please check a few minutes later', "log": last_line},
                                status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No a valid task id'}, status=status.HTTP_200_OK)

class CheckDatasetDownloadTask(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = TrainModelResult

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status_id = serializer.validated_data.get('task_id',None)
        task = AsyncResult(status_id)
        last_obj = DatasetDownloadResults.objects.get(task_id=status_id)
        if last_obj:
            if last_obj.is_completed:
                if last_obj.results != None:
                    return Response({'results': last_obj.results}, status=status.HTTP_200_OK)
                else:
                    return Response({'message':'Error in downloading the dataset check log file for details'}, status=status.HTTP_200_OK)
            elif not last_obj.is_completed:
                return Response({'message': 'Dataset downloading is continue please check a few minutes later'},
                                status=status.HTTP_200_OK)
        else:
            return Response({'message': 'No a valid task id'}, status=status.HTTP_200_OK)




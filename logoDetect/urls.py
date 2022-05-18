from django.urls import path, include
from logoDetect import views
from django.conf.urls.static import static

urlpatterns = [
    path('logo_detect/', views.LogoDetectView.as_view(), name='logodetect'),
    path('logo_url_detect/', views.LogoURLDetectView.as_view(), name='logourldetect'),
    path('train_model/', views.TrainModelView.as_view(), name='trainmodel'),
    path('celery_train_model/', views.CeleryTestTask.as_view(), name='celery_trainmodel'),
    path('check_status/', views.CheckTask.as_view(), name='celery_trainmodel_status'),
    path('update_dataset/', views.UpdateDatasetView.as_view(), name='updatedataset'),
]

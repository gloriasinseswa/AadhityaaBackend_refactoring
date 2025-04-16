from django.urls import include, path
from rest_framework import routers
urlpatterns = [
    path('v1/', include('api.v1.urls')),

]   
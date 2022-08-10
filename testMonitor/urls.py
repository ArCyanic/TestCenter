from django.urls import path 
from testMonitor.views import *

urlpatterns = [
    path('mockDays', mockDays),
    path('mockDevices', mockDevices),
    path('getProjectStatistics', getProjectStatistics),
    path('test', test),
    path('getDiffs', getDiffs)
]

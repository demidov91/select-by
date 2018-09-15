"""exchange URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin

from exchange.views import *

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', get_rates, name='rates'),
    url(r'^config/$', config, name='config'),
    url(r'my-points/$', my_points, name="my_points"),
    url(r'save-points/$', save_points, name="save_points"),
    url(r'^i18n/', include('django.conf.urls.i18n')),
]

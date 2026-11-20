from django.urls import path
from . import views

urlpatterns = [

    path('', views.home, name='home'),
    
    path('about/', views.about, name='about'),

    path('results/', views.results, name='results'),

    path('ai/', views.ai_mode, name='ai_mode'),

    path('images/', views.images, name='images'),

    path('videos/', views.videos, name='videos'),

    path('shopping/', views.shopping, name='shopping'),

    path('news/', views.news, name='news'),

    path('site/<slug:site_slug>/', views.site_detail, name='site_detail'),

]
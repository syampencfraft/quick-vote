from django.urls import path
from . import views

urlpatterns = [

    path('', views.first, name='first'),


    path('election_list', views.election_list, name='election_list'),
    path('<int:election_id>/', views.election_detail, name='election_detail'),
    path('<int:election_id>/verify/', views.verify_face, name='verify_face'),
    path('<int:election_id>/vote/', views.cast_vote, name='cast_vote'),
    path('<int:election_id>/results/', views.election_results, name='election_results'),
    path('feedback/', views.feedback_view, name='feedback'),
]

from django.urls import path
from . import views

urlpatterns = [

    path('', views.first, name='first'),


    path('election_list', views.election_list, name='election_list'),
    path('<int:election_id>/', views.election_detail, name='election_detail'),
    path('<int:election_id>/verify/', views.verify_face, name='verify_face'),
    path('<int:election_id>/vote/', views.cast_vote, name='cast_vote'),
    path('<int:election_id>/results/', views.election_results, name='election_results'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('election/add/', views.add_election, name='add_election'),
    path('election/<int:election_id>/edit/', views.edit_election, name='edit_election'),
    path('election/<int:election_id>/toggle/', views.toggle_election, name='toggle_election'),
    path('election/<int:election_id>/candidate/add/', views.add_candidate, name='add_candidate'),
    path('election/<int:election_id>/toggle-results/', views.toggle_results, name='toggle_results'),
    path('election/<int:election_id>/finish/', views.finish_election, name='finish_election'),
    path('feedback/', views.feedback_view, name='feedback'),
]

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    #health check
    path('health-check/',views.health_check,name='health_check'),
    # Static pages
    path('about/', views.about_page, name='about'),
    path('rules/', views.rules_page, name='rules'),
    path('history/', views.history_page, name='history'),

    # Game management
    path('lobby/', views.game_lobby, name='lobby'),
    path('fetch-matches/', views.fetch_matches, name='get_game_history'),
    
    # Challenge system
    path('challenge-approved/<int:game_id>/', views.start_match, name='challenge_approved'),
    path('cancel-game/<int:game_id>/', views.cancel_match, name='cancel_game'),
    
    # Game operations
    path('game/<int:game_id>/', views.match_detail, name='game_detail'),
    path('edit-game/<int:game_id>/', views.update_match, name='edit_game'),
    path('delete-game/<int:game_id>/', views.remove_game, name='delete_game'),
    
]

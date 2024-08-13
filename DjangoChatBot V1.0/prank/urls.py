from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.sign_up, name='signup'),
    path('login/', views.user_login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_user, name='logout'),
    path('chat/', views.start_chat, name='start_chat'),
    path('chat/<str:username>/history/', views.chat_history, name='chat_history'),
    path('chat/<str:username>/new/', views.new_chat, name='new_chat'),
    path('chat/<str:username>/<str:session_id>/', views.chatting, name='chatting'),
    path('chat/<str:username>/<str:session_id>/history/', views.chatting_messages, name='chatting_history'),
    path('chat/<str:username>/<str:session_id>/handle-message/', views.handle_message, name='handle_message'),
    path('chat/<str:username>/<str:session_id>/delete/', views.delete_chat, name='delete_chat'),
]

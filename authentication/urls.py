from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # JWT token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # User endpoints
    path('users/', views.search_users, name='user-search'),
    path('users/<int:user_id>/', views.get_user, name='user-detail'),
    path('users/<int:user_id>/edit/', views.edit_user, name='user-edit'),
    path('users/facebook-user-exists/<int:facebook_id>/', views.facebook_user_exists, name='fb-user-exists'),
    path('users/is-username-available/<str:username>/', views.is_username_available, name='username-available'),
    path('users/register/', views.signup, name='user-signup'),
    path('users/facebook-login/', views.facebook_login, name='fb-login'),
    path('users/forgotten-password/', views.forgotten_password, name='forgotten-password'),
]

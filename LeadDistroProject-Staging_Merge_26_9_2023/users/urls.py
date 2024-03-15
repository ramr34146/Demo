from django.urls import path, include

from .views import (
    EditProfileView, 
    MemberProcessView,
    LDIntegrationView,
    UpdateThemePreferenceView
    )

app_name = 'users'


urlpatterns = [
    path('edit-profile/', EditProfileView.as_view(), name='edit_profile'),

    path('member-process/', MemberProcessView.as_view(), name='member_process'),

    path('integration/', LDIntegrationView.as_view(), name='integration'),

    path('update-theme-preference/', UpdateThemePreferenceView.as_view(), name='update-theme-preference'),

]




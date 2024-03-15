from django.urls import path
from .views import ContactUsView, FeedbackView

app_name = 'contact'
urlpatterns = [
    path('contact/', ContactUsView.as_view(), name='contactus'),
    path('feedback/', FeedbackView.as_view(), name='feedback'),

]

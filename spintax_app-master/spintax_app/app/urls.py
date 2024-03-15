from django.contrib import admin
from django.urls import path, include
from .views import *
from django.contrib.auth import views as auth_views
from django.contrib.auth import views as auth_view
from django.conf.urls.static import static
from django.conf import settings

from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [

    path('login', Login, name='login'),
    path('register', register, name='register'),
    path('', dashboard, name="dashboard"),
    path("verifyEmail/<email>", verify_email, name="verifyEmail"),

    path('rewrite', rewrite, name='rewrite'),
    path('rewrite1', rewrite1, name='rewrite1'),
    path('rewrite-text', rewrite_text, name='rewrite-text'),
    path('rewrite-zip', rewrite_zip, name='rewrite-zip'),

    path('archive', user_archive, name='archive'),
    path('archive/<id>', user_archive_id, name='user_archive_id'),

    path('logout', log_out, name='logout'),

    path('test', test, name='test'),
    path('TestClass/<id>', TestClass.as_view(), name='TestClass'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password/password_reset_form.html',
                                                                 email_template_name="password/password_reset_email.html"),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='password/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='password/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='password/password_reset_complete.html'),
         name='password_reset_complete'),

    # path('password_change', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('password_change', password_change, name='password_change'),
    path('password_change_done',
         auth_views.PasswordChangeDoneView.as_view(template_name='password/password_change_done.html'),
         name='password_change_done'),

    path('paraphrase_data', paraphrase_data, name='paraphrase_data'),

    #     restart
    path('generateUniqueArticle', generate_unique_article, name='generateUniqueArticle'),

    # path('login', Login, name='login'),
    # path('home', home, name='home'),
    # path('spin_article', spin_article, name='spin_article'),
    # path('spin_txt_file', spin_txt_file, name='spin_txt_file'),
    # path('spin_zip_file', spin_zip_file, name='spin_zip_file'),

    path('spintax_chatgpt', spintax_chatgpt, name='spintax_chatgpt'),
    path('data_collection', data_collection, name='data_collection'),
    path('rewrite2', rewrite2, name='rewrite2'),

    path('test1', test1, name='test1')

]

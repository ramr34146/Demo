import time

from . import spintax
import io
import random
import re
import json
import zipfile
import requests
import copy
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import spacy
from spacy.tokens import Token
import random
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CustomUser, ParaphraseData, Archive, Synonyms, DataCollection, SpinParaphrase
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authentication import TokenAuthentication
from rest_framework.views import APIView
from .decorators import *


def send_email(first_name, last_name, email, codes):
    msg = f'Hey {first_name} {last_name}!\n\n\n A sign in attempt requires further verification.\n\nVerification code: {codes} '
    subject = 'Email Verify'
    send_mail(
        subject,
        msg,
        settings.EMAIL_HOST_USER,
        [email],
    )


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        first_name = request.POST.get('first-name')
        last_name = request.POST.get('last-name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        recaptcha_response = request.POST.get('g-recaptcha-response')

        password_regex = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=!]).{8,}$'

        if not first_name and not last_name and not email and not password:
            context = {'error': 'Please fill up the Fields!', "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}

            return render(request, 'register.html', context)

        elif not re.fullmatch(password_regex, password):
            context = {'error': 'Use 8 or more characters with a mix of letters, numbers & symbols',
                       "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
            return render(request, 'register.html', context)
        elif password != confirm_password:
            context = {'error': 'Password Does not Match', "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}

            return render(request, 'register.html', context)
        else:
            if CustomUser.objects.filter(email=email).exists():
                context = {'error': 'User already exists', "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}

                return render(request, 'register.html', context)
            else:
                data = {
                    'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response
                }
                r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
                result = r.json()
                if result['success']:
                    codes = str(random.randint(100000, 999999))
                    user = CustomUser.objects.create_user(email=email, password=password, verification_otp=codes,
                                                          first_name=first_name, last_name=last_name)
                    user.save()
                    send_email(first_name, last_name, email, codes)
                    return redirect('verifyEmail', email)
                context = {'error': 'Invalid please retry this form',
                           "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
                return render(request, 'register.html', context)
    if request.method == 'GET':
        return render(request, 'register.html', {"recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY})


@check_user_login
def Login(request):
    # if request.user.is_authenticated:
    #     return redirect('dashboard')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not email and not password:
            context = {'error': 'Please fill up the Fields!', "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
            return render(request, 'register.html', context)
        elif CustomUser.objects.filter(email=email).exists():
            data = {
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            result = r.json()
            if result['success']:
                user = authenticate(request, email=email, password=password)
                if user is not None:
                    if user.is_verified:
                        login(request, user)
                        return redirect('dashboard')
                    else:
                        context = {'error': 'Please First Verified',
                                   "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
                        return render(request, 'login.html', context)
                else:
                    context = {'error': 'Please enter a valid password',
                               "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
                    return render(request, 'login.html', context)
            else:
                context = {'error': 'Invalid please retry this form',
                           "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
                return render(request, 'login.html', context)
        else:
            context = {'error': 'User does not exist', "recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
            return render(request, 'login.html', context)
    if request.method == 'GET':
        context = {"recaptcha_site_key": settings.GOOGLE_RECAPTCHA_SITE_KEY}
        return render(request, 'login.html', context)


@login_required(login_url='login')
def dashboard(request):
    user = CustomUser.objects.get(email=request.user)

    context = {'name': user.first_name + ' ' + user.last_name}
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def rewrite(request):
    if request.method == 'POST':
        article = request.POST.get('article')
        context = {'rewrite': article, 'result': article}
        return render(request, 'rewrite.html', context)
    if request.method == 'GET':
        return render(request, 'rewrite.html')


@csrf_exempt
def rewrite1(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        content = data['article']
        if not data['article']:
            return JsonResponse({'result': 'Enter Article'})
        # result = spintax.result(content)
        # user = CustomUser.objects.get(email=request.user)
        # archive_save(user, content, result)
        # context = {'result': result}
        # return JsonResponse(context)

        generated_text = spintax.generate_spin_options(content)
        word_count = spintax.count_variations_within_braces(generated_text)
        rewritten_text = spintax.rewrite_sentence(generated_text)
        context = {'generated_text': generated_text,
                   'rewritten_text': rewritten_text,
                   'word_count': word_count}
        return JsonResponse(context)

    if request.method == 'GET':
        return render(request, 'rewrite1.html')


@csrf_exempt
@login_required(login_url='login')
def rewrite_text(request):
    if request.method == 'POST':
        file = request.FILES  # Get the file object from the request
        if file and file['file'].name.endswith('.txt'):
            content = file['file'].read().decode('utf-8')  # Read the contents of the file as a string
            result = spintax.result(content)
            user = CustomUser.objects.get(email=request.user)
            archive_save(user, content, result)
            c = {'result': result}
            return JsonResponse(c)
        else:
            c = {'result': 'Invalid file format. Only .txt files are allowed.'}
            return JsonResponse(c)
    if request.method == 'GET':
        return render(request, 'rewrite_text.html')


def archive_save(user, content, result):
    Archive(user=user, content=content, result=result).save()


def inner_zip_read(inner_zip_bytes):
    txt_content = ''
    inner_zip = zipfile.ZipFile(io.BytesIO(inner_zip_bytes))
    for file_name in inner_zip.namelist():
        if file_name.endswith('.txt'):
            text_file = inner_zip.open(file_name)
            content = text_file.read().decode('utf-8')
            txt_content += content + '\n'
        elif file_name.endswith('.zip'):
            inner_zip_bytes = inner_zip.read(file_name)
            txt_content += inner_zip_read(inner_zip_bytes) + '\n'
    return txt_content


def zip_read(path):
    txt_content = ''
    zip_file = zipfile.ZipFile(path)
    for file_name in zip_file.namelist():
        if file_name.endswith('.txt'):
            text_file = zip_file.open(file_name)
            content = text_file.read().decode('utf-8')
            txt_content += content + '\n'
        elif file_name.endswith('.zip'):
            inner_zip_bytes = zip_file.read(file_name)
            txt_content += inner_zip_read(inner_zip_bytes) + '\n'
    return txt_content


@csrf_exempt
@login_required(login_url='login')
def rewrite_zip(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'result': 'please upload zip'})
        try:
            content = zip_read(file)
            result = spintax.result(content)
            user = CustomUser.objects.get(email=request.user)
            archive_save(user, content, result)
            return JsonResponse({'result': result})
        except Exception as e:
            return JsonResponse({'result': 'invalid zip'})
    if request.method == 'GET':
        return render(request, 'rewrite_zip.html')


def verify_email(request, email):
    if request.method == 'POST':
        codes = request.POST.get('codes')
        try:
            user = CustomUser.objects.get(email=email)
            if user.verification_otp == codes:
                user.is_verified = True
                user.save()
                return redirect('login')
            else:
                context = {'email': email, 'error': 'Invalid email verification code !'}
                return render(request, 'verifyEmail.html', context)
        except Exception as e:
            return HttpResponse('Invalid')

    if request.method == 'GET':
        context = {'email': email}
        return render(request, 'verifyEmail.html', context)


def log_out(request):
    logout(request)
    return redirect('dashboard')


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def paraphrase_data(request):
    json_data = request.body
    stream = io.BytesIO(json_data)
    python_data = JSONParser().parse(stream)
    input_tax = python_data.get('input_tax', None)
    result_tax = python_data.get('result_tax', None)
    select_tax = python_data.get('select_tax', None)
    paraphrase_data_obj = ParaphraseData(input_tax=input_tax, result_tax=result_tax,
                                         select_tax=select_tax)
    paraphrase_data_obj.save()
    return Response({'Data': "true"})


@login_required(login_url='login')
def password_change(request):
    if request.method == 'GET':
        return render(request, 'password/password_change_form.html')
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm-password')
        user = authenticate(request, username=request.user, password=old_password)
        password_regex = r'^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[@#$%^&+=!]).{8,}$'
        if user is None:
            context = {'error': 'Current password does not match!'}
            return render(request, 'password/password_change_form.html', context)
        elif password != confirm_password:
            context = {'error': 'Password and confirm password does not match!'}
            return render(request, 'password/password_change_form.html', context)
        elif not re.fullmatch(password_regex, password):
            context = {'error': 'Use 8 or more characters with a mix of letters, numbers & symbols'}
            return render(request, 'register.html', context)
        else:
            user.set_password(confirm_password)
            user.save()
            user = authenticate(request, email=request.user, password=confirm_password)
            login(request, user)
            return redirect('password_change_done')


def handler404(request, exception):
    return render(request, '400.html')


def handler500(request):
    return render(request, '500.html')


@login_required(login_url='login')
def user_archive(request):
    if request.method == 'GET':
        user = CustomUser.objects.get(email=request.user)
        archive = Archive.objects.filter(user=user)
        context = {'archive': archive}
        return render(request, 'user_archive.html', context)
    if request.method == 'POST':
        return render(request, 'user_archive.html')


@login_required(login_url='login')
def user_archive_id(request, id):
    if request.method == 'GET':
        try:
            user = CustomUser.objects.get(email=request.user)
            archive = Archive.objects.get(id=id, user=user.id)
            context = {'content': archive.content,
                       'result': archive.result}
            return render(request, 'user_archive_id.html', context)
        except:
            context = {}
            return render(request, 'user_archive_id.html', context)
    if request.method == 'POST':
        data = json.loads(request.body)
        content = data['article']
        if not data['article']:
            return JsonResponse({'result': 'Enter Article'})
        result = spintax.result(content)
        user = CustomUser.objects.get(email=request.user)
        archive_save(user, content, result)
        context = {'result': result}
        return JsonResponse(context)


import base64


@api_view(['POST', 'GET'])
@csrf_exempt
@custom_login_required
def test(request, data=None):
    print(type(request))
    print(data)
    context = {}
    image_path = 'D:\spintax_app\KAIZEN.png'

    with open(image_path, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode('utf-8')

    context["image"] = image_data

    return render(request, 'test.html', context)


class TestClass(APIView):
    def get(self, request, id):
        return HttpResponse(id)


@csrf_exempt
def generate_unique_article(request):
    data = json.loads(request.body)
    content = data['generated_text']
    word_count = spintax.count_variations_within_braces(content)
    rewritten_text = spintax.rewrite_sentence(content)

    context = {'rewritten_text': rewritten_text,
               'word_count': word_count}
    return JsonResponse(context)


import time

import jwt
from datetime import datetime, timedelta


@api_view(['POST', 'GET'])
def token_generate(request):
    print(request.META['HTTP_AUTHORIZATION'])
    secret_key = 'my_secret_key'

    expiration_time = datetime.utcnow() + timedelta(seconds=1)
    payload = {
        'user_id': 1234,
        'username': 'john.doe',
        'exp': expiration_time
    }

    token = jwt.encode(payload, secret_key, algorithm='HS256')
    token = {'token': token}
    return JsonResponse(token)


@api_view(['POST', 'GET'])
def token_check(request):
    secret_key = 'my_secret_key'
    token = request.META['HTTP_AUTHORIZATION']

    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])
        print(decoded_token)
        print("Decoded Token:", decoded_token)

        expiration_time = datetime.fromtimestamp(decoded_token["exp"])
        current_time = datetime.utcnow()

        if current_time < expiration_time:
            print("Token is still valid.")
        else:
            raise jwt.ExpiredSignatureError("Token has expired.")


    except jwt.ExpiredSignatureError:
        print("Token has expired.")
        return JsonResponse({'response': 'Token has expired.'})


# @api_view(['POST'])
# def Login(request):
#     email = request.data.get('email')
#     password = request.data.get('password')
#     context = {}
#     print(email)
#     print(password)
#
#     if CustomUser.objects.filter(email=email).exists():
#         user = authenticate(request, email=email, password=password)
#         if user is not None:
#             context['response'] = True
#             context['message'] = 'login successfully'
#             context['token'] = user.token
#             return JsonResponse(context)
#
#     context['response'] = False
#     context['message'] = 'enter valid detail'
#     return JsonResponse(context)


# @api_view(['POST', 'GET'])
# def home(request):
#     context = {}
#     try:
#         token = request.META['HTTP_AUTHORIZATION'].split(' ')[1]
#         user = CustomUser.objects.get(token=token)
#
#         context['response'] = True
#         context['message'] = 'token valid'
#         return JsonResponse(context)
#
#     except:
#         context['response'] = False
#         context['message'] = 'token In valid'
#         return JsonResponse(context)


@api_view(['POST'])
def spin_article(request):
    context = {}

    article = request.data.get('article')
    print(article)

    generated_text = spintax.generate_spin_options(article)
    word_count = spintax.count_variations_within_braces(generated_text)
    rewritten_text = spintax.rewrite_sentence(generated_text)
    print(rewritten_text)
    context = {'generated_text': generated_text,
               'rewritten_text': rewritten_text,
               'word_count': word_count}

    return JsonResponse(context)


# @api_view(['POST'])
# def spin_article(request):
#     context = {}
#
#     article = request.data.get('article')
#     if article:
#
#         generated_text = spintax.generate_spin_options(article)
#         word_count = spintax.count_variations_within_braces(generated_text)
#         rewritten_text = spintax.rewrite_sentence(generated_text)
#         print(rewritten_text)
#         context = {
#             'response': True,
#             'generated_text': generated_text,
#             'rewritten_text': rewritten_text,
#             'word_count': word_count
#         }
#     else:
#         context = {
#             'response': False,
#             'message': 'enter article',
#
#         }
#
#     return JsonResponse(context)


# @api_view(['POST'])
# def spin_txt_file(request):
#     file = request.FILES.get('file', None)
#
#     if not file or not file.name.endswith('.txt'):
#         context = {
#             'response': False,
#             'result': 'Invalid file format. Only .txt files are allowed.'
#         }
#         return JsonResponse(context)
#
#     article = file.read().decode('utf-8')
#     if not article:
#         context = {
#             'response': False,
#             'message': 'enter article',
#
#         }
#         return JsonResponse(context)
#
#     generated_text = spintax.generate_spin_options(article)
#     word_count = spintax.count_variations_within_braces(generated_text)
#     rewritten_text = spintax.rewrite_sentence(generated_text)
#     context = {
#         'response': True,
#         'generated_text': generated_text,
#         'rewritten_text': rewritten_text,
#         'word_count': word_count
#     }
#     return JsonResponse(context)


# @api_view(['POST'])
# def spin_zip_file(request):
#     file = request.FILES.get('file', None)
#
#     if not file or not file.name.endswith('.zip'):
#         context = {
#             'response': False,
#             'result': 'Invalid file format. Only .zip files are allowed.'
#         }
#         return JsonResponse(context)
#
#     try:
#         article = zip_read(file)
#
#     except Exception as e:
#         return JsonResponse({'result': 'invalid zip'})
#
#     if not article:
#         context = {
#             'response': False,
#             'message': 'enter article',
#
#         }
#         return JsonResponse(context)
#     print(article)
#
#     generated_text = spintax.generate_spin_options(article)
#     word_count = spintax.count_variations_within_braces(generated_text)
#     rewritten_text = spintax.rewrite_sentence(generated_text)
#     context = {
#         'response': True,
#         'generated_text': generated_text,
#         'rewritten_text': rewritten_text,
#         'word_count': word_count
#     }
#     return JsonResponse(context)


def get_index(word_list):
    word_index_list = []
    for word in word_list:
        s_w = Synonyms.objects.get(word=word)
        word_index_list.append(s_w.id)
    print('*****', 'word_index_list', word_index_list)
    return word_index_list


@csrf_exempt
def spintax_chatgpt(request):
    string = '''
    The {next|upcoming} {tool|software|application} on my {list|agenda} is {Sakari|Sakari messaging platform}. {Sakari|It} is {also|likewise} a {SaaS-based|cloud-based} {text message|SMS} {service provider|platform} {similar to|just like} {Textdrip|Textdrip software}. The {tool|platform} is {also|additionally} {generously|positively} {reviewed|rated|evaluated} on {Capterra|Capterra's website} for its {ease of use|user-friendly interface}, {customer service|client support}, and {features|functionality} it {offers|provides}.

    {Talking|Discussing|Speaking} about {features|functionalities}, {Sakari|the Sakari messaging platform} {offers|provides} {unlimited|limitless} {contact|recipient} {imports|uploads}, {2-way|bidirectional} messaging, {campaigns|marketing campaigns}, {MMS|multimedia messaging} {messaging|communication}, and {others|additional} {similar to|comparable to} {Textdrip|Textdrip software}. {Even though|Although|Despite the fact that} the {tool|platform} {offers|provides} {several|various} {business|enterprise} {text message|SMS} {messaging|communication} {features|functionalities} like {reminders|notifications}, {alerts|notifications}, and {confirmations|acknowledgments}, it still {lags behind|falls short} in {many|numerous|several} {capabilities|features} {compared to|when compared to|in comparison to} {Textdrip|Textdrip software}.
    '''

    pattern = r'{(.*?)}'
    substrings = re.findall(pattern, string)
    split_substrings = [substring.split('|') for substring in substrings]
    print(split_substrings)

    for i in split_substrings:
        for j in i:
            # print(j)
            if not Synonyms.objects.filter(word=j).exists():
                s = Synonyms(word=j, synonyms_list=[])
                s.save()

    for i in split_substrings:
        print('-----------------------------------------------------')
        print('i', i)
        for j in i:
            print('j', j)

            word_list = copy.deepcopy(i)

            word_list.remove(j)
            print('word_list', word_list)
            synonyms = Synonyms.objects.get(word=j)
            print('synonyms----ID', synonyms.id, synonyms.word)

            word_index_list = get_index(word_list)
            synonyms_word_index = synonyms.synonyms_list

            for w_i in word_index_list:
                print(w_i)
                if w_i not in synonyms_word_index:
                    synonyms_word_index.append(w_i)
            synonyms.synonyms_list = synonyms_word_index
            synonyms.save()

            print('---------------', synonyms_word_index)

    return HttpResponse('abc')


@api_view(['POST'])
def data_collection(request):
    input_text = request.data.get('input_text')
    output_text = request.data.get('output_text')

    if input_text and output_text:
        pattern = r'{(.*?)}'
        substrings = re.findall(pattern, output_text)
        split_substrings = [substring.split('|') for substring in substrings]

        spin_paraphrase = SpinParaphrase(input_text=input_text, output_text=output_text)
        spin_paraphrase.save()

        if split_substrings:

            nlp = spacy.load('en_core_web_sm')
            doc = nlp(input_text)
            words_meaning = []
            synonyms_words = []

            for token in doc:
                if token.pos_ == "VERB" or token.pos_ == "NOUN" or token.pos_ == "ADJ":
                    words_meaning.append([token.text, token.pos_])
                synonyms_words = []

                ind = 0
                w_m_l = len(words_meaning)

                indexed = [i for i in range(len(split_substrings))]

                for c, i in enumerate(split_substrings):
                    for j in range(ind, w_m_l):
                        if words_meaning[j][0] in i:
                            indexed[c] = None
                            ind = j
                            synonyms_words.append([words_meaning[j][1], i])
                            break

                for i in indexed:
                    if i:
                        synonyms_words.append(['satellite', split_substrings[i]])

            for word in synonyms_words:
                data_collection = DataCollection(words=word[1], pos=word[0])
                data_collection.save()

    return JsonResponse({'response': True})


@api_view(['GET', 'POST'])
def rewrite2(request):
    context = {'input_text': request.data.get('input_text'),
               'generated_text': 'generated_text',
               'rewritten_text': 'rewritten_text'
               }

    return JsonResponse(context)


@csrf_exempt
def test1(request):
    print('------------------------------------------------------------')
    search_values = ["addition", "tool", "choice", "option"]
    search_values = ["choice", "addition"]
    search_values = ["booking", " reserving", " scheduling"]

    # Start with an empty Q object
    query = Q()

    # Build the query dynamically using a loop
    for value in search_values:
        query |= Q(words__contains=value)

    # Execute the query to get the matching rows
    matching_rows = DataCollection.objects.filter(query)
    print(matching_rows, len(matching_rows))

    # Print the matching rows
    for row in matching_rows:
        print(row.words)

    # query = Q(words__icontains="Textdrip")
    #
    # matching_rows = DataCollection.objects.filter(query)
    #
    #
    # word_set = set()
    # for row in matching_rows:
    #     # print(row.words)
    #     for word in row.words:
    #         word_set.add(word)
    # print(word_set)
    return HttpResponse('test1')

from django.shortcuts import redirect, render
from django.views.generic import View
from django.contrib import messages

from .models import ContactUs, FeedBack
from .forms import ContactForm, FeedBackForm

def returnUserRequestData(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    try:
        os = str(request.META.get('OS'))
    except:
        os = ''
    return ip.strip(), os.strip()

class ContactUsView(View):
    template_name = "contact/contactus.html"
    context = {'form':ContactForm(), }
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)
    def post(self, request, *args, **kwargs):
        contact_form = ContactForm(self.request.POST or None)
        if contact_form.is_valid() and request.method == 'POST':
            name = contact_form.cleaned_data['name'] 
            email = contact_form.cleaned_data['email'] 
            subject = contact_form.cleaned_data['subject'] 
            message = contact_form.cleaned_data['message'] 
            user_ipaddress,user_os = returnUserRequestData(request)
            ContactUs.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message,
                user_ipaddress=user_ipaddress,
                user_os=user_os,
                )
            messages.info(request, "Your Message Sent Successfully")
        else:
            messages.info(request, "Your Message Sent Failed. Please Check All Fields")
        return render(request, self.template_name, self.context)



class FeedbackView(View):
    template_name = "contact/feedback.html"
    context = {'form':FeedBackForm(), }
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)
    def post(self, request, *args, **kwargs):
        feedback_form = FeedBackForm(self.request.POST or None)
        if feedback_form.is_valid() and request.method == 'POST':
            name = feedback_form.cleaned_data['name'] 
            email = feedback_form.cleaned_data['email'] 
            subject = feedback_form.cleaned_data['subject'] 
            message = feedback_form.cleaned_data['message'] 
            user_ipaddress,user_os = returnUserRequestData(request)
            FeedBack.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message,
                user_ipaddress=user_ipaddress,
                user_os=user_os,
                )
            messages.info(request, "Thank you for your Feedback.")
        else:
            messages.info(request, "Failed to submit your feedback. Please Check All Fields and try again.")
        return render(request, self.template_name, self.context)


def error_404(request, *args, **argv): return render(request, 'pages/404.html', status=404)
def error_500(request, *args, **argv): return render(request, 'pages/500.html', status=500)

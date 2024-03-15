from django import forms
from .models import ContactUs, FeedBack

class ContactForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Enter Name",
        "required": "required",
        'class':'form-control',
    }), label="Full name:")
  
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "required": "required",
        "placeholder": "Enter Your Email",
        'class':'form-control',

    }), label="Email")

    subject = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Subject",
        "required": "required",
        'class':'form-control',
    }), label="Subject")
  
    message = forms.CharField(widget=forms.Textarea(attrs={
        "placeholder": "Message",
        "required": "required",
        'class':'form-control',
    }), label="Message")

    class Meta:
        model = ContactUs
        fields = ('name', 'email', 'subject', 'message',)

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['subject'].initial = "General Query"


class FeedBackForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Enter Name",
        "required": "required",
        'class':'form-control',
    }), label="Full name:")
  
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        "required": "required",
        "placeholder": "Enter Your Email",
        'class':'form-control',

    }), label="Email")

    subject = forms.CharField(widget=forms.TextInput(attrs={
        "placeholder": "Subject",
        "required": "required",
        'class':'form-control',
    }), label="Subject")
  
    message = forms.CharField(widget=forms.Textarea(attrs={
        "placeholder": "Message",
        "required": "required",
        'class':'form-control',
    }), label="Message")

    class Meta:
        model = FeedBack
        fields = ('name', 'email', 'subject', 'message',)

    def __init__(self, *args, **kwargs):
        super(FeedBackForm, self).__init__(*args, **kwargs)
        self.fields['subject'].initial = "General Query"
from django import forms
from django.utils import timezone

from .models import ContactMessage, Enquiry


class EnquiryForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event_date"].required = True
        self.fields["guests"].required = True
        self.fields["event_date"].widget.attrs["min"] = timezone.localdate().isoformat()

    class Meta:
        model = Enquiry
        fields = ["name", "phone", "email", "event_type", "event_date", "guests", "message"]
        labels = {
            "name": "Your name",
            "phone": "Phone / WhatsApp",
            "email": "Email (optional)",
            "event_type": "Type of event",
            "event_date": "Date",
            "guests": "Number of guests",
            "message": "Anything else? (optional)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Thandi Nkosi", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"placeholder": "e.g. 072 000 0000", "autocomplete": "tel", "type": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "event_date": forms.DateInput(attrs={"type": "date"}),
            "guests": forms.NumberInput(attrs={"min": 1, "placeholder": "e.g. 40"}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Braai packages, DJ, decor, VIP area..."}),
        }



class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "phone", "email", "message"]
        labels = {
            "name": "Your name",
            "phone": "Phone / WhatsApp",
            "email": "Email (optional)",
            "message": "Your message",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Thandi Nkosi", "autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"placeholder": "e.g. 072 000 0000", "autocomplete": "tel", "type": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "you@example.com", "autocomplete": "email"}),
            "message": forms.Textarea(attrs={"rows": 4, "placeholder": "Ask us anything: prices, packages, events..."}),
        }

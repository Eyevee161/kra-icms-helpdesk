from django import forms
from .models import Ticket, Category, Priority, TicketComment, TicketAttachment


class TicketSubmitForm(forms.ModelForm):
    attachment = forms.FileField(required=False, help_text="Optional supporting document (PDF, image, max 5MB)")

    class Meta:
        model = Ticket
        fields = [
            "subject",
            "description",
            "category",
            "priority",
            "taxpayer_name",
            "taxpayer_email",
            "taxpayer_phone",
            "kra_pin",
            "id_number",
        ]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Brief summary of the issue"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5, "placeholder": "Describe the problem in detail..."}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "taxpayer_name": forms.TextInput(attrs={"class": "form-control"}),
            "taxpayer_email": forms.EmailInput(attrs={"class": "form-control"}),
            "taxpayer_phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 0712 345 678"}),
            "kra_pin": forms.TextInput(attrs={"class": "form-control", "placeholder": "A000000000X"}),
            "id_number": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.filter(is_active=True)
        self.fields["priority"].queryset = Priority.objects.all()


class TicketTrackForm(forms.Form):
    ticket_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. KRA-ICMS-20261102-0001"}),
        label="Ticket Number",
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={"class": "form-control"}),
        label="Email used when submitting",
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ["body", "is_internal"]
        widgets = {
            "body": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "is_internal": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class AssignTicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["assigned_to", "status", "priority"]
        widgets = {
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.Select(attrs={"class": "form-select"}),
        }

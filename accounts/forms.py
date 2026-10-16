from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class _StyledFormMixin:
    """Injecte les classes du design system + ARIA d'erreur (sans JS)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault("class", "field__input")
            if self.is_bound and name in (self.errors or {}):
                field.widget.attrs["aria-invalid"] = "true"
                field.widget.attrs["aria-describedby"] = f"id_{name}-msg"


class StyledLoginForm(_StyledFormMixin, AuthenticationForm):
    pass


class SignupForm(_StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

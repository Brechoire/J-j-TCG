from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View

from .forms import SignupForm
from .models import PlayerProfile


class SignupView(View):
    def get(self, request):
        return render(request, "accounts/signup.html", {"form": SignupForm()})

    def post(self, request):
        form = SignupForm(request.POST)
        if not form.is_valid():
            return render(request, "accounts/signup.html", {"form": form}, status=400)
        user = form.save()
        PlayerProfile.objects.get_or_create(user=user)
        login(request, user)
        return redirect("accounts:profile")


@method_decorator(login_required, name="dispatch")
class ProfileView(View):
    def get(self, request):
        profile, _ = PlayerProfile.objects.get_or_create(user=request.user)
        return render(request, "accounts/profile.html", {"profile": profile})

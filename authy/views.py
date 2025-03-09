from django.views import View
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.conf import settings
from msal import ConfidentialClientApplication
import requests

class AzureLoginView(View):
    """Redirects users to Microsoft's authentication URL."""

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("home")
        else:
            return render(request, "login.html")
    
class AzureSSOView(View):
    """Redirects users to Microsoft's authentication URL."""

    def get(self, request):
        msal_app = ConfidentialClientApplication(
            settings.AZURE_AD["CLIENT_ID"],
            authority=settings.AZURE_AD["AUTHORITY"],
            client_credential=settings.AZURE_AD["CLIENT_SECRET"],
        )
        auth_url = msal_app.get_authorization_request_url(
            settings.AZURE_AD["SCOPES"],
            redirect_uri=settings.AZURE_AD["REDIRECT_URI"],
        )
        return redirect(auth_url)

class AzureCallbackView(View):
    """Handles authentication response from Microsoft and logs the user in."""

    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return render(request, "error.html", {"message": "Authentication failed"})

        msal_app = ConfidentialClientApplication(
            settings.AZURE_AD["CLIENT_ID"],
            authority=settings.AZURE_AD["AUTHORITY"],
            client_credential=settings.AZURE_AD["CLIENT_SECRET"],
        )
        
        token_response = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=settings.AZURE_AD["SCOPES"],
            redirect_uri=settings.AZURE_AD["REDIRECT_URI"],
        )

        if "access_token" in token_response:
            user_info = self.get_user_info(token_response["access_token"])

            user, created = User.objects.update_or_create(
                username=user_info["mail"] or user_info["userPrincipalName"],
                defaults={
                    "email": user_info["mail"] or user_info["userPrincipalName"],
                    "first_name": user_info.get("givenName", ""),
                    "last_name": user_info.get("surname", ""),
                },
            )

            login(request, user)
            return redirect("home")

        return render(request, "error.html", {"message": "Failed to authenticate"})

    def get_user_info(self, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
        return response.json()

class AzureLogoutView(View):
    def get(self, request):
        logout(request)
        return redirect("azure_login")
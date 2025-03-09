from django.urls import path
from .views import (
    AzureLoginView, 
    AzureCallbackView, 
    AzureLogoutView,
    AzureSSOView
)

urlpatterns = [
    path("login", AzureLoginView.as_view(), name="azure_login"),
    path("sso_login", AzureSSOView.as_view(), name="azure_sso"),
    path("auth/callback", AzureCallbackView.as_view(), name="azure_callback"),
    path("logout", AzureLogoutView.as_view(), name="azure_logout")
]

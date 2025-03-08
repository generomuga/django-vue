from django.urls import path
from .views import AzureLoginView, AzureCallbackView, HomeView

urlpatterns = [
    path("login/", AzureLoginView.as_view(), name="azure_login"),
    path("callback/", AzureCallbackView.as_view(), name="azure_callback"),
    path("logout/", AzureCallbackView.as_view(), name="azure_logout"),
    path("home/", HomeView.as_view(), name="home"),
]

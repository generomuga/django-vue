from django.core.management.base import BaseCommand
import requests
from django.conf import settings
from msal import ConfidentialClientApplication
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Syncs users from Azure Active Directory to Django'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting Azure AD sync...')
        
        # Step 1: Get Access Token
        token = self.get_access_token()
        
        # Step 2: Sync Users
        self.sync_azure_users(token)

        self.stdout.write(self.style.SUCCESS('Successfully synced Azure AD users'))

    def get_access_token(self):
        app = ConfidentialClientApplication(
            settings.AZURE_AD["CLIENT_ID"],
            authority=settings.AZURE_AD["AUTHORITY"],
            client_credential=settings.AZURE_AD["CLIENT_SECRET"],
        )
        token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        return token["access_token"]

    def sync_azure_users(self, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{settings.AZURE_AD['GRAPH_API_URL']}/users", headers=headers)

        print (response.json())
        if response.status_code == 200:
            users = response.json().get("value", [])
            for user_data in users:
                user, created = User.objects.update_or_create(
                    username=user_data["userPrincipalName"],
                    defaults={
                        "email": user_data["userPrincipalName"],
                        "first_name": user_data["givenName"] if user_data.get("givenName") else user_data.get("displayName"),
                        "last_name": user_data["surname"] if user_data.get("surname") else user_data.get("displayName"),
                        "is_staff": True,
                    },
                )
                if created:
                    self.stdout.write(f"Created user: {user.username}")
                else:
                    self.stdout.write(f"Updated user: {user.username}")
        else:
            self.stdout.write(self.style.ERROR("Failed to fetch users"))
            self.stdout.write(response.text)

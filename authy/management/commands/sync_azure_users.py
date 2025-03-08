from django.core.management.base import BaseCommand
import requests
from django.conf import settings
from msal import ConfidentialClientApplication
from django.contrib.auth.models import User, Group

class Command(BaseCommand):
    help = 'Syncs users and groups from Azure Active Directory to Django'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting Azure AD sync...')
        
        # Step 1: Get Access Token
        token = self.get_access_token()
        
        # Step 2: Sync Users
        self.sync_azure_users(token)
        
        # Step 3: Sync Groups
        self.sync_azure_groups(token)
        
        # Step 4: Assign Users to Groups
        self.assign_users_to_groups(token)

        self.stdout.write(self.style.SUCCESS('Successfully synced Azure AD users and groups'))

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

    def sync_azure_groups(self, token):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{settings.AZURE_AD['GRAPH_API_URL']}/groups", headers=headers)

        if response.status_code == 200:
            groups = response.json().get("value", [])
            for group_data in groups:
                # Create or update group in Django
                group, created = Group.objects.update_or_create(
                    name=group_data["displayName"]
                )
                if created:
                    self.stdout.write(f"Created group: {group.name}")
                else:
                    self.stdout.write(f"Updated group: {group.name}")
        else:
            self.stdout.write(self.style.ERROR("Failed to fetch groups"))
            self.stdout.write(response.text)

    def assign_users_to_groups(self, token):
        headers = {"Authorization": f"Bearer {token}"}
        
        # Fetch all groups first
        groups_response = requests.get(f"{settings.AZURE_AD['GRAPH_API_URL']}/groups", headers=headers)

        if groups_response.status_code == 200:
            groups = groups_response.json().get("value", [])
            
            for group_data in groups:
                group_name = group_data["displayName"]
                group = Group.objects.filter(name=group_name).first()
                
                if group:
                    group_id = group_data["id"]
                    members_response = requests.get(
                        f"{settings.AZURE_AD['GRAPH_API_URL']}/groups/{group_id}/members", 
                        headers=headers
                    )

                    if members_response.status_code == 200:
                        members = members_response.json().get("value", [])
                        for member_data in members:
                            # Fetch the corresponding user in Django
                            user = User.objects.filter(username=member_data["userPrincipalName"]).first()
                            
                            if user:
                                # Add the user to the group
                                group.user_set.add(user)
                                self.stdout.write(f"Added user {user.username} to group {group.name}")
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to fetch members for group {group_name}"))
                        self.stdout.write(members_response.text)
                else:
                    self.stdout.write(self.style.WARNING(f"Group {group_name} not found in Django"))
        else:
            self.stdout.write(self.style.ERROR("Failed to fetch groups"))
            self.stdout.write(groups_response.text)

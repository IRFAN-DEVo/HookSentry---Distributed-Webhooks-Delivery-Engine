import pytest
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.workspaces.models import Workspace, WorkspaceMember, APIKey

@pytest.mark.django_db
class TestAuthAndWorkspaces:
    def setup_method(self):
        self.client = APIClient()

    def test_user_registration_creates_workspace_and_owner(self):
        payload = {
            'email': 'alice@example.com',
            'full_name': 'Alice Engineer',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!'
        }
        response = self.client.post('/api/v1/auth/register/', payload)
        assert response.status_code == 201
        data = response.json()
        assert 'tokens' in data
        assert data['user']['email'] == 'alice@example.com'
        assert data['workspace']['role'] == 'OWNER'

        # Verify database entities
        user = User.objects.get(email='alice@example.com')
        assert user.check_password('StrongPassword123!')
        membership = WorkspaceMember.objects.get(user=user)
        assert membership.role == WorkspaceMember.Role.OWNER

    def test_login_returns_jwt_tokens(self):
        user = User.objects.create_user(
            email='bob@example.com',
            password='SecurePassword123!',
            full_name='Bob Developer'
        )
        ws = Workspace.objects.create(name="Bob's Workspace", slug='bob-ws-1')
        WorkspaceMember.objects.create(workspace=ws, user=user, role=WorkspaceMember.Role.OWNER)

        response = self.client.post('/api/v1/auth/login/', {
            'email': 'bob@example.com',
            'password': 'SecurePassword123!'
        })
        assert response.status_code == 200
        data = response.json()
        assert 'tokens' in data
        assert 'access' in data['tokens']
        assert 'refresh' in data['tokens']
        assert data['user']['email'] == 'bob@example.com'

    def test_cross_workspace_isolation(self):
        # Create User A and Workspace A
        user_a = User.objects.create_user(email='user_a@example.com', password='Password123!')
        ws_a = Workspace.objects.create(name='Workspace A', slug='ws-a')
        WorkspaceMember.objects.create(workspace=ws_a, user=user_a, role=WorkspaceMember.Role.OWNER)

        # Create User B and Workspace B
        user_b = User.objects.create_user(email='user_b@example.com', password='Password123!')
        ws_b = Workspace.objects.create(name='Workspace B', slug='ws-b')
        WorkspaceMember.objects.create(workspace=ws_b, user=user_b, role=WorkspaceMember.Role.OWNER)

        # Authenticate as User A
        self.client.force_authenticate(user=user_a)

        # User A cannot retrieve Workspace B
        resp = self.client.get(f'/api/v1/workspaces/{ws_b.id}/')
        assert resp.status_code == 404

        # Listing workspaces shows only Workspace A
        list_resp = self.client.get('/api/v1/workspaces/')
        assert list_resp.status_code == 200
        results = list_resp.json()['results']
        assert len(results) == 1
        assert results[0]['id'] == str(ws_a.id)

    def test_api_key_generation_and_authentication(self):
        user = User.objects.create_user(email='dev@example.com', password='Password123!')
        ws = Workspace.objects.create(name='Dev Workspace', slug='dev-ws')
        WorkspaceMember.objects.create(workspace=ws, user=user, role=WorkspaceMember.Role.OWNER)

        self.client.force_authenticate(user=user)
        resp = self.client.post('/api/v1/api-keys/', {
            'name': 'CI/CD Pipeline Key'
        }, HTTP_X_WORKSPACE_ID=str(ws.id))

        assert resp.status_code == 201
        data = resp.json()
        raw_key = data['raw_key']
        assert raw_key.startswith('hk_live_')

        # Clear session auth
        self.client.force_authenticate(user=None)

        # Make authenticated call using raw API key header
        api_client = APIClient()
        api_client.credentials(HTTP_X_API_KEY=raw_key)

        # Access audit logs with API Key
        audit_resp = api_client.get('/api/v1/audit-logs/')
        assert audit_resp.status_code == 200


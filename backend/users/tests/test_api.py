import pytest

from users.models import User
from users.tests.factories import DEFAULT_PASSWORD, UserFactory

pytestmark = pytest.mark.django_db


class TestProfile:
    def test_get_own_profile(self, staff_client, staff_user):
        response = staff_client.get('/api/users/profile/')
        assert response.status_code == 200
        assert response.data['email'] == staff_user.email

    def test_update_own_profile_but_not_role_or_email(self, staff_client, staff_user):
        response = staff_client.patch('/api/users/profile/', {
            'phone_number': '555-0101', 'role': 'admin', 'email': 'new@example.com',
        }, format='json')

        assert response.status_code == 200
        staff_user.refresh_from_db()
        assert staff_user.phone_number == '555-0101'
        assert staff_user.role == User.STAFF
        assert staff_user.email != 'new@example.com'


class TestUserManagement:
    def test_list_is_a_plain_list_without_guardian_anonymous_user(self, admin_client, admin_user):
        response = admin_client.get('/api/users/')

        assert response.status_code == 200
        assert isinstance(response.data, list)
        assert 'AnonymousUser' not in [u['email'] for u in response.data]

    def test_admin_creates_user_with_role(self, admin_client):
        response = admin_client.post('/api/users/', {
            'username': 'newmgr', 'email': 'newmgr@example.com', 'password': 'Mgr!Passw0rd',
            'first_name': 'New', 'last_name': 'Manager', 'role': 'manager',
        }, format='json')

        assert response.status_code == 201
        assert User.objects.get(email='newmgr@example.com').role == User.MANAGER

    def test_staff_cannot_create_users(self, staff_client):
        response = staff_client.post('/api/users/', {'email': 'x@example.com'}, format='json')
        assert response.status_code == 403

    def test_staff_cannot_promote_themselves(self, staff_client, staff_user):
        staff_client.patch(f'/api/users/{staff_user.id}/', {'role': 'admin', 'first_name': 'Changed'},
                           format='json')

        staff_user.refresh_from_db()
        assert staff_user.role == User.STAFF
        assert staff_user.first_name == 'Changed'

    def test_staff_cannot_edit_someone_else(self, staff_client):
        other = UserFactory()
        response = staff_client.patch(f'/api/users/{other.id}/', {'first_name': 'Hacked'}, format='json')
        assert response.status_code == 403

    def test_admin_changes_roles(self, admin_client, staff_user):
        response = admin_client.patch(f'/api/users/{staff_user.id}/', {'role': 'manager'}, format='json')
        assert response.status_code == 200
        staff_user.refresh_from_db()
        assert staff_user.role == User.MANAGER

    def test_only_admin_deletes_users(self, admin_client, staff_client, staff_user):
        assert staff_client.delete(f'/api/users/{staff_user.id}/').status_code == 403
        assert admin_client.delete(f'/api/users/{staff_user.id}/').status_code == 204

    def test_team_members_lists_active_staff_only(self, manager_client):
        active = UserFactory(role=User.STAFF)
        UserFactory(role=User.STAFF, is_active=False)
        UserFactory(role=User.MANAGER)

        response = manager_client.get('/api/users/team-members/')
        assert [u['id'] for u in response.data] == [active.id]


class TestChangePassword:
    URL = '/api/auth/change-password/'

    def test_changes_password(self, staff_client, staff_user):
        response = staff_client.post(self.URL, {
            'current_password': DEFAULT_PASSWORD, 'new_password': 'Brand!New1234',
        }, format='json')

        assert response.status_code == 200
        staff_user.refresh_from_db()
        assert staff_user.check_password('Brand!New1234')

    def test_wrong_current_password(self, staff_client):
        response = staff_client.post(self.URL, {
            'current_password': 'wrong', 'new_password': 'Brand!New1234',
        }, format='json')
        assert response.status_code == 400

    def test_weak_new_password(self, staff_client):
        response = staff_client.post(self.URL, {
            'current_password': DEFAULT_PASSWORD, 'new_password': '123',
        }, format='json')
        assert response.status_code == 400

    def test_old_duplicate_endpoint_is_gone(self, staff_client, staff_user):
        response = staff_client.post(f'/api/users/{staff_user.id}/change_password/', {}, format='json')
        assert response.status_code == 404

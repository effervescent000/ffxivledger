import pytest
from flask_login import current_user

from ffxivledger.models import User


@pytest.mark.parametrize('username,password', [
    ('a_user', 'a_password')
])
def test_sign_up(client, username, password):
    data = {
        'name': username, 'password': password, 'confirm_password' : password, 'submit': True
    }
    num_users = len(User.query.all())

    assert client.get('/auth/signup').status_code == 200

    client.post('/auth/signup', data=data)
    assert len(User.query.all()) == num_users + 1


@pytest.mark.parametrize('username,password,message', [
    ('a_user', 'aaa', b'Choose a longer password')
])
def test_sign_up_validate(client, username, password, message):
    data = {
        'name': username, 'password': password, 'submit': True
    }
    response = client.post('/auth/signup', data=data)
    assert message in response.data

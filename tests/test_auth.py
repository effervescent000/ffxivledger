import pytest
from flask_login import current_user

from ffxivledger.models import User


@pytest.mark.parametrize('username,password', [
    ('a_user', 'a_password')
])
def test_sign_up(client, username, password):
    data = {
        'username': username, 'password': password, 'confirm_password': password, 'submit': True
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
        'username': username, 'password': password, 'confirm_password': password, 'submit': True
    }
    response = client.post('/auth/signup', data=data)
    assert message in response.data


# the problem here is that these are redirecting, rather than just rendering a template directly, so the response
# is the "Redirecting..." page which doesn't have the info I'm looking for, I'm not sure how to make it display this
@pytest.mark.parametrize('username,password', [('Admin', 'testing_')])
def test_login(client, username, password):
    data = {
        'username': username, 'password': password, 'submit': True
    }
    assert client.get('/auth/login').status_code == 200

    response = client.post('/auth/login', data=data)
    # assert response.status_code == 302


@pytest.mark.parametrize('username,password,message', [
    ('a_user', 'a_password', b'Invalid username/password combination')
])
def test_login_validation(client, username, password, message):
    data = {
        'username': username, 'password': password, 'submit': True
    }
    response = client.post('/auth/login', data=data)
    assert message in response.data

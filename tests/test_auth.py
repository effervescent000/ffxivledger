import pytest
from wtforms import ValidationError


def test_sign_up(client):
    assert client.get('/auth/signup').status_code == 200


@pytest.mark.parametrize('username,password,message', [
    ('aaaaaaaaa', 'aaa', b'Choose a longer password')
])
def test_sign_up_validate(client, username, password, message):
    data = {
        'name': username, 'password': password
    }
    response = client.post('/auth/signup', data=data)
    assert message in response.data

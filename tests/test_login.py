def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_valid_admin_login(client):
    response = client.post(
        '/login',
        data={'username': 'admin', 'password': 'adminpass'},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_valid_user_login(client):
    response = client.post(
        '/login',
        data={'username': 'testuser', 'password': 'userpass'},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_invalid_password_shows_error(client):
    response = client.post(
        '/login',
        data={'username': 'admin', 'password': 'wrongpassword'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


def test_nonexistent_user_shows_error(client):
    response = client.post(
        '/login',
        data={'username': 'nobody', 'password': 'pass'},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


# def test_register_page_loads(client):
#     response = client.get('/register')
#     assert response.status_code == 200


# def test_register_new_user(client):
#     response = client.post(
#         '/register',
#         data={'username': 'newuser', 'password': 'newpass', 'role': 'user'},
#         follow_redirects=True,
#     )
#     assert response.status_code == 200


# def test_register_duplicate_username_shows_error(client):
#     response = client.post(
#         '/register',
#         data={'username': 'admin', 'password': 'somepass', 'role': 'user'},
#         follow_redirects=True,
#     )
#     assert response.status_code == 200
#     assert b'Username already exists' in response.data


def test_logout_redirects_to_login(client):
    client.post('/login', data={'username': 'admin', 'password': 'adminpass'})
    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200


def test_admin_route_requires_admin_role(client):
    with client.session_transaction() as sess:
        sess['role'] = 'user'
        sess['username'] = 'testuser'
    response = client.get('/admin', follow_redirects=True)
    assert response.status_code == 200
    assert b'Access denied' in response.data


def test_admin_route_accessible_to_admin(client):
    with client.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['username'] = 'admin'
    response = client.get('/admin')
    assert response.status_code == 200


def test_user_route_blocked_when_not_logged_in(client):
    response = client.get('/user', follow_redirects=True)
    assert response.status_code == 200
    assert b'Access denied' in response.data


def test_user_route_accessible_when_logged_in(client):
    with client.session_transaction() as sess:
        sess['username'] = 'testuser'
    response = client.get('/user')
    assert response.status_code == 200

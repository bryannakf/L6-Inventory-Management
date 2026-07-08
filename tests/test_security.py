from werkzeug.security import check_password_hash


def test_session_cookie_security_flags(app):
	assert app.config['SESSION_COOKIE_HTTPONLY'] is True
	assert app.config['SESSION_COOKIE_SECURE'] is True
	assert app.config['SESSION_COOKIE_SAMESITE'] == 'Lax'


def test_login_sets_secure_session_cookie(client):
	response = client.post(
		'/login',
		data={'username': 'admin', 'password': 'adminpass'},
	)

	cookie_header = response.headers.get('Set-Cookie', '')

	assert response.status_code == 302
	assert 'HttpOnly' in cookie_header
	assert 'Secure' in cookie_header
	assert 'SameSite=Lax' in cookie_header


def test_change_password_requires_login(client):
	response = client.get('/change-password')

	assert response.status_code == 302
	assert response.headers['Location'].endswith('/login')


def test_forced_password_change_redirects_to_change_password(client, app):
	import app as app_module

	db = app_module.get_db()
	db.execute(
		'UPDATE users SET must_change_password = 1 WHERE username = ?',
		('admin',),
	)
	db.commit()

	response = client.post(
		'/login',
		data={'username': 'admin', 'password': 'adminpass'},
	)

	assert response.status_code == 302
	assert response.headers['Location'].endswith('/change-password')

	with client.session_transaction() as sess:
		assert sess['user_id'] == 1
		assert sess['role'] == 'admin'


def test_change_password_rejects_mismatch(client):
	with client.session_transaction() as sess:
		sess['user_id'] = 1
		sess['username'] = 'admin'
		sess['role'] = 'admin'

	response = client.post(
		'/change-password',
		data={'password': 'NewPass123', 'confirm_password': 'WrongPass123'},
		follow_redirects=True,
	)

	assert response.status_code == 200
	assert b'Passwords do not match.' in response.data


def test_change_password_updates_hash_and_clears_force_reset(client, app):
	import app as app_module

	db = app_module.get_db()
	db.execute(
		'UPDATE users SET must_change_password = 1 WHERE id = ?',
		(1,),
	)
	db.commit()

	with client.session_transaction() as sess:
		sess['user_id'] = 1
		sess['username'] = 'admin'
		sess['role'] = 'admin'

	response = client.post(
		'/change-password',
		data={'password': 'NewPass123', 'confirm_password': 'NewPass123'},
	)

	row = db.execute(
		'SELECT password, must_change_password FROM users WHERE id = ?',
		(1,),
	).fetchone()

	assert response.status_code == 302
	assert response.headers['Location'].endswith('/admin')
	assert row['must_change_password'] == 0
	assert check_password_hash(row['password'], 'NewPass123')


def test_logout_clears_session_and_redirects(client):
	with client.session_transaction() as sess:
		sess['user_id'] = 1
		sess['username'] = 'admin'
		sess['role'] = 'admin'

	response = client.get('/logout')

	assert response.status_code == 302
	assert response.headers['Location'].endswith('/login')

	with client.session_transaction() as sess:
		assert 'user_id' not in sess
		assert 'username' not in sess
		assert 'role' not in sess


def test_admin_route_redirects_non_admin_to_login(client):
	with client.session_transaction() as sess:
		sess['user_id'] = 2
		sess['username'] = 'testuser'
		sess['role'] = 'user'

	response = client.get('/admin', follow_redirects=True)

	assert response.status_code == 200
	assert b'Access denied' in response.data


def test_deleted_items_endpoint_requires_login(client):
	response = client.get('/api/items/deleted')

	assert response.status_code == 302
	assert response.headers['Location'].endswith('/login')


def test_deleted_items_endpoint_forbids_non_admin(client):
	with client.session_transaction() as sess:
		sess['user_id'] = 2
		sess['username'] = 'testuser'
		sess['role'] = 'user'

	response = client.get('/api/items/deleted')

	assert response.status_code == 403
	assert response.get_json() == {'error': 'Forbidden'}


def test_login_rejects_sql_injection_attempt(client):
	response = client.post(
		'/login',
		data={
			'username': "admin' OR '1'='1",
			'password': 'anything',
		},
		follow_redirects=True,
	)

	assert response.status_code == 200
	assert b'Invalid username or password.' in response.data

	with client.session_transaction() as sess:
		assert 'user_id' not in sess
		assert 'username' not in sess
		assert 'role' not in sess


def test_login_rate_limit_returns_429(client):
	import app as app_module

	app_module.limiter.reset()

	for _ in range(15):
		response = client.post(
			'/login',
			data={'username': 'admin', 'password': 'wrongpassword'},
		)
		assert response.status_code == 302

	response = client.post(
		'/login',
		data={'username': 'admin', 'password': 'wrongpassword'},
	)

	assert response.status_code == 429

import json


def test_add_datacenter_returns_201(client):
    response = client.post(
        '/api/datacenter',
        json={'location': 'New York', 'capacity': 1000},
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Data Center added successfully'


def test_add_datacenter_missing_fields_returns_400(client):
    response = client.post('/api/datacenter', json={'location': 'Berlin'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_add_datacenter_empty_body_returns_400(client):
    response = client.post('/api/datacenter', json={})
    assert response.status_code == 400


def test_get_datacenters_returns_200(client):
    response = client.get('/api/datacenters')
    assert response.status_code == 200


def test_get_datacenters_returns_list(client):
    response = client.get('/api/datacenters')
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_get_datacenters_contains_seeded_datacenter(client):
    response = client.get('/api/datacenters')
    data = json.loads(response.data)
    assert len(data) >= 1
    locations = [dc['location'] for dc in data]
    assert 'Test DC' in locations


def test_update_datacenter_returns_200(client):
    response = client.put('/api/datacenter/1', json={'capacity': 999})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Data Center updated successfully'


def test_update_datacenter_missing_capacity_returns_400(client):
    response = client.put('/api/datacenter/1', json={'location': 'Tokyo'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_delete_datacenter_returns_200(client):
    response = client.delete('/api/datacenter/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Data Center deleted successfully'

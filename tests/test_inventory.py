import json


def test_add_item_returns_201(client):
    response = client.post(
        '/api/item',
        json={'itemName': 'Server A', 'quantity': 10, 'datacenter_id': 1},
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['message'] == 'Item added successfully'


def test_add_item_missing_fields_returns_400(client):
    response = client.post('/api/item', json={'itemName': 'Server A'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_add_item_empty_body_returns_400(client):
    response = client.post('/api/item', json={})
    assert response.status_code == 400


def test_get_items_returns_200(client):
    response = client.get('/api/items')
    assert response.status_code == 200


def test_get_items_returns_list(client):
    client.post(
        '/api/item',
        json={'itemName': 'Switch', 'quantity': 5, 'datacenter_id': 1},
    )
    response = client.get('/api/items')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_update_item_missing_fields_returns_400(client):
    response = client.put('/api/item', json={'itemName': 'Server A'})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_update_item_returns_200(client):
    client.post(
        '/api/item',
        json={'itemName': 'Router', 'quantity': 3, 'datacenter_id': 1},
    )
    response = client.put('/api/item', json={'itemName': 'Router', 'quantity': 99})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Item updated successfully'


def test_delete_item_returns_200(client):
    client.post(
        '/api/item',
        json={'itemName': 'Temp Item', 'quantity': 1, 'datacenter_id': 1},
    )
    response = client.delete('/api/item/1')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['message'] == 'Item deleted successfully'

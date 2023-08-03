def test_room_create(host):
    @host.on('room/update')
    def room_update(data):
        for field in ('id', 'users', 'host', 'codecaster'):
            assert field in data

    host.emit('room/create', {})


def test_room_create_and_join(client, host):
    room_data = {}

    @host.on('room/update')
    def room_update(data):
        for field in ('id', 'users', 'host', 'codecaster'):
            assert field in data
        room_data.update(data)

    host.emit('room/create', {})
    host.sleep(0.1)

    assert 'id' in room_data
    actual_room_id = room_data['id']

    @client.on('room/join')
    def room_join(data):
        assert 'user_id' in data
        assert data.get('room_id') == actual_room_id

    client.emit('room/join', {"room_id": actual_room_id, "name": "Ivan"})

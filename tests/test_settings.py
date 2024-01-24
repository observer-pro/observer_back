import asyncio

from socketio import AsyncClient

from tests.conftest import TestContext


async def test_settings(
    host: AsyncClient,
    client: AsyncClient,
    room_join: dict,
    room_update: dict,
    settings: dict,
    context: TestContext,
):
    await host.emit('room/create', data={'name': 'Teacher'})
    await asyncio.sleep(0.01)
    context.room_id = room_update['id']
    context.host_id = room_update['host']
    await client.emit(
        'room/join',
        data={'room_id': context.room_id, 'name': 'Json Statham'},
    )
    await asyncio.sleep(0.01)
    context.client_id = room_join['user_id']

    ignore_settings = {
        'files_to_ignore': '# Byte-compiled / optimized / DLL files\n__pycache__/\n*.py[cod]\n*$py.class'
        '\n\n# C extensions\n*.so\n\n# Distribution / packaging\n.Python\nbuild/\ndev'
        'elop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nshare/python-wheels/\n*.'
        'egg-info/\n.installed.cfg\nvenv/\ntest.py',
    }
    await host.emit('settings', data=ignore_settings)
    await asyncio.sleep(0.01)

    assert set(settings['names']) == {'.Python', 'test.py', '.installed.cfg'}
    assert set(settings['dirs']) == {
        'venv',
        '__pycache__',
        'develop-eggs',
        'eggs',
        '.egg-info',
        'build',
        'downloads',
        '.eggs',
        'lib',
        'dist',
    }
    assert set(settings['extensions']) == {'so', 'py[cod]'}

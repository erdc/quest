from time import sleep
from quest.api.tasks import add_async, get_pending_tasks
import pytest
import quest


@pytest.fixture
def task_cleanup(api, request):
    request.addfinalizer(api.remove_tasks)

@add_async
def long_process(delay, msg):
    sleep(delay)
    return {'delay': delay, 'msg': msg}


@add_async
def long_process_with_exception(delay, msg):
    sleep(delay)
    1/0
    return {'delay': delay, 'msg': msg}


def wait_until_done():
    while len(get_pending_tasks()) > 0:
        sleep(0.2)
    return


@pytest.mark.parametrize('api', [quest.api])
def test_launch_tasks(api, task_cleanup):
    test_tasks = [
        long_process(1, 'first', async=True),
        long_process(1, 'second', async=True),
        long_process(1, 'third', async=True),
        ]

    tasks = api.get_tasks(as_dataframe=True)
    assert len(tasks) == 3
    assert sorted(test_tasks) == sorted(tasks.index.values)

    wait_until_done()
    for task, msg in zip(test_tasks, ['first', 'second', 'third']):
        assert {'delay': 1, 'msg': msg} == api.get_task(task)['result']


@pytest.mark.parametrize('api', [quest.api])
def test_add_remove_tasks(api):
    test_tasks = [
        long_process(1, 'first', async=True),
        long_process(1, 'second', async=True),
        long_process(1, 'third', async=True),
        ]

    assert len(api.get_tasks()) == 3
    test_tasks.append(long_process(5, 'fourth', async=True))
    assert len(api.get_tasks()) == 4
    api.cancel_tasks(test_tasks[3])
    assert len(api.get_tasks(filters={'status': 'cancelled'})) == 1
    api.remove_tasks(status='cancelled')
    assert len(api.get_tasks(filters={'status': 'cancelled'})) == 0
    assert len(api.get_tasks()) == 3
    wait_until_done()
    api.remove_tasks()
    assert len(api.get_tasks()) == 0


@pytest.mark.parametrize('api', [quest.api])
def test_task_with_exception(api, task_cleanup):
    test_tasks = [
        long_process(1, 'first', async=True),
        long_process_with_exception(1, 'second', async=True),
        long_process(1, 'third', async=True),
        ]

    tasks = api.get_tasks(as_dataframe=False)
    assert len(tasks) == 3
    wait_until_done()
    assert len(api.get_tasks(filters={'status': 'error'})) == 1

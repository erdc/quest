from time import sleep
from quest.api.tasks import add_async
import pytest
import quest


@pytest.fixture
def task_cleanup(api, request):
    def remove_tasks():
        pending_tasks = api.get_pending_tasks()
        api.cancel_tasks(pending_tasks)
        api.remove_tasks()

    request.addfinalizer(remove_tasks)


@add_async
def long_process(delay, msg):
    sleep(delay)
    return {'delay': delay, 'msg': msg}


@add_async
def long_process_with_exception(delay, msg):
    sleep(delay)
    1/0
    return {'delay': delay, 'msg': msg}


setattr(quest.api, 'long_process', long_process)
setattr(quest.api, 'long_process_with_exception', long_process_with_exception)


def wait_until_done(api):
    while len(api.get_pending_tasks()) > 0:
        sleep(0.2)
    return


@pytest.mark.tasks
def test_launch_tasks(api, task_cleanup):
    test_tasks = [
        api.long_process(1.011, 'first', async_tasks=True),
        api.long_process(1.012, 'second', async_tasks=True),
        api.long_process(1.013, 'third', async_tasks=True),
        ]

    tasks = api.get_tasks(as_dataframe=True)
    assert sorted(test_tasks) == sorted(tasks.index.values)
    assert len(tasks) == 3

    wait_until_done(api)
    for task, delay, msg in zip(test_tasks, [1.011, 1.012, 1.013], ['first', 'second', 'third']):
        task = api.get_task(task)
        assert 'finished' == task['status']
        assert {'delay': delay, 'msg': msg} == task['result']


@pytest.mark.tasks
def test_add_remove_tasks(api, task_cleanup):
    test_tasks = [
        api.long_process(1.021, 'first', async_tasks=True),
        api.long_process(1.022, 'second', async_tasks=True),
        api.long_process(1.023, 'third', async_tasks=True),
        ]
    assert len(api.get_tasks()) == 3
    test_tasks.append(api.long_process(10, 'fourth', async_tasks=True))
    assert len(api.get_tasks()) == 4
    api.cancel_tasks(test_tasks[3])
    sleep(.1)  # give status messages some time to update
    assert len(api.get_tasks(filters={'status': 'cancelled'})) == 1
    api.remove_tasks(status='cancelled')
    assert len(api.get_tasks(filters={'status': 'cancelled'})) == 0
    assert len(api.get_tasks()) == 3

    # test remove tasks by id
    t = api.long_process_with_exception(.01, 'fifth', async_tasks=True)
    assert len(api.get_tasks()) == 4
    wait_until_done(api)
    api.remove_tasks(task_ids=t)
    tasks = api.get_tasks()
    assert len(tasks) == 3
    assert t not in tasks

    # test remove tasks by id and status
    t1 = api.long_process_with_exception(.01, 'sixth', async_tasks=True)
    t2 = api.long_process(10, 'seventh', async_tasks=True)
    api.cancel_tasks(t2)
    wait_until_done(api)
    assert len(api.get_tasks()) == 5
    api.remove_tasks(task_ids=[t1, t2], status='finished')  # shouldn't remove any tasks
    assert len(api.get_tasks()) == 5
    api.remove_tasks(task_ids=[t1, t2], status=['error', 'cancelled'])
    assert len(api.get_tasks()) == 3

    wait_until_done(api)
    api.remove_tasks()
    assert len(api.get_tasks()) == 0


@pytest.mark.tasks
def test_task_with_exception(api, task_cleanup):
    test_tasks = [
        api.long_process(1.031, 'first', async_tasks=True),
        api.long_process_with_exception(1.032, 'second', async_tasks=True),
        api.long_process(1.033, 'third', async_tasks=True),
        ]

    tasks = api.get_tasks(as_dataframe=False)
    assert len(tasks) == len(test_tasks)
    wait_until_done(api)
    assert len(api.get_tasks(filters={'status': 'error'})) == 1


@pytest.mark.tasks
def test_get_tasks(api, task_cleanup):
    test_tasks = [
        api.long_process(1.041, 'first', async_tasks=True),
        api.long_process_with_exception(1.042, 'second', async_tasks=True),
        api.long_process(1.043, 'third', async_tasks=True),
    ]

    tasks = api.get_tasks(filters={'task_ids': test_tasks[:2]})
    assert len(tasks) == 2
    assert test_tasks[0] in tasks and test_tasks[1] in tasks
    wait_until_done(api)
    tasks = api.get_tasks(filters={'status': 'finished'})
    assert len(tasks) == 2
    assert test_tasks[0] in tasks and test_tasks[2] in tasks
    tasks = api.get_tasks(filters={'status': ['finished', 'error']})
    assert len(tasks) == 3
    tasks = api.get_tasks(filters={'fn': api.long_process.__name__})
    assert len(tasks) == 2
    tasks = api.get_tasks(filters={'task_ids': test_tasks, 'status': 'cancelled'})
    assert len(tasks) == 0
    tasks = api.get_tasks(filters={'task_ids': test_tasks, 'status': ['finished']})
    assert len(tasks) == 2

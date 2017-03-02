from time import sleep
import quest
from quest.api.tasks import add_async

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
    while len(quest.api.get_pending_tasks()) > 0:
        sleep(0.2)
    return


def test_launch_tasks():
    test_tasks = [
        long_process(1, 'first', async=True),
        long_process(1, 'second', async=True),
        long_process(1, 'third', async=True),
        ]

    tasks = quest.api.get_tasks(as_dataframe=True)
    assert len(tasks) == 3
    assert sorted(test_tasks) == sorted(tasks.index.values)

    wait_until_done()
    for task, msg in zip(test_tasks, ['first', 'second', 'third']):
        assert {'delay': 1, 'msg': msg} == quest.api.get_task(task)['result']


def test_add_remove_tasks():
    test_tasks = [
        long_process(1, 'first', async=True),
        long_process(1, 'second', async=True),
        long_process(1, 'third', async=True),
        ]

    assert len(quest.api.get_tasks()) == 3
    test_tasks.append(long_process(5, 'fourth', async=True))
    assert len(quest.api.get_tasks()) == 4
    quest.api.cancel_tasks(test_tasks[3])
    assert len(quest.api.get_tasks(filters={'status': 'cancelled'})) == 1
    quest.api.remove_tasks(status='cancelled')
    assert len(quest.api.get_tasks(filters={'status': 'cancelled'})) == 0
    assert len(quest.api.get_tasks()) == 3
    wait_until_done()
    quest.api.remove_tasks()
    assert len(quest.api.get_tasks()) == 0


def test_task_with_exception():
    test_tasks = [
        long_process(1, 'first', async=True),
        long_process_with_exception(1, 'second', async=True),
        long_process(1, 'third', async=True),
        ]

    tasks = quest.api.get_tasks(as_dataframe=True)
    assert len(tasks) == 3
    wait_until_done()
    assert len(quest.api.get_tasks(filters={'status': 'error'})) == 1

from functools import wraps, partial
from distributed import Client, LocalCluster
import psutil
import uuid


_ncores = psutil.cpu_count()

cluster = LocalCluster(nanny=False, n_workers=_ncores)
client = Client(cluster)

tasks = {}

def add_async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        async = kwargs.pop('async', None)
        if async:
            task_id = uuid.uuid4().hex
            future = client.submit(f, *args, **kwargs)
            task = {
                'task': f.__name__,
                'args': args,
                'kwargs': kwargs,
                'future': future,
                'status': 'active',
                'result': None,
            }
            tasks[task_id] = task
            future.add_done_callback(partial(_completed, task_id=task_id))
            return task_id
        else:
            return f(*args, **kwargs)
    return wrapper


def get_task(task_id):
    task = tasks.get(task_id)
    if task:
        task['task_id'] = task_id
        return task
    print('task {} not found'.format(task_id))
    return


def get_task_result(task_id):
    task = get_task(task_id)
    return task.get('result')


def get_task_status(task_id):
    task = get_task(task_id)
    return task.get('status')


def cancel_task(task_id):
    task = get_task(task_id)


def list_tasks(task=None, status=None, expand=None):
    """
        task = function name
        status = active, completed
    """
    task_list = tasks
    if status:
        task_list = {k: v for k, v in task_list.items() if v['status'] == status}

    if task:
        task_list = {k: v for k, v in task_list.items() if v['task'] == task}

    if not expand:
        task_list = task_list.keys()

    return task_list


def _completed(future, task_id):
    tasks[task_id]['status'] = 'completed'
    tasks[task_id]['result'] = future.result()
    return


def _pretty_print(f, args, kwargs):
    args_str = ", ".join('"{}"'.format(x) if isinstance(x, str) else str(x) for x in args)
    kwargs_str = ", ".join(['{}={}'.format(k, v) for k, v in kwargs.items()])
    return '{}({}{})'.format(f.__name__, args_str, kwargs_str)

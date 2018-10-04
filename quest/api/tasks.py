import sys
import psutil

import pandas as pd
from tornado import gen
from functools import wraps
from distributed import Client, LocalCluster
from concurrent.futures import CancelledError

from ..static import DatasetStatus
from ..util import listify, logger

_cluster = None
tasks = {}
futures = {}


class StartCluster():
    def __init__(self, n_cores=None):
        if n_cores is None:
            n_cores = psutil.cpu_count()-2
        self.cluster = LocalCluster(processes=True, n_workers=1)
        self.client = Client(self.cluster)

    def __exit__(self, type, value, traceback):
        self.cluster.close()


def _get_client():
    global _cluster
    if _cluster is None:
        _cluster = StartCluster()
    return _cluster.client


def add_async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        async_tasks = kwargs.pop('async_tasks', None)
        if async_tasks:
            client = _get_client()
            future = client.submit(f, *args, **kwargs)
            client.loop.add_callback(add_result_when_done, future)
            futures[future.key] = future
            tasks[future.key] = {
                'fn': f.__name__,
                'args': args,
                'kwargs': kwargs,
                'status': DatasetStatus.PENDING,
                'result': None,
            }
            return future.key
        else:
            return f(*args, **kwargs)
    return wrapper


def get_pending_tasks(**kwargs):
    """Return list of pending tasks

    calls get_tasks with filter -> status=pending, passes through other kwargs
    (filters={}, expand=None, as_dataframe=None, with_future=None)

    """
    filters = {'status': DatasetStatus.PENDING}
    if 'filters' in kwargs:
        kwargs['filters'].update(filters)
    else:
        kwargs['filters'] = filters
    return get_tasks(**kwargs)


def get_task(task_id, with_future=None):
    """Get details for a task.

    Args:
        task_id (string,Required):
            id of a task
        with_future (bool, Optional, Default=None):
           If true include the task `future` objects in the returned dataframe/dictionary

    """
    task = get_tasks(expand=True, with_future=with_future).get(task_id)
    if task is None:
        logger.error('task {} not found'.format(task_id))

    return task


def get_tasks(filters=None, expand=None, as_dataframe=None, with_future=None):
    """Get all available tasks.

    Args:
        filters (dict, Optional, Default=None):
            filter tasks by one or more of the available filters
                available filters:
                    `task_ids` (str or list): task id or list of task ids
                    `status` (str or list): single status or list of statuses. Must be subset of
                        ['pending', 'cancelled', 'finished', 'lost', 'error']
                    `fn` (str): name of the function a task was assigned
                    `args` (list): list of arguments that were passed to the task function
                    `kwargs` (dict): dictionary of keyword arguments that were passed to the task function
                    'result' (object): result of the task function
        expand (bool, Optional, Default=None):
            include details of tasks and format as a dict
        as_dataframe (bool, Optional, Default=None):
            include details of tasks and format as a pandas dataframe
        with_future (bool, Optional, Default=None):
           If true include the task `future` objects in the returned dataframe/dictionary

    Returns:
        tasks (list, dict, or pandas dataframe, Default=list):
            all available tasks
    """
    task_list = tasks
    if filters:
        task_ids = listify(filters.pop('task_ids', None))
        if task_ids is not None:
            task_list = {k: v for k, v in task_list.items() if k in task_ids}
        statuses = listify(filters.pop('status', None))
        if statuses is not None:
            task_list = {k: v for k, v in task_list.items() if v['status'] in statuses}
        for fk, fv in filters.items():
            task_list = {k: v for k, v in task_list.items() if v[fk] == fv}

    task_list = pd.DataFrame.from_dict(task_list, orient='index')
    if with_future:
        task_list['future'] = [futures[k] for k in task_list.index]

    if not expand and not as_dataframe:
        task_list = task_list.index.tolist()

    if expand:
        task_list = task_list.to_dict(orient='index')

    return task_list


def cancel_tasks(task_ids):
    """Cancel tasks.

       Args:
         task_ids (string or list of strings, Required):
            id of tasks to be cancelled
       """
    task_ids = listify(task_ids)
    df = get_tasks(with_future=True, as_dataframe=True)
    futures = df['future'][task_ids].tolist()
    c = _get_client()
    c.cancel(futures)
    return


def remove_tasks(task_ids=None, status=None):
    """Remove tasks.

    Args:
        task_ids (string or list, Optional, Default=None):
            tasks with this id(s) will be removed
        status (string or list, Optional, Default=None):
            tasks with this status(es) will be removed
            NOTE: 'pending' is not a valid option and will be ignored,
                since pending tasks must be canceled before they can be removed.

        If no status is specified, remove tasks with
        status = ['cancelled', 'finished', 'lost', 'error'] from task list
    """
    global tasks
    if status:
        status = listify(status)
    else:
        status = ['cancelled', 'finished', 'lost', 'error']

    if DatasetStatus.PENDING in status:
        logger.error('cannot remove pending tasks, please cancel them first')
        status.remove(DatasetStatus.PENDING)

    task_list = get_tasks(filters={'status': status, 'task_ids': task_ids})

    for key in task_list:
        del tasks[key]
        del futures[key]
    return


@gen.coroutine
def add_result_when_done(future):
    try:
        result = yield future._result()
        tasks[future.key]['result'] = result
    except CancelledError as e:
        tasks[future.key]['result'] = {'error_message': 'task cancelled'}
    except:
        tasks[future.key]['result'] = {'error_message': str(sys.exc_info()[0])}
    tasks[future.key]['status'] = future.status

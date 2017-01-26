from functools import wraps
from distributed import Client, LocalCluster
import psutil
from jsonrpc import dispatcher
import pandas as pd
from ..util import listify
from ..util.log import logger

_cluster = None
tasks = {}
futures = {}


class StartCluster():
    def __init__(self, n_cores=None):
        if n_cores is None:
            n_cores = psutil.cpu_count()-2
        self.cluster = LocalCluster(nanny=True, n_workers=1)
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
        async = kwargs.pop('async', None)
        if async:
            client = _get_client()
            future = client.submit(f, *args, **kwargs)
            futures[future.key] = future
            tasks[future.key] = {
                'fn': f.__name__,
                'args': args,
                'kwargs': kwargs,
                'status': None,
                'result': None,
            }
            return future.key
        else:
            return f(*args, **kwargs)
    return wrapper


@dispatcher.add_method
def get_task(task_id, with_future=None):
    """Get details for a task.

    Args:
        task_id (string,Required):
            id of a task
        with_future (bool, Optional, Default=None):

    """
    task = get_tasks(expand=True, with_future=with_future).get(task_id)
    if task is None:
        logger.error('task {} not found'.format(task_id))

    return task


@dispatcher.add_method
def get_tasks(filters=None, expand=None, as_dataframe=None, with_future=None):
    """Get all available tasks.

    Args:
        filters #comback
        expand (bool, Optional, Default=None):
            include details of tasks and format as a dict
        as_dataframe (bool, Optional, Default=None):
            include details of tasks and format as a pandas dataframe
        with_future (bool, Optional, Default=None):
            #comeback

    Returns:
        tasks (list, dict, or pandas dataframe, Default=list):
            all available tasks
    """
    # update status
    _update_status()

    task_list = tasks
    if filters:
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


@dispatcher.add_method
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


@dispatcher.add_method
def remove_tasks(status=None):
    """Remove tasks.

    Args:
        status (string, Optional, Default=None):
            tasks with this status will be removed

        If no status is specified, remove tasks with
        status = ['cancelled', 'finished', 'lost', 'error'] from task list
    """
    global tasks
    _update_status()
    if status:
        status = listify(status)
    else:
        status = ['cancelled', 'finished', 'lost', 'error']

    if 'pending' in status:
        logger.error('cannot remove pending tasks, please cancel them first')
        status.remove('pending')

    for key in [k for k, v in tasks.items() if v['status'] in status]:
        del tasks[key]
        del futures[key]
    return


def _update_status():
    for k in tasks.keys():
        future = futures[k]
        tasks[k]['status'] = future.status
        if future.status == 'finished':
            tasks[k]['result'] = future.result()

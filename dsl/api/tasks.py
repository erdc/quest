from functools import wraps
from distributed import Client, LocalCluster
import psutil
from jsonrpc import dispatcher
import pandas as pd
from ..util import listify


_cluster = None
tasks = {}


class StartCluster():
    def __init__(self, n_cores=None):
        if n_cores is None:
            n_cores = psutil.cpu_count()
        self.cluster = LocalCluster(nanny=False, n_workers=n_cores)
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
            task = {
                'fn': f.__name__,
                'args': args,
                'kwargs': kwargs,
                'future': future,
                'status': future.status,
                'result': None,
            }
            tasks[future.key] = task
            future.add_done_callback(_completed)
            return future.key
        else:
            return f(*args, **kwargs)
    return wrapper


@dispatcher.add_method
def get_task(task_id, with_future=None):
    task = get_tasks(expand=True, with_future=with_future).get(task_id)
    if task is None:
        print('task {} not found'.format(task_id))
    return task


@dispatcher.add_method
def get_tasks(filters=None, expand=None, as_dataframe=None, with_future=None):
    """
        filters: any of the dict keys i.e. status, fn
        status = (pending, cancelled, finished, lost, error)
    """
    # update status
    _update_status()

    task_list = tasks
    if filters:
        for fk, fv in filters.items():
            task_list = {k: v for k, v in task_list.items() if v[fk] == fv}

    task_list = pd.DataFrame.from_dict(task_list, orient='index')
    if not with_future:
        task_list.drop(['future'], inplace=True, axis=1, errors='ignore')

    if not expand and not as_dataframe:
        task_list = task_list.index.tolist()

    if expand:
        task_list = task_list.to_dict()

    return task_list


@dispatcher.add_method
def cancel_tasks(task_ids):
    task_ids = listify(task_ids)
    df = get_tasks(with_future=True, as_dataframe=True)
    futures = df['future'][task_ids].tolist()
    c = _get_client()
    c.cancel(futures)
    return


@dispatcher.add_method
def remove_tasks(status=None):
    """
        status can be a list of statuses, default removes
        tasks with status = ['cancelled', 'finished', 'lost', 'error']
        from task list
    """
    global tasks
    _update_status()
    if status:
        status = listify(status)
    else:
        status = ['cancelled', 'finished', 'lost', 'error']

    if 'pending' in status:
        print('cannot remove pending tasks, please cancel them first')
        status.remove('pending')

    tasks = {k: v for k, v in tasks.items() if v['status'] in status}
    return


def _completed(future):
    tasks[future.key]['status'] = future.status
    tasks[future.key]['result'] = future.result()
    return


def _update_status():
    for k in tasks.keys():
        tasks[k]['status'] = tasks[k]['future'].status

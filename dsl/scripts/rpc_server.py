"""run dsl rpc server.

This script wraps dsl.api functions and exposes them through RPC
"""

import click
from dsl import api
import json
from jsonrpc import JSONRPCResponseManager, dispatcher

import requests

from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from threading import Thread
import time

jobid = 0


@click.group()
def cli():
    """Run DSL RPC Server

    This script wraps dsl.api functions and exposes them through JSON RPC over HTTP.
    """
    pass


@cli.command('start', help='Start DSL RPC server')
@click.option('--port', default=4000, help='Port number to run rpc server. Default(4000)')
@click.option('--threaded', is_flag=True, help='Run each request in a new thread')
@click.option('--processes', default=1, type=int, help='Number of Processes to use')
def start_server(port, threaded, processes):
    """Start DSL RPC Server\b

    This script wraps dsl.api functions and exposes them through JSON RPC over HTTP.

    example of using rpc with curl:

        curl -H "Content-Type: application/json" -X POST -d '{"jsonrpc": "2.0", "method": "get_collections", "id":0}' localhost:4000

    \b
    <port>   : Port number to run rpc server. Default(4000)
    """
    if threaded and processes>1:
        print('RPC server can either be started multithreaded or multiprocess. Not both. Please pick one.')
        exit(0)
        
    run_simple('localhost', port, wsgi_app, threaded=threaded, processes=processes)


@cli.command('stop', help='Stop DSL RPC server')
@click.option('--port', default=4000, help='Port number rpc server is running on. Default(4000)')
def stop_server(port):
    """Stop DSL RPC Server\b

    DSL RPC server can also be stopped using RPC

    example using curl:

        curl -H "Content-Type: application/json" -X POST -d '{"jsonrpc": "2.0", "method": "shutdown", "id": 0}' localhost:4000
    \b
    <port>   : Port number rpc server is running on. Default(4000)
    """
    url = "http://localhost:%s" % port
    headers = {'content-type': 'application/json'}

    payload = {
        "method": "shutdown",
        "jsonrpc": "2.0",
        "id": 0,
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print('DSL RPC Server shutting down...')


@dispatcher.add_method
def long_download(delay=1):
    global jobid
    print('Job {0}. sleeping for: {1} seconds'.format(jobid, delay))
    jobid += 1
    thr = Thread(target=run_download, args=[jobid-1, delay])
    thr.start()
    return jobid

def run_download(jobid, delay):
    time.sleep(delay)
    print('-> Job {0}. {1} seconds task is finished'.format(jobid, delay))


def shutdown_server(environ):
    if not 'werkzeug.server.shutdown' in environ:
        raise RuntimeError('Not running the development server')

    def fn():
        environ['werkzeug.server.shutdown']()
        return 'DSL RPC Server shutting down...'

    return fn


@Request.application
def wsgi_app(request):
    # Dispatcher is a dictionary {<method_name>: callable}
    dispatcher["echo"] = lambda s: s
    dispatcher["shutdown"] = shutdown_server(request.environ)

    response = JSONRPCResponseManager.handle(request.data, dispatcher)
    return Response(response.json, mimetype='application/json')


if __name__ == '__main__':
    cli()

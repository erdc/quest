import click
import dsl

@click.group()
def cli():
    """get-elevations
    Script to extract elevation data
    """
    pass


@cli.command('list')
def list_elevation_services():
    services = dsl.api.get_services(parameter='elevation', datatype='raster')
    click.echo('\n                             Available Elevation Datasets:')
    click.echo('-----------------------------------------------------------------------------------------')
    click.echo('service code\t\t|\tdescription')
    click.echo('-----------------------------------------------------------------------------------------')
    for s in services:
        click.echo('%s\t\t|\t%s' % (s['service_code'], s['display_name']))
    click.echo('-----------------------------------------------------------------------------------------\n')


@cli.command('extract')
@click.option('--method', default='bilinear', help='Interpolation type (bilinear or nearest')
@click.option('--collection', default='default', help='Name of collection to save data')
@click.argument('service')
@click.argument('input_file')
@click.argument('output_file')
def extract(service, input_file, output_file, collection, method):
    #create a temporary collection
    col = dsl.api.new_collection(collection)
    col = dsl.api.apply_filter('get-elevations-along-path', collection_name=collection, method=method, service=service, input_file=input_file, output_file=output_file)
    click.echo('\n Extracted elevations saved in %s \n' % output_file)


if __name__ == '__main__':
    cli()
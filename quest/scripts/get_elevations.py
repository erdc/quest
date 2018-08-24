import click
import quest

@click.group()
def cli():
    """Quest script to extract elevation data along a path/polygon from raster elevation web providers
    """
    pass


@cli.command('list')
def list_elevation_services():
    """Lists available elevation providers
    """
    services = quest.api.get_services(parameter='elevation', datatype='raster')
    click.echo('\n                             Available Elevation Datasets:')
    click.echo('-----------------------------------------------------------------------------------------')
    click.echo('service code\t\t|\tdescription')
    click.echo('-----------------------------------------------------------------------------------------')
    for s in services:
        click.echo('%s\t\t|\t%s' % (s['service_code'], s['display_name']))
    click.echo('-----------------------------------------------------------------------------------------\n')


@cli.command('extract')
@click.option('--method', default='bilinear', type=click.Choice(['bilinear', 'nearest']), help='Interpolation method (Default: "bilinear")')
@click.option('--collection', default='default', help='Collection to save data in (Default: "default")')
@click.argument('service', metavar='<service>')
@click.argument('input_file', metavar='<input>', type=click.Path(exists=True))
@click.argument('output_file', metavar='<output>')
def extract(service, input_file, output_file, collection, method):
    """Extract elevation data along path/polygon

    Any vector format supported by gdal/fiona *should* work as 
    long as they ony contain simple geometries. i.e. Polylines, MultiPoint, 
    Polygon OR collections of the same. Script has only been tested with 
    Polyline GeoJSON.

    \b
    <service>   : service code of elevation dataset (see 'list')
    <input>     : path to input vector file (GeoJSON, Shapefile etc)
    <output>    : path to output vector file (same type as input)
    """
    #create a temporary collection
    col = quest.api.new_collection(collection)
    col = quest.api.run_tool('get-elevations-along-path', collection_name=collection, method=method, service=service, input_file=input_file, output_file=output_file)
    click.echo('\n Extracted elevations saved in %s \n' % output_file)


if __name__ == '__main__':
    cli()
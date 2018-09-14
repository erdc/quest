import param

from .rst_base import RstBase
from quest.util import unit_list, unit_registry, setattr_on_dataframe


class RstUnitConversion(RstBase):
    _name = 'raster-unit-conversion'
    to_units = param.ObjectSelector(default=None,
                                    doc="""Units of the resulting dataset.""",
                                    objects=unit_list()
                                    )

    def _run(self, df, orig_metadata):
        if self.to_units is None:
            raise ValueError('to_units cannot be None')

        metadata = orig_metadata
        if 'file_path' in metadata:
            del metadata['file_path']

        reg = unit_registry()
        from_units = metadata['unit']
        if '/' in from_units and '/' not in self.to_units:
            beg = from_units.find('/')
            end = len(from_units)
            default_time = from_units[beg:end]
            to_units = self.to_units + default_time
        else:
            to_units = self.to_units
        conversion = reg.convert(1, src=from_units, dst=to_units)
        result = df.read()
        result = result * conversion
        metadata.update({'unit': to_units})
        setattr_on_dataframe(df, 'metadata', metadata)
        df = result
        return df

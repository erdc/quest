import param

from quest.util import setattr_on_dataframe, unit_list, unit_registry

from .ts_base import TsBase

periods = {
    'daily': 'D',
    'weekly': 'W',
    'monthly': 'M',
    'annual': 'A',
}


class TsRemoveOutliers(TsBase):
    _name = 'ts-remove-outliers'
    sigma = param.Number(default=1, doc="values greater than (sigma * std deviation) from median will be filtered out")

    def _run(self, df):
        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']
        parameter = metadata['parameter']
        sigma = self.sigma
        if sigma is None:
            sigma = 3

        # remove anything 'sigma' standard deviations from median
        vmin = df[parameter].median() - float(sigma)*df[parameter].std()
        vmax = df[parameter].median() + float(sigma)*df[parameter].std()
        df = df[(df[parameter] > vmin)]
        df = df[(df[parameter] < vmax)]
        setattr_on_dataframe(df, 'metadata', metadata)

        #if despike:
        #    kw = dict(n1=2, n2=20, block=6)
        #    df = despike(df, **kw)
        #    new_df = df.resample(periods[period], how=method, kind='period')

        return df


class TsUnitConversion:  # (TsBase): TODO: Fix this to allow for multi-dimensional units
    _name = 'ts-unit-conversion'
    to_units = param.ObjectSelector(default=None,
                                    doc="""Units of the resulting dataset.""",
                                    objects=unit_list()
                                    )

    def _run(self, df):
        if self.to_units is None:
            raise ValueError('To_units cannot be None')

        metadata = df.metadata
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
        df[df.columns[1]] = df[df.columns[1]] * conversion
        metadata.update({'unit': to_units})
        setattr_on_dataframe(df, 'metadata', metadata)

        return df


class TsResample(TsBase):
    _name = 'ts-resample'
    period = param.ObjectSelector(doc="resample frequency",
                                  objects=['daily', 'weekly', 'monthly', 'annual'],
                                  default='daily',
                                  precedence=1,
                                  )
    method = param.ObjectSelector(doc="resample method",
                                  objects=['sum', 'mean', 'std', 'max', 'min', 'median'],
                                  default='mean',
                                  precedence=2,
                                  allow_None=False,
                                  )

    def _run(self, df):
        metadata = df.metadata
        if 'file_path' in metadata:
            del metadata['file_path']
        param = metadata['parameter']
        period = self.period
        method = self.method

        orig_param, orig_period, orig_method = (param.split(':') + [None, None])[:3]
        new_df = getattr(df.resample(periods[period], kind='period'), method)()

        new_param = '%s:%s:%s' % (orig_param, period, method)
        new_df.rename(columns={param: new_param}, inplace=True)  #inplace must be set to True to make changes

        metadata.update({'parameter': new_param})
        setattr_on_dataframe(new_df, 'metadata', metadata)

        return new_df

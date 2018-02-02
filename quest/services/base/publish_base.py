from quest.util.param_util import format_json_options
import param


class PublishBase(param.Parameterized):
    publisher_name = None
    display_name = None
    description = None
    publisher_type = None

    def __init__(self, provider, **kwargs):
        self.provider = provider
        super(PublishBase, self).__init__(**kwargs)

    @property
    def title(self):
        return '{} Download Options'.format(self.display_name)
        pass

    @property
    def metadata(self):
        return {
            'display_name': self.display_name,
            'description': self.description,
            'publisher_type': self.publisher_type,
        }

    def publish_options(self, fmt):
        if fmt == 'param':
            schema = self

        elif fmt == 'json':
            schema = format_json_options(self)

        else:
            raise ValueError('{} is an unrecognized format.'.format(fmt))

        return schema

    def publish(self, feature, file_path, dataset, **params):
        raise NotImplementedError()

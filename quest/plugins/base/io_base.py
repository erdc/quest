import abc


class IoBase(metaclass=abc.ABCMeta):
    """Abstract Base class for I/O for different file formats."""

    def __init__(self):
        """Init calls register."""
        self.register()

    @abc.abstractmethod
    def register(self):
        """Register plugin by setting description and io type."""

    @abc.abstractmethod
    def read(self):
        """Write data to format."""

    @abc.abstractmethod
    def open(self):
        """Open data and return in requested format."""

    @abc.abstractmethod
    def write(self):
        """Write data to format."""

    @abc.abstractmethod
    def visualize(self):
        """Lightweight vizualization."""

    @abc.abstractmethod
    def visualize_options(self):
        """Lightweight vizualization options."""

from abc import abstractmethod


class AbstractBackend(object):
    def __init__(self, config, *args, **kwargs):
        self.config = config
        super(AbstractBackend, self).__init__()

    @abstractmethod
    def get(self, key, **kwargs):
        pass

    @abstractmethod
    def set(self, key, value, **kwargs):
        pass

    @abstractmethod
    def delete(self, key, **kwargs):
        pass

    @abstractmethod
    def list(self, path, **kwargs):
        pass

import os

class Env_Dictionary(dict):

    def _add_to_env(self, key: str, item: str):
        os.environ[key] = item
    
    def _remove_from_env(self, key: str):
        os.environ.pop(key, None)

    def __setitem__(self, key, item):
        self.__dict__[key] = item
        self._add_to_env(self, key, item)

    def __getitem__(self, key):
        return self.__dict__[key]

    def __repr__(self):
        return repr(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __delitem__(self, key):
        del self.__dict__[key]
        self._remove_from_env(self, key)

    def clear(self):
        for key in self.__dict__.keys():
            self._remove_from_env(self, key)

        return self.__dict__.clear()

    def copy(self):
        return self.__dict__.copy()

    def has_key(self, k):
        return k in self.__dict__

    def update(self, *args, **kwargs):
        self._add_to_env(*args, **kwargs)
        return self.__dict__.update(*args, **kwargs)
        
    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def pop(self, *args):
        self._remove_from_env(*args)
        return self.__dict__.pop(*args)
        
    def __cmp__(self, dict_):
        return self.__cmp__(self.__dict__, dict_)

    def __contains__(self, item):
        return item in self.__dict__

    def __iter__(self):
        return iter(self.__dict__)

    def __unicode__(self):
        return unicode(repr(self.__dict__))


# o = Mapping()
# o.foo = "bar"
# o['lumberjack'] = 'foo'
# o.update({'a': 'b'}, c=44)
# print 'lumberjack' in o
# print o

# In [187]: run mapping.py
# True
# {'a': 'b', 'lumberjack': 'foo', 'foo': 'bar', 'c': 44}
   
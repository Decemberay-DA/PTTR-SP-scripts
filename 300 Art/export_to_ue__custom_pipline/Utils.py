
class Utils:
    @staticmethod
    def map_action(iterator, func):
        for item in iterator:
            func(item)

    @staticmethod
    def map_iter(iterator, func):
        for item in iterator:
            yield func(item)

    @staticmethod
    def map_iter_pipe(iterator, *funcs):
        for item in iterator:
            for func in funcs:
                item = func(item)
            yield item

    @staticmethod
    def execute_pass_queue(obj, *fn):
        for fn in fn:
            fn(obj)

    @staticmethod
    def do(obj, fn):
        fn()
        return obj

    @staticmethod
    def btw(fn):
        fn()
        return lambda obj: obj

class Decorating:
    @staticmethod
    def returns_self(method):
        def wrapper(self, *args, **kwargs):
            method(self, *args, **kwargs)
            return self
        return wrapper

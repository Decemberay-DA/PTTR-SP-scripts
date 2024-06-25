
def map_action(iterator, func):
    for item in iterator:
        func(item)

def map_iter(iterator, func):
    for item in iterator:
        yield func(item)

def map_iter_pipe(iterator, *funcs):
    for item in iterator:
        for func in funcs:
            item = func(item)
        yield item

def execute_pass_queue(obj, *fn):
    for fn in fn:
        fn(obj)

def do(obj, fn):
    fn()
    return obj

def btw(fn):
    fn()
    return lambda obj: obj


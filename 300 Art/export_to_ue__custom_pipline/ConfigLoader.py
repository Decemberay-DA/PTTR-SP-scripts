import json
from types import *

def load_config():
    with open("config.json", "r") as config_file:
        config_dict = json.load(config_file)

    def dict_to_namespace(d):
        return json.loads(json.dumps(d), object_hook=lambda d: SimpleNamespace(**d))
    
    return dict_to_namespace(config_dict)


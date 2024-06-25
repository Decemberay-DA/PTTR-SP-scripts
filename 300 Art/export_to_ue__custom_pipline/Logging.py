import datetime
import traceback
import Logging
import Decorating
import Utils as U
import ConfigLoader

cnf = ConfigLoader.load_config().logging

def tab():
    return " " * cnf.tab_size

def clear_log_file():
    with open(cnf.log_file_name, "w") as f:
        pass
def log_to_file(message):
    time_written = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    stack_depth = len(traceback.extract_stack()) - 1 - 10
    indentation = tab() * stack_depth
    log_message = f"{time_written}: {indentation}{message}"
    
    with open(cnf.log_file_name, "a") as f:
        f.write(f"{log_message}\n")

class LoggerMonad:
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name
        self.current_intent = 0

    @property
    def current_intent(self):
        return self._current_intent
    
    @property
    def current_intent(self, level):
        self._current_intent = level
    
    @property
    def log_file_name(self):
        return self.log_file_name

    @Decorating.returns_self
    def clear_log_file(self):
        Logging.cLoggingear_log_file()

    @Decorating.returns_self
    def write(self, message):
        Logging.log_to_file(message)
    
    @Decorating.returns_self 
    def up(self):
        self.current_intent += 1
    
    @Decorating.returns_self    
    def down(self):
        self.current_intent -= 1

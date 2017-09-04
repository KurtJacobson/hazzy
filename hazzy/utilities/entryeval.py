#!/usr/bin/env python

from simpleeval import SimpleEval
from getiniinfo import GetIniInfo

import logger

log = logger.get('HAZZY.UTILITIES.ENTRY_EVAL')


class EntryEval:

    def __init__(self):
        self.s = SimpleEval()

        try:
            ini = GetIniInfo()
            self.machine_metric = ini.get_machine_metric()
        except:
            # GetIniInfo instance has no __call__ method
            self.machine_metric = False
            log.info('INI file not available, assuming machine units inch')

    # Evaluate expressions in numeric entries
    def eval(self, data):
        factor = 1
        data = data.lower()
        if "in" in data or '"' in data:
            data = data.replace("in", "").replace('"', "")
            if self.machine_metric:
                factor = 25.4
        elif "mm" in data:
            data = data.replace("mm", "")
            if self.machine_metric:
                factor = 1/25.4
        return self.s.eval(data) * factor

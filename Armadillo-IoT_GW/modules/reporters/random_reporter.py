from modules.lib.reporter import Reporter
from modules.lib.report import Report
import random


class RandomReporter(Reporter):
    def data_type(self):
        return 'random'

    def report(self):
        report = Report.report_now(
            'measurement',
            type='random',
            key='random',
            value=random.randint(0,100),
            unit='%'
        )

        return report

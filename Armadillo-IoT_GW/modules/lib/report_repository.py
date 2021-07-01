from abc import abstractmethod
from modules.const import Const
from modules.lib.loopable import Loopable


class ReportRepository(Loopable):
    @abstractmethod
    async def process_report(self, report):
        pass

    async def process_reports(self, reports):
        return False

    def __init__(self, report_queue, interval):
        super().__init__(interval)
        self._report_queue = report_queue
        self._enable_posting_multi_measurement = False

    async def routine(self):
        if self._enable_posting_multi_measurement:
            if self._report_queue.size() == 1:
                report = self._report_queue.pop()
                if not self.process_report(report):
                    self._report_queue.push_top(report)
            elif self._report_queue.size() > 1:
                while True:
                    reports = self._report_queue.pop_multi(Const.BULK_REPORT_COUNT)
                    if reports is None:
                        break

                    if not self.process_reports(reports):
                        self._report_queue.push_top_multi(reports)
                        break
        else:
            while True:
                report = self._report_queue.pop()
                if report is None:
                    break

                if not self.process_report(report):
                    self._report_queue.push_top(report)
                    break

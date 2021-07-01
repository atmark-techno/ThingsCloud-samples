import threading
from modules.const import Const
from modules.lib.agent_utils import get_mac
from modules.lib.report_queue import ReportQueue
from modules.lib.reporter_manager import ReporterManager
from modules.things_cloud.device import ThingsCloudDevice
from modules.things_cloud.operation_handler import OperationDispatcher
from modules.things_cloud.report_repository import ThingsCloudReportRepository
from modules.things_cloud.alarm_repository import ThingsCloudAlarmRepository


class ThingsCloud:
    def set_cloud_interval(self, interval):
        if interval is None:
            interval = Const.DEFAULT_CLOUD_REPORT_INTERVAL_SEC

        self.__report_repo.interval = interval
        self.__dispatcher.interval = interval

    def set_reporter_interval(self, key, interval):
        reporters = (x for x in self.__reporters if x.data_type() == key)
        for reporter in reporters:
            reporter.interval = interval

    def __listen_to_reporters(self):
        for reporter in self.__reporters:
            if reporter.interval == 0:
                self.__manager.add_nop(reporter)
            else:
                self.__manager.listen_to(reporter)

    def __apply_params(self, params):
        self.set_cloud_interval(params.interval('cloud'))
        for reporter in self.__reporters:
            reporter_name = reporter.data_type()
            reporter.interval = params.interval(reporter_name)
            reporter.set_alarm_condition(params.alarms(reporter_name))

    def upate_config(self, userame, password):
        self.__config.update(userame, password)

    def update_params_with_json(self, params):
        self.__params.update_with_json(params)
        self.__apply_params(self.__params)

    def __init__(self, reporters, config, params, led):
        print('Hello ThingsCloud')
        unique_id = 'armadillo-' + get_mac()

        if not config.is_valid():
            raise Exception("The config is invalid: some fields are not set!")

        self.__config = config

        self.__device = ThingsCloudDevice(config, self.upate_config,
                                          params, self.update_params_with_json,
                                          unique_id, led)
        self.__report_queue = ReportQueue()
        self.__alarm_queue = ReportQueue()
        report_interval = Const.DEFAULT_CLOUD_REPORT_INTERVAL_SEC
        self.__report_repo = ThingsCloudReportRepository(self.__report_queue,
                                                         self.__device,
                                                         report_interval)
        self.__alarm_repo = ThingsCloudAlarmRepository(self.__alarm_queue,
                                                       self.__device, 1)
        self.__manager = ReporterManager(
                                    self.__report_queue, self.__alarm_queue)
        self.__params = params

        self.__dispatcher = OperationDispatcher(self.__device,
                                                params.interval('cloud'))

        self.__reporters = reporters
        self.__apply_params(params)

        self.__listen_to_reporters()

        loopables = [
            self.__report_repo,
            self.__alarm_repo,
            self.__manager,
            self.__dispatcher
        ]

        for loopable in loopables:
            self.thread = threading.Thread(target=loopable.start_loop)
            self.thread.start()

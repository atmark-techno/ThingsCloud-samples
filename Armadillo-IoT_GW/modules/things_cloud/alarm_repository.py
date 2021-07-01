from modules.lib.report_repository import ReportRepository


class ThingsCloudAlarmRepository(ReportRepository):
    def __init__(self, alarm_queue, device, interval):
        self.device = device
        super().__init__(alarm_queue, interval)

    def process_report(self, alarm):
        if alarm.is_activate:
            return self.device.activate_alarm(alarm)
        else:
            return self.device.deactivate_alarm(alarm)

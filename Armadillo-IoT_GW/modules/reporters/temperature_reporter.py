from modules.lib.reporter import Reporter
from modules.lib.report import Report


class TemperatureReporter(Reporter):
    def data_type(self):
        return 'temperature'

    def report(self):
        with open('/sys/class/thermal/thermal_zone0/temp') as file:
            temp = int(file.read()) // 1000
            # temp = int(file.read()) / float(1000)
        report = Report.report_now(
            'measurement',
            type='temperature',
            key='zone_0',
            value=temp,
            unit='c'
        )

        return report

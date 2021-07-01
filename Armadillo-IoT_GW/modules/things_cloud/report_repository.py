from modules.lib.report_repository import ReportRepository


class ThingsCloudReportRepository(ReportRepository):
    def __init__(self, report_queue, device, interval):
        super().__init__(report_queue, interval)
        self._enable_posting_multi_measurement = True
        self.device = device

    def __create_measurement(self, report):
        data = report.reported_data
        data_type = data['type']
        key = data['key']
        unit = data['unit']
        value = data['value']
        datetime = report.reported_at
        measurement = {
            'type': data_type,
            data_type: {
                key: {
                    'value': value,
                    'unit': unit
                }
            },
            'source': {
                'id': self.device.device_id()
            },
            'time': datetime.isoformat()
        }
        return measurement

    def process_report(self, report):
        if report.data_type == 'measurement':
            return self.device.post_measurement(
                                            self.__create_measurement(report))

        return False

    def process_reports(self, reports):
        if len(reports) == 1:
            return self.process_report(reports[0])

        mesurements = []
        for report in reports:
            if report.data_type == 'measurement':
                mesurements.append(self.__create_measurement(report))

        if mesurements:
            return self.device.post_measurements(mesurements)
        else:
            return False

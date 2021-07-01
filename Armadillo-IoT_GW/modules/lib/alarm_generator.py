from modules.lib.alarm import Alarm


class AlarmGenerator:
    def generate(self, report):
        alarm = None
        if self.__condition is None:
            return None

        for cond in self.__condition:
            if cond.is_active:
                (result, alarm_id) = cond.check_clear_on_report(report)
                if result:
                    alarm = Alarm(cond.alarm_type, cond.description,
                                  alarm_id, is_activate=False,
                                  time=report.reported_at)
            else:
                (result, alarm_id) = cond.check_generate_on_report(report)
                if result:
                    alarm = Alarm(cond.alarm_type, cond.description,
                                  alarm_id, is_activate=True,
                                  time=report.reported_at)

        return alarm

    def __init__(self, condition):
        self.__condition = condition

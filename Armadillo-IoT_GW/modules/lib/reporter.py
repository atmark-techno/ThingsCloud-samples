from abc import ABC, abstractmethod
from modules.lib.alarm_generator import AlarmGenerator


class Reporter(ABC):
    @abstractmethod
    def data_type(self):
        pass

    @abstractmethod
    def report(self):
        pass

    def report_with_alarm(self):
        report = self.report()

        alarm = None
        if self.alarm_generator is not None:
            alarm = self.alarm_generator.generate(report)

        return report, alarm

    def set_alarm_condition(self, alarm_condition):
        if alarm_condition is None:
            self.__alarm_generator = None
            return

        self.__alarm_generator = AlarmGenerator(alarm_condition)

    @property
    def alarm_generator(self):
        return self.__alarm_generator

    def __init__(self):
        self.interval = 30
        self.__alarm_generator = None

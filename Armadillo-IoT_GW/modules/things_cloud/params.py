from modules.lib.alarm_condition import AlarmCondition
from modules.lib.alarm_condition_parser import parse_alarm_condition
import json


def alarm_condition_from_params(params, key):
    try:
        alarm_condition = params[key]['alarms']
        if alarm_condition is None:
            return None
        return [parse_alarm_condition(cond) for cond in alarm_condition]
    except KeyError:
        return None


def interval_from_params(params, key):
    interval = 0
    try:
        interval_string = params[key]['interval']
        interval = str_to_interval(interval_string)
    except KeyError:
        print('KeyError:', key)

    return interval


def str_to_interval(interval_string):
    interval = 0
    if interval_string is not None:
        try:
            interval = max(int(interval_string), 0)
        except ValueError:
            pass
    return interval


class ThingsCloudParams:
    @classmethod
    def from_file(cls, filename):
        with open(filename, 'r') as f:
            params_str = f.read()
            params = cls(origin_file=filename)

            params.load_json(params_str)

            return params

    def load_json(self, params_json):
        parsed = json.loads(params_json)

        for key in parsed.keys():
            interval = interval_from_params(parsed, key)
            self.add_param(key, interval)

            condition = alarm_condition_from_params(parsed, key) or []
            self.set_alarms(key, condition)

        self.set_serialization(params_json)

    def __init__(self, serialization=None, origin_file=None):
        self.__params = {
            "cloud": {
                "interval": 30,
                "alarms": [],
            }
        }
        self.__serialization = serialization
        self.__origin_file = origin_file

    def __str__(self):
        def default(o):
            if type(o) is AlarmCondition:
                return json.loads(repr(o))
            else:
                raise TypeError(repr(o) + " is not JSON serializable")

        if self.__serialization is not None:
            return self.__serialization

        return json.dumps(self.__params, default=default)

    def set_serialization(self, serialization):
        self.__serialization = serialization

    def __check_presense(self, name):
        if name not in self.__params:
            raise Exception(
                "No reporter with the name exists: {}"
                .format(name)
            )

    def update_with_json(self, json):
        if self.__origin_file is not None:
            with open(self.__origin_file, 'w') as f:
                f.write(json)

        self.load_json(json)

    def add_param(self, name, interval):
        self.__serialization = None
        self.__params[name] = {
            "interval": interval,
            "alarms": [],
        }

    def set_interval(self, name, interval):
        self.__serialization = None
        self.__check_presense(name)

        self.__params[name]["interval"] = interval

    def set_alarms(self, name, alarms):
        self.__serialization = None
        self.__check_presense(name)

        self.__params[name]["alarms"] = alarms

    def add_alarm(self, name, alarm):
        self.__serialization = None
        self.__check_presense(name)

        self.__params[name]["alarms"].append(alarm)

    def alarms(self, name):
        self.__check_presense(name)
        return self.__params[name]["alarms"]

    def interval(self, name):
        self.__check_presense(name)
        return self.__params[name]["interval"]

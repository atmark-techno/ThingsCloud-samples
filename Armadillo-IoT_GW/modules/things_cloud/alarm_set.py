class AlarmSet:
    def equals(self, agent_alarm_id):
        return self.__agent_alarm_id == agent_alarm_id

    def things_cloud_alarm_id(self):
        return self.__things_cloud_alarm_id

    def __init__(self, agent_alarm_id, things_cloud_alarm_id):
        self.__agent_alarm_id = agent_alarm_id
        self.__things_cloud_alarm_id = things_cloud_alarm_id


class AlarmSetArray:
    def append(self, agent_alarm_id, things_cloud_alarm_id):
        alarm_set = AlarmSet(agent_alarm_id, things_cloud_alarm_id)
        self.array.append(alarm_set)

    def get(self, agent_alarm_id):
        for alarm_set in self.array:
            if alarm_set.equals(agent_alarm_id):
                return alarm_set.things_cloud_alarm_id()

    def remove(self, agent_alarm_id):
        for alarm_set in self.array:
            if alarm_set.equals(agent_alarm_id):
                self.remove(alarm_set)
                return

    def __init__(self):
        self.array = []

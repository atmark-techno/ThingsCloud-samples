class Operation:
    def status(self):
        return self.__status

    def parameters(self):
        return self.__parameters

    def id(self):
        return self.__id

    def command(self):
        return self.__command

    def spec(self):
        return self.__spec

    def set_status(self, status):
        self.__status = status

    def set_parameters(self, parameters):
        self.__parameters = parameters

    def set_spec(self, spec):
        self.__spec = spec

    def add_parameters(self, parameters):
        self.__parameters.update(parameters)

    def add_spec(self, spec):
        self.__spec.update(spec)

    def into_raw(self):
        raw = {
            'id': self.__id,
            'status': self.__status,
            self.__command: {}
        }
        raw.update(self.__spec)
        raw[self.__command].update(self.__parameters)
        return raw

    def __init__(self, op_id, status, spec, command, parameters):
        self.__id = op_id
        self.__status = status
        self.__spec = spec
        self.__command = command
        self.__parameters = parameters

    @classmethod
    def from_raw(cls, data, include_spec=True):
        op_id = data['id']
        status = data['status']
        c8y_keys = [key for key in data.keys() if key.startswith('c8y_')]
        if len(c8y_keys) == 0:
            return None
        command = c8y_keys[0]
        parameters = data[command]
        if include_spec:
            spec = {
                key: data[key]
                for key in data if key not in ('id', 'status', command)
            }
        else:
            spec = {}
        return cls(op_id, status, spec, command, parameters)

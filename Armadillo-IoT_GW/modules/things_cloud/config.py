import json


class ThingsCloudConfig:
    @classmethod
    def from_file(cls, filename):
        config = cls(origin_file=filename)

        with open(filename, 'r') as f:
            config.load_str(f)

        return config

    def __init__(self, origin_file=None):
        self.__origin_file = origin_file
        self.username = None
        self.password = None
        self.host = None
        self.tenant = None

    def load_str(self, config_str):
        config_json = json.load(config_str)
        self.username = config_json.get('username', None)
        self.password = config_json.get('password', None)
        self.host = config_json['host']
        self.tenant = config_json['tenant']

    def __str__(self):
        return json.dumps({
            'username': self.username,
            'password': self.password,
            'host': self.host,
            'tenant': self.tenant,
        })

    def update(self, username, password):
        if self.__origin_file is None:
            return

        f = open(self.__origin_file, 'w')
        cloud_config = {
            'host': self.host,
            'tenant': self.tenant,
            'username': username,
            'password': password
        }
        f.write(json.dumps(cloud_config, indent=4))
        f.close()


    def is_valid(self):
        fields = (self.host, self.tenant)
        return None not in fields

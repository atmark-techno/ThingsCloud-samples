import os
import json
import requests
import sys
from modules.operators.user_led_operator import UserLedOperator
from modules.things_cloud.alarm_set import AlarmSetArray
from modules.things_cloud.operation_handler import OperationHandler
from modules.things_cloud.operation import Operation
from modules.const import Const

''' use to show rest log
import logging
'''

REST_LOG = False

def optional_or(a, b):
    return a if a is not None else b


def is_json_format(config):
    try:
        json.loads(config)
        return True
    except json.JSONDecodeError:
        return False


def has_method(object, method):
    return hasattr(object, method) and callable(getattr(object, method))


class AuthorizedJSONRequest:
    CODE = b'ZGV2aWNlYm9vdHN0cmFwOkZoZHQxYmIxZg=='

    @staticmethod
    def __default_headers():
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'charset': 'UTF-8',
        }

    def __default_headers_with_cert(self):
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'charset': 'UTF-8',
            'Authorization': 'Basic ' + self.CODE.decode('utf-8')
        }

    def __auth(self):
        return requests.auth.HTTPBasicAuth(self.username, self.password)

    def get(self, url, headers=None):
        if self.username is None:
            return requests.get(
                url,
                headers=optional_or(headers,
                                    self.__default_headers_with_cert()),
            )
        else:
            return requests.get(
                url,
                headers=optional_or(headers, self.__default_headers()),
                auth=self.__auth(),
            )

    def post(self, url, payload, headers=None):
        if self.username is None:
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=optional_or(headers,
                                    self.__default_headers_with_cert()),
            )
            if self.__rest_log:
                print(response)
            return response
        else:
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers=optional_or(headers, self.__default_headers()),
                auth=self.__auth(),
            )
            if self.__rest_log:
                print(response)
            return response

    def post_with_file(self, url, data, files):
        headers = {
            'Accept': 'application/json',
        }
        return requests.post(
            url,
            headers=headers,
            auth=self.__auth(),
            data=data,
            files=files
        )

    def put(self, url, payload, headers=None):
        response = requests.put(
            url,
            data=json.dumps(payload),
            headers=optional_or(headers, self.__default_headers()),
            auth=self.__auth(),
        )
        if self.__rest_log:
            data = response.json()
            print(data)
        return response

    def set_default_cert(self):
        self.username = None
        self.password = None

    def set_cert(self, username, password):
        self.username = username
        self.password = password

    def __init__(self, username, password):
        self.__rest_log = REST_LOG
        if None in (username, password):
            self.set_default_cert()
        else:
            self.set_cert(username, password)


class ThingsCloudDevice:
    def construct_url(self, *paths):
        path = '/'.join(path.strip('/') for path in paths)
        return ('{}://{}.{}/{}'
                .format(self.scheme, self.tenant, self.host, path))

    def get_device_id(self):
        managed_object = self.get_managed_object()
        if managed_object is None:
            return None

        return managed_object['id']

    def get_managed_object(self):
        endpoint = self.construct_url(
            '/identity/externalIds/c8y_Serial',
            self.unique_id
        )

        try:
            response = self.request.get(endpoint)
            status_code = response.status_code

            if status_code == 200:
                data = response.json()
                if self.__rest_log:
                    print(data)
                return data['managedObject']
            elif status_code == 404:
                return None
            else:
                raise Exception('Unexpected status code {}'
                                .format(status_code))
        except Exception as e:
            print('exception occured:', e)
            sys.exit(1)

    def led_str(self):
        return 'OPEN' if self.__user_led.status() else 'CLOSED'

    def led_on(self):
        self.__user_led.on()

    def led_off(self):
        self.__user_led.off()

    def register_device_credential(self):
        headers = {
            'Content-Type': 'application/vnd.com.nsn.cumulocity.deviceCredentials+json',
            'Accept': 'application/vnd.com.nsn.cumulocity.deviceCredentials+json',
            'Authorization': 'Basic ' + self.request.CODE.decode('utf-8')
        }
        endpoint = self.construct_url('/devicecontrol/deviceCredentials')
        device_id = self.unique_id
        payload = {
            'id': device_id,
        }

        try:
            response = self.request.post(endpoint, payload, headers=headers)

            if response.status_code == 201:
                data = response.json()
                if self.__rest_log:
                    print(data)
                self.request.set_cert(data['username'], data['password'])
                self.update_config_callback(data['username'], data['password'])
                return True
            else:
                print('register_device_credential error status_code:',
                      response.status_code)
                sys.exit(1)
        except Exception as e:
            print('exception occured:', e)
            sys.exit(1)

    def register_device(self, **kwargs):
        model_name = 'Armadillo-IoT Gateway' # default

        try:
            with open(Const.MODEL_NAME_PATH) as f:
                model_name = f.read()
        except Exception as e:
            print(e)

        device_name = kwargs.get('device_name', model_name)
        supported_operations = kwargs.get('supported_operations', [])
        supported_logs = kwargs.get('supported_logs', [])
        offline_after = kwargs.get('offline_after', [])

        endpoint = self.construct_url('/inventory/managedObjects')

        params_str = str(self.__params)

        payload = {
            'name': device_name,
            'c8y_IsDevice': {},
            'type': 'IoT Gateway',
            'com_cumulocity_model_Agent': {},
            'c8y_SupportedOperations': supported_operations,
            'c8y_SupportedLogs': supported_logs,
            'c8y_Display': {},
            'c8y_RequiredAvailability': {
                'responseInterval': offline_after
            },
            'c8y_Configuration': {
                'config': params_str
            },
            'c8y_Relay': {
                'relayState': self.led_str()
            },
        }

        try:
            response = self.request.post(endpoint, payload)

            if response.status_code != 201:
                print(
                    'Failed to register this device: {}'
                    .format(response.status_code))
                return False

            data = response.json()
            if self.__rest_log:
                print(data)
            self.__device_id = data['id']
            print('Successfully registered this device')

            return True
        except Exception as e:
            print('exception occured:', e)
            return False

    def register_serial(self):
        endpoint = self.construct_url(
            '/identity/globalIds/' + self.__device_id + '/externalIds')

        payload = {
            'type': 'c8y_Serial',
            'externalId': self.unique_id
        }

        try:
            response = self.request.post(endpoint, payload)

            if response.status_code != 201:
                print('Could not add device identification by unique serial')
                return False

            if self.__rest_log:
                data = response.json()
                print(data)
            return True
        except Exception as e:
            print('exception occured:', e)
            return False

    def post_measurement(self, measurement):
        endpoint = self.construct_url('/measurement/measurements')

        try:
            response = self.request.post(endpoint, measurement)

            if response.status_code == 201:
                if self.__rest_log:
                    data = response.json()
                    print('*** mesurement response ***')
                    print(data)
                return True
            else:
                print('Failed to post the measurement')
                print('The response was {}'.format(response.text))
                return False
        except Exception as e:
            print('exception occured:', e)
            return False

    def post_measurements(self, mesurements):
        endpoint = self.construct_url('/measurement/measurements')
        headers = {
            'Content-Type':
                'application/vnd.com.nsn.cumulocity.measurementCollection+json',
            'Accept': 'application/json',
            'charset': 'UTF-8',
        }

        payload = {
            'measurements': mesurements
        }

        try:
            response = self.request.post(endpoint, payload, headers=headers)

            if response.status_code == 201:
                data = response.json()
                if self.__rest_log:
                    print('*** mesurements response ***')
                    print(data)
                return True
            else:
                print('Failed to post the measurement')
                print('The response was {}'.format(response.text))
                return False
        except Exception as e:
            print('exception occured:', e)
            return False

    def post_log(self, operation, file_path):
        if file_path is None:
            print('no file path')
            operation.set_status('FAILED')
            return

        endpoint = self.construct_url('/inventory/binaries')
        objects = {
                    'name': os.path.basename(file_path),
                    'type': 'text/plain'
                  }
        objects_data = json.dumps(objects)
        data = dict(
            object=objects_data,
            filesize=os.path.getsize(file_path),
        )
        files = dict(
            file=open(file_path, 'r')
        )

        try:
            response = self.request.post_with_file(endpoint, data, files)
            if response.status_code == 201:
                json_data = response.json()
                if self.__rest_log:
                    print('*** post log response ***')
                    print(json_data)
                file_url = json_data['self']
                parameters = operation.parameters()
                parameters['file'] = file_url
                operation.set_parameters(parameters)
            else:
                operation.set_status('FAILED')
        except Exception as e:
            print('exception occured:', e)
            operation.set_status('FAILED')

    def post_config(self):
        params_str = str(self.__params)
        config_json = {
            'c8y_Configuration': {
                'config': params_str
            }
        }

        endpoint = self.construct_url('/inventory/managedObjects/',
                                      self.__device_id)

        try:
            response = self.request.put(endpoint, config_json)

            if response.status_code != 200:
                print('could not update config:', response.status_code)
                return False

            if self.__rest_log:
                data = response.json()
                print('*** post config response ***')
                print(data)
            return True
        except Exception as e:
            print('exception occured:', e)
            return False

    def post_led(self):
        status = {
            'c8y_Relay': {
                'relayState': self.led_str()
            }
        }
        endpoint = self.construct_url('/inventory/managedObjects/',
                                      self.__device_id)

        try:
            response = self.request.put(endpoint, status)

            if response.status_code != 200:
                print('could not update LED status:', response.status_code)
                return False

            return True
        except Exception as e:
            print('exception occured:', e)
            return False

    def activate_alarm(self, alarm):
        endpoint = self.construct_url('/alarm/alarms')

        headers = {
            'Content-Type': 'application/vnd.com.nsn.cumulocity.alarm+json',
            'Accept': 'application/json',
            'charset': 'UTF-8'
        }

        payload = alarm.to_dict(self.managed_object, status='ACTIVE')

        try:
            response = self.request.post(endpoint, payload, headers=headers)

            if response.status_code != 201:
                print(
                    'Failed to update the status of alarm with status code: {}'
                    .format(response.status_code)
                )
                return False

            data = response.json()
            if self.__rest_log:
                print('*** alarm post response ***')
                print(data)
            alarm_id = data['id']
            print('Successfully activated alarm id:', alarm_id)
            self.__alarm_array.append(alarm.alarm_id, alarm_id)
            return True
        except Exception as e:
            print('exception occured:', e)
            return False

    def deactivate_alarm(self, alarm):
        alarm_id = self.__alarm_array.get(alarm.alarm_id)
        endpoint = self.construct_url('/alarm/alarms/'+str(alarm_id))
        payload = {
            'status': 'CLEARED'
        }

        headers = {
            'Content-Type': 'application/vnd.com.nsn.cumulocity.alarm+json',
            'Accept': 'application/json',
            'charset': 'UTF-8'
        }

        try:
            response = self.request.put(endpoint, payload, headers=headers)

            if response.status_code not in [200, 202]:
                print(
                    'Failed to update the status of alarm with status code: {}'
                    .format(response.status_code)
                )
                return False

            self.__alarm_array.remove(alarm.alarm_id)

            if self.__rest_log:
                data = response.json()
                print('*** alarm clear put response ***')
                print(data)

            print('Successfully deactivated alarm')
            return True
        except Exception as e:
            print('exception occured:', e)
            return False

    OPERATIONS_DEFAULTKEYS = [u'status', u'description', u'self',
                              u'creationTime', u'deviceId', u'id']

    def get_operations(self, status):
        if status not in ['', 'PENDING', 'EXECUTING', 'SUCCESSFUL', 'FAILED']:
            raise Exception('Unknown status "{:s}" queried'
                            .format(status))

        endpoint = self.construct_url(
            '/devicecontrol/operations?deviceId={}&status={}'
            .format(self.__device_id, status))

        try:
            response = self.request.get(endpoint)

            if response.status_code == 200:
                data = response.json()

                if self.__rest_log:
                    print('*** pending operation ***')
                    print(data)

                if 'operations' in data:
                    operations = [
                        Operation.from_raw(operation, include_spec=False)
                        for operation in data['operations']
                    ]
                    return [x for x in operations if x is not None]
                return None

            return None
        except Exception as e:
            print('exception occured:', e)
            return None

    def save_operation(self, operation):
        endpoint = self.construct_url(
            '/devicecontrol/operations/{}'.format(operation.id())
        )

        payload = operation.into_raw()

        try:
            response = self.request.put(endpoint, payload)

            if response.status_code != 200:
                print('could not save operation {}'.format(operation.id()))
                return False

            if self.__rest_log:
                data = response.json()
                print('*** save operation response ***')
                print(data)
            return True
        except Exception as e:
            print('exception occured:', e)
            return False

    def clean_restart_operations(self):
        operations = self.get_operations('EXECUTING')
        if operations:
            for o in operations:
                if 'c8y_Restart' == o.command():
                    o.set_status('SUCCESSFUL')
                    self.save_operation(o)

    def dispatch_operation(self):
        operations = self.get_operations('PENDING')
        if operations is None:
            return False

        for operation in operations:
            command = operation.command()
            # print('try to dispatch operation:', command)
            if has_method(OperationHandler, command):
                # print('run operation command:', command)
                handler = getattr(OperationHandler, command)
                handler(operation, self)

                self.save_operation(operation)

                if operation.command() == 'c8y_Restart':
                    OperationHandler.reboot()
            else:
                print('OperationHandler cannot handle the operation')
                operation.set_status('FAILED')
                self.save_operation(operation)

    def device_id(self):
        return self.__device_id

    def handle_c8y_Configuration(self, operation):
        config = operation.parameters()['config']
        if is_json_format(config):
            self.update_params_callback(config)
            operation.set_status('SUCCESSFUL')
        else:
            operation.set_status('FAILED')
        return

    def __init__(
        self,
        config,
        update_config_callback,
        params,
        update_params_callback,
        unique_id,
        led,
        scheme='https'
    ):
        if not config.is_valid():
            raise Exception("The config is invalid: some fields are not set!")

        self.update_config_callback = update_config_callback
        self.update_params_callback = update_params_callback
        self.scheme = scheme
        self.tenant = config.tenant
        self.host = config.host
        self.unique_id = unique_id
        self.request = AuthorizedJSONRequest(config.username, config.password)
        self.__params = params
        self.__alarm_array = AlarmSetArray()
        self.__user_led = led

        self.__rest_log = REST_LOG

        ''' use to show rest log
        import http.client as http_client
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True
        '''

        self.managed_object = self.get_managed_object()
        self.__device_id = self.get_device_id()
        if self.__device_id is None:
            self.request.set_default_cert()
            self.register_device_credential()
            successful = self.register_device(
                supported_operations=[
                    'c8y_Restart',
                    'c8y_Configuration',
                    'c8y_SendConfiguration',
                    'c8y_Command',
                    'c8y_LogfileRequest',
                    'c8y_Relay'
                ],
                supported_logs=['dmesg', 'syslog'],
                offline_after=600
            )
            if not successful:
                raise Exception('Unexpected error')
            successful = self.register_serial()
        else:
            self.clean_restart_operations()
            self.post_config()
            self.post_led()

import os
import re
from datetime import datetime
from subprocess import check_output, call
from modules.const import Const
from modules.lib.agent_utils import run_on_bash
from modules.lib.loopable import Loopable


def parse_parameters(operation, string):
    if string in operation.parameters():
        parameters = operation.parameters()
        return parameters[string]
    else:
        return None


def filter_and_cut_lines(lines, search_text, max_lines):
    return [line for line in lines
            if (search_text is None) or (search_text in line)][0:max_lines]


def dmesg_date(line):
    pattern = '\\[ *([^\\]]+) *\\]'
    matched = re.match(pattern, line)
    if matched is None:
        return None
    date = matched.groups()[0]
    parsed_date = datetime.strptime(date, '%a %b %d %H:%M:%S %Y')
    return parsed_date


def dmesg_file(date_from, date_to, search_text, max_lines):
    (_, log) = run_on_bash('dmesg -T')

    parsed = ((dmesg_date(line), line) for line in log.split('\n'))
    lines = [line for (date, line) in parsed
             if date is not None
             and date_from <= date <= date_to]
    filtered = filter_and_cut_lines(lines, search_text, max_lines)
    log = '\n'.join(filtered)

    os.makedirs(Const.LOG_DIR, exist_ok=True)
    with open(Const.DMESG_PATH, 'w') as f:
        f.write(log)

    return Const.DMESG_PATH


def syslog_date(line):
    date = line[:15]
    try:
        return datetime.strptime(date, '%b %d %H:%M:%S')
    except ValueError:
        return None


def is_in_period_syslog(now, date_from, date_to, is_reverse):
    now = now.replace(year=2020)
    if is_reverse:
        if date_from <= now and now <= date_to:
            return True

        now = now.replace(year=2019)
        return date_from <= now and now <= date_to
    else:
        return date_from <= now and now <= date_to


'''
    syslog には年がないのである程度でフィルタリングする
'''


'''
    syslog has not year string, put temp year 2020 or 2019.
'''
def syslog_file(date_from, date_to, search_text, max_lines):
    log = []
    count = 0
    is_over_year = False
    is_reverse = False

    if date_from.year + 1 == date_to.year:
        if date_from.month == date_to.month:
            if date_from.day == date_to.day:
                if date_from.hour == date_to.hour:
                    if date_from.minute > date_to.minute:
                        is_reverse = True
                    else:
                        is_over_year = True
                elif date_from.hour > date_to.hour:
                    is_reverse = True
                else:
                    is_over_year = True
            elif date_from.day > date_to.day:
                is_reverse = True
            else:
                is_over_year = True
        elif date_from.month > date_to.month:
            is_reverse = True
        else:
            is_over_year = True
    elif date_from.year < date_to.year:
        is_over_year = True

    if is_reverse:
        print('is reverse')
        date_from = date_from.replace(year=2019)
        date_to = date_to.replace(year=2020)
    elif is_over_year:
        print('is over year')
        date_from = date_from.replace(year=2020)
        date_to = date_to.replace(year=2020)
    else:
        date_from = date_from.replace(year=2020)
        date_to = date_to.replace(year=2020)

    try:
        with open(Const.SYSLOG_ORIG_PATH, 'r', errors='ignore') as f:
            for line in f:
                date = syslog_date(line)
                if date is None:
                    continue

                if not is_over_year and \
                    not is_in_period_syslog(date, date_from, date_to, is_reverse):
                    continue

                if (search_text is None) or (search_text in line):
                    log.append(line)
                    count += 1

                if count >= max_lines:
                    break

    except Exception as e:
        print(e)

    if count == 0:
        return None

    os.makedirs(Const.LOG_DIR, exist_ok=True)
    try:
        with open(Const.SYSLOG_PATH, 'w') as f:
            f.write(''.join(log))
    except Exception as e:
        print(e)


    return Const.SYSLOG_PATH


def parse_iso_date(date):
    output = check_output(['date', '-d', date, '+%s'])
    return datetime.fromtimestamp(int(output.decode('utf-8')))


class OperationDispatcher(Loopable):
    def __init__(self, device, interval):
        super().__init__(interval)
        self.__device = device

    async def routine(self):
        self.__device.dispatch_operation()


class OperationHandler:
    @staticmethod
    def c8y_Restart(operation, device):
        print('run operation cy8_Restart')

        # check has 'reboot' command
        output = None
        (returncode, output) = run_on_bash('which reboot')
        if returncode != 0:
            operation.set_status('FAILED')
            return

        operation.set_status('EXECUTING')

    @staticmethod
    def reboot():
        call('reboot')

    @staticmethod
    def c8y_Command(operation, device):
        CMD_KEY = 'text'
        print('run operation c8y_Command')

        parameters = operation.parameters()

        if CMD_KEY not in parameters:
            print('could not find command in operation')
            print('update operation to failed')

            operation.add_spec({
                'error': 'missing key {} in operation'.format(CMD_KEY)
            })
            operation.set_status('FAILED')
            return

        cmd = parameters[CMD_KEY]

        # check if command includes '&' which could open another thread and
        # circumvent timeout system
        if '&' in cmd:
            print('do not run commands with "&"')
            error = (
                'character "&" found in command;'
                'multiple thread is forbidden to prevent circumventing timeout'
            )
            operation.add_spec({
                'error': error
            })
            operation.set_status('FAILED')
            return

        timeout = '15s'
        if 'timeout' in parameters:
            timeout = str(parameters['timeout'])

        (returncode, output) = run_on_bash(cmd, timeout=timeout)

        operation.set_parameters({
            CMD_KEY: cmd,
            'result': output,
        })
        operation.add_spec({
            'returncode': returncode
        })
        operation.set_status('SUCCESSFUL')

    @staticmethod
    def c8y_Configuration(operation, device):
        device.handle_c8y_Configuration(operation)
        device.post_config()
        return

    @staticmethod
    def c8y_SendConfiguration(operation, device):
        if device.post_config():
            operation.set_status('SUCCESSFUL')
        else:
            operation.set_status('FAILED')

    @staticmethod
    def c8y_LogfileRequest(operation, device):
        parameters = operation.parameters()
        log_file = parameters.get('logFile')
        date_from = parameters.get('dateFrom')
        date_to = parameters.get('dateTo')
        max_lines = parameters.get('maximumLines')
        search_text = parameters.get('searchText')

        if None in (log_file, date_from, date_to, max_lines):
            operation.add_spec({
                'error': 'parameter error.'
            })
            operation.set_status('FAILED')
            return

        log_getter = (
            dmesg_file if log_file == 'dmesg' else
            syslog_file if log_file == 'syslog'
            else None
        )

        if log_getter is None:
            print('unknown logFile: {}'.format(log_file))
            operation.add_spec({
                'error': 'unknown logFile type: {}'.format(log_file)
            })
            operation.set_status('FAILED')
            return

        date_from_parsed = parse_iso_date(date_from)
        date_to_parsed = parse_iso_date(date_to)
        log_file = log_getter(date_from_parsed, date_to_parsed,
                              search_text, max_lines)
        if log_file is None:
            operation.set_status('FAILED')
        else:
            operation.set_status('SUCCESSFUL')
            device.post_log(operation, log_file)

    @staticmethod
    def c8y_Relay(operation, device):
        status = parse_parameters(operation, 'relayState')
        if status == 'OPEN':
            device.led_on()
            operation.set_status('SUCCESSFUL')
        elif status == 'CLOSED':
            device.led_off()
            operation.set_status('SUCCESSFUL')
        else:
            operation.set_status('FAILED')

        device.post_led()

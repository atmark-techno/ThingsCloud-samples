class Const:
    SYSLOG_ORIG_PATH = '/var/log/syslog'
    LOG_DIR = '/tmp/things_cloud/'
    SYSLOG_PATH = LOG_DIR + 'syslog.log'
    DMESG_PATH = LOG_DIR + 'dmesg.log'
    DEFAULT_CLOUD_REPORT_INTERVAL_SEC = 30
    SLEEP_NO_REPORT_SEC = 10
    BULK_REPORT_COUNT = 20
    MODEL_NAME_PATH = '/proc/device-tree/model'

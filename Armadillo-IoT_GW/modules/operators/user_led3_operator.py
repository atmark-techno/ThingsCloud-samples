from modules.lib.agent_utils import run_on_bash


class UserLed3Operator:
    PATH = '/sys/class/leds/led3/'
    BRIGHTNESS = PATH + 'brightness'
    TRIGGER = PATH + 'trigger'
    DELAY_ON = PATH + 'delay_on'
    DELAY_OFF = PATH + 'delay_off'
    INVERT = PATH + 'invert'
    def on(self):
       run_on_bash('echo none > ' + self.TRIGGER)
       run_on_bash('echo 1 > ' + self.BRIGHTNESS)

    def off(self):
       run_on_bash('echo none > ' + self.TRIGGER)
       run_on_bash('echo 0 > ' + self.BRIGHTNESS)

    def blink(self):
       run_on_bash('echo timer > ' + self.TRIGGER)
       run_on_bash('echo 100 > ' + self.DELAY_ON)
       run_on_bash('echo 100 > ' + self.DELAY_OFF)

    def blink_twice(self):
       run_on_bash('echo heartbeat > ' + self.TRIGGER)
       run_on_bash('echo 1 > ' + self.INVERT)

    def set_default(self):
        run_on_bash('echo default-on > ' + self.TRIGGER)

    def status(self):
       (returncode, output) = run_on_bash('cat ' + self.BRIGHTNESS)
       return True if int(output) == 1 else False

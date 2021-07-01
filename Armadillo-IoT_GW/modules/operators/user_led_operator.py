class UserLedOperator():

    def __init__(self, path):
        self.brightness = path + 'brightness'
        self.trigger = path + '/' + 'trigger'
        self.delay_on = path + '/' + 'delay_on'
        self.delay_off = path + '/' + 'delay_off'
        self.invert = path + '/' + 'invert' 

    def __set_value(self, path, value):
        with open(path, mode='w') as f:
            f.write(value)

    def __value(self, path):
        value = 0
        try:
            with open(path) as f:
                value = f.read()
        except Exception as e:
            print(e)

        return value

    def on(self):
        self.__set_value(self.trigger, 'none')
        self.__set_value(self.brightness, '1')

    def off(self):
        self.__set_value(self.trigger, 'none')
        self.__set_value(self.brightness, '0')

    def blink(self):
        self.__set_value(self.trigger, 'timer')
        self.__set_value(self.delay_on, '100')
        self.__set_value(self.delay_off, '100')

    def blink_twice(self):
        self.__set_value(self.trigger, 'heartbeat')
        self.__set_value(self.invert, '1')

    def set_default(self):
        self.__set_value(self.trigger, 'default-on')

    def status(self):
       return True if int(self.__value(self.brightness)) == 1 else False

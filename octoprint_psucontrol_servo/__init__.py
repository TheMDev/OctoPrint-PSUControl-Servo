# coding=utf-8
from __future__ import absolute_import

from time import sleep

import octoprint.plugin


class PSUControlServo(octoprint.plugin.StartupPlugin,
                      octoprint.plugin.RestartNeedingPlugin,
                      octoprint.plugin.TemplatePlugin,
                      octoprint.plugin.SettingsPlugin):

    def __init__(self):
        try:
            global GPIO
            import RPi.GPIO as GPIO
            self._hasGPIO = True
        except (ImportError, RuntimeError):
            self._hasGPIO = False

        self._pin_to_gpio_rev1 = [-1, -1, -1, 0, -1, 1, -1, 4, 14, -1, 15, 17, 18, 21, -1, 22, 23, -1, 24, 10,
                                  -1, 9, 25, 11, 8, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        self._pin_to_gpio_rev2 = [-1, -1, -1, 2, -1, 3, -1, 4, 14, -1, 15, 17, 18, 27, -1, 22, 23, -1, 24, 10,
                                  -1, 9, 25, 11, 8, -1, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        self._pin_to_gpio_rev3 = [-1, -1, -1, 2, -1, 3, -1, 4, 14, -1, 15, 17, 18, 27, -1, 22, 23, -1, 24, 10,
                                  -1, 9, 25, 11, 8, -1, 7, -1, -1, 5, -1, 6, 12, 13, -1, 19, 16, 26, 20, -1, 21]

        self.config = dict()

        self._configuredGPIOPins = []

    def get_settings_defaults(self):
        return dict(
            GPIOMode='BOARD',
            GPIOServoPin=0,
            GPIOServoFreq=50,
            GPIOServoMode='',
            GPIOServoOn=6.0,
            GPIOServoOff=8.0,
            GPIOServoIdle=7.0,
            GPIOServoTime=1.0,
            GPIOSensePin=0,
            GPIOSenseInvert=False,
            GPIOSensePinPull=''
        )

    def on_settings_initialized(self):
        self.reload_settings()
        self.configure_gpio()

    def reload_settings(self):
        for k, v in self.get_settings_defaults().items():
            if type(v) == str:
                v = self._settings.get([k])
            elif type(v) == int:
                v = self._settings.get_int([k])
            elif type(v) == float:
                v = self._settings.get_float([k])
            elif type(v) == bool:
                v = self._settings.get_boolean([k])

            self.config[k] = v
            self._logger.debug("{}: {}".format(k, v))

    def on_startup(self, host, port):
        psucontrol_helpers = self._plugin_manager.get_helpers("psucontrol")
        if not psucontrol_helpers or 'register_plugin' not in psucontrol_helpers.keys():
            self._logger.warning("The version of PSUControl that is installed does not support plugin registration.")
            return

        self._logger.debug("Registering plugin with PSUControl")
        psucontrol_helpers['register_plugin'](self)

    def _gpio_board_to_bcm(self, pin):
        if GPIO.RPI_REVISION == 1:
            pin_to_gpio = self._pin_to_gpio_rev1
        elif GPIO.RPI_REVISION == 2:
            pin_to_gpio = self._pin_to_gpio_rev2
        else:
            pin_to_gpio = self._pin_to_gpio_rev3

        return pin_to_gpio[pin]

    def _gpio_bcm_to_board(self, pin):
        if GPIO.RPI_REVISION == 1:
            pin_to_gpio = self._pin_to_gpio_rev1
        elif GPIO.RPI_REVISION == 2:
            pin_to_gpio = self._pin_to_gpio_rev2
        else:
            pin_to_gpio = self._pin_to_gpio_rev3

        return pin_to_gpio.index(pin)

    def _gpio_get_pin(self, pin):
        if (GPIO.getmode() == GPIO.BOARD and self.config['GPIOMode'] == 'BOARD') or (GPIO.getmode() == GPIO.BCM and self.config['GPIOMode'] == 'BCM'):
            return pin
        elif GPIO.getmode() == GPIO.BOARD and self.config['GPIOMode'] == 'BCM':
            return self._gpio_bcm_to_board(pin)
        elif GPIO.getmode() == GPIO.BCM and self.config['GPIOMode'] == 'BOARD':
            return self._gpio_board_to_bcm(pin)
        else:
            return 0

    def configure_gpio(self):
        if not self._hasGPIO:
            self._logger.error("Error importing RPi.GPIO.")
            return

        self._logger.info("Running RPi.GPIO version {}".format(GPIO.VERSION))
        if GPIO.VERSION < "0.6":
            self._logger.error("RPi.GPIO version 0.6.0 or greater required.")
            return

        GPIO.setwarnings(False)

        if GPIO.getmode() is None:
            if self.config['GPIOMode'] == 'BOARD':
                GPIO.setmode(GPIO.BOARD)
            elif self.config['GPIOMode'] == 'BCM':
                GPIO.setmode(GPIO.BCM)
            else:
                return

        if self.config['GPIOSensePin'] > 0:
            self._logger.info("Configuring sensing GPIO for pin {}".format(self.config['senseGPIOPin']))

            if self.config['GPIOSensePinPull'] == 'PULL_UP':
                pull_up_down = GPIO.PUD_UP
            elif self.config['GPIOSensePinPull'] == 'PULL_DOWN':
                pull_up_down = GPIO.PUD_DOWN
            else:
                pull_up_down = GPIO.PUD_OFF

            try:
                GPIO.setup(self._gpio_get_pin(self.config['GPIOSensePin']), GPIO.IN, pull_up_down=pull_up_down)
                self._configuredGPIOPins.append(self.config['GPIOSensePin'])
            except Exception:
                self._logger.exception(
                    "Exception while setting up GPIO pin {}".format(self.config['GPIOSensePin'])
                )

        if self.config['GPIOServoPin'] > 0:
            self._logger.info("Configuring Servo GPIO for pin {}".format(self.config['GPIOServoPin']))
            try:
                GPIO.setup(self._gpio_get_pin(self.config['GPIOServoPin']), GPIO.OUT)
                self._configuredGPIOPins.append(self.config['GPIOServoPin'])
            except Exception:
                self._logger.exception(
                    "Exception while setting up GPIO pin {}".format(self.config['GPIOServoPin'])
                )

    def cleanup_gpio(self):
        GPIO.setwarnings(False)

        for pin in self._configuredGPIOPins:
            self._logger.debug("Cleaning up pin {}".format(pin))
            try:
                GPIO.cleanup(self._gpio_get_pin(pin))
            except Exception:
                self._logger.exception(
                    "Exception while cleaning up GPIO pin {}".format(pin)
                )
        self._configuredGPIOPins = []

    def turn_psu_on(self):
        if self.config['GPIOServoPin'] <= 0:
            self._logger.warning("Switching is not enabled")
            return

        self._logger.debug("Switching PSU On Using GPIO: {}".format(self.config['GPIOServoPin']))
        try:
            pwm = GPIO.PWM(self.config['GPIOServoPin'], self.config['GPIOServoFreq'])
            pwm.start(0)
            pwm.ChangeDutyCycle(self.config['GPIOServoOn'])
            sleep(self.config['GPIOServoTime'])

            if self.config['GPIOServoMode'] == 'BUTTON':
                pwm.ChangeDutyCycle(self.config['GPIOServoIdle'])
                sleep(self.config['GPIOServoTime'])
                self._logger.debug("Servo Mode: {}".format(self.config['GPIOServoMode']))
            elif self.config['GPIOServoMode'] == 'SWITCH':
                self._logger.debug("Servo Mode: {}".format(self.config['GPIOServoMode']))

            pwm.stop()
        except Exception:
            self._logger.exception("Exception while writing GPIO line")

    def turn_psu_off(self):
        if self.config['GPIOServoPin'] <= 0:
            self._logger.warning("Switching is not enabled")
            return

        self._logger.debug("Switching PSU On Using GPIO: {}".format(self.config['GPIOServoPin']))
        try:
            pwm = GPIO.PWM(self.config['GPIOServoPin'], self.config['GPIOServoFreq'])
            pwm.start(0)
            pwm.ChangeDutyCycle(self.config['GPIOServoOff'])
            sleep(self.config['GPIOServoTime'])

            if self.config['GPIOServoMode'] == 'BUTTON':
                pwm.ChangeDutyCycle(self.config['GPIOServoIdle'])
                sleep(self.config['GPIOServoTime'])
                self._logger.debug("Servo Mode: {}".format(self.config['GPIOServoMode']))
            elif self.config['GPIOServoMode'] == 'SWITCH':
                self._logger.debug("Servo Mode: {}".format(self.config['GPIOServoMode']))

            pwm.stop()
        except Exception:
            self._logger.exception("Exception while writing GPIO line")

    def get_psu_state(self):
        if self.config['GPIOSensePin'] <= 0:
            self._logger.warning("Sensing is not enabled")
            return 0

        r = 0
        try:
            r = GPIO.input(self._gpio_get_pin(self.config['GPIOSensePin']))
        except Exception:
            self._logger.exception("Exception while reading GPIO line")
            return False
        self._logger.debug("Result: {}".format(r))
        r = bool(r)

        if self.config['GPIOSenseInvert']:
            r = not r

        return r

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        self.reload_settings()

        self.cleanup_gpio()
        self.configure_gpio()

    def get_settings_version(self):
        return 1

    def on_settings_migrate(self, target, current=None):
        pass

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=False)
        ]

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://docs.octoprint.org/en/master/bundledplugins/softwareupdate.html
        # for details.
        return {
            "psucontrol_servo": {
                "displayName": "PSU Control Servo",
                "displayVersion": self._plugin_version,

                # version check: github repository
                "type": "github_release",
                "user": "TheMDev",
                "repo": "OctoPrint-PSUControl-Servo",
                "current": self._plugin_version,

                # update method: pip
                "pip": "https://github.com/TheMDev/OctoPrint-PSUControl_Servo/archive/{target_version}.zip",
            }
        }


__plugin_name__ = "PSU Control Servo"
__plugin_pythoncompat__ = ">=3,<4"  # Only Python 3


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = PSUControlServo()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }

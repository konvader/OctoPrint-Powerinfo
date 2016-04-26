# coding=utf-8
from __future__ import absolute_import

import flask
import octoprint.plugin
from octoprint.util import RepeatedTimer
import re
import RPi.GPIO as GPIO
import sys

class PowerinfoPlugin(octoprint.plugin.StartupPlugin,
		      octoprint.plugin.SettingsPlugin,
                      octoprint.plugin.AssetPlugin,
                      octoprint.plugin.TemplatePlugin,
		      octoprint.plugin.SimpleApiPlugin):

	##~~ Intialization

	def __init__(self):
		self._checkPwrStatusTimer = None
		self.isRaspi = False
		self.pwrOnName = ""
		self.pwrOffName = ""
		self.pwrOneStatus = ""
		self.pwrTwoStatus = ""
		self.relayOneName = ""
		self.relayTwoName = ""
		self.rOneMessage = ""
		self.rTwoMessage = ""
		self.showPwrOneStatus = False
		self.showPwrTwoStatus = False

	##~~ StartupPlugin mixin

	def on_after_startup(self):
		# Get our settings
		self.pwrOnName = self._settings.get(["pwrOnName"])
		self.pwrOffName = self._settings.get(["pwrOffName"])
		self.relayOneName = self._settings.get(["relayOneName"])
		self.relayTwoName = self._settings.get(["relayTwoName"])
                self.showPwrOneStatus = self._settings.get(["showPwrOneStatus"])
                self.showPwrTwoStatus = self._settings.get(["showPwrTwoStatus"])

		self._logger.info("Powerinfo plugin started")

		if sys.platform == "linux2":
		    with open('/proc/cpuinfo', 'r') as infile:
			cpuinfo = infile.read()
		    # Search for the cpu info
		    match = re.search('^Hardware\s+:\s+(\w+)$', cpuinfo, flags=re.MULTILINE | re.IGNORECASE)

		    if match is None:
			# The hardware is not a pi.
			self.isRaspi = False
		    elif match.group(1) == 'BCM2708':
			self._logger.info("Pi 1")
			self.isRaspi = True
		    elif match.group(1) == 'BCM2709':
			self._logger.info("Pi 2")
			self.isRaspi = True
		    elif match.group(1) == 'BCM2710':
			self._logger.info("Pi 3")
			self.isRaspi = True

		    if self.showPwrOneStatus or self.showPwrTwoStatus and self.isRaspi:
			self._logger.info("Initialize GPOI")

			# Set GPIO layout like pin-number
			GPIO.setmode(GPIO.BOARD)

			# Disable GPIO warnings
			GPIO.setwarnings(False)

			# Initialize the GPIO after restart
                        GPIO.cleanup()

			# Configure our GPIO outputs
			GPIO.setup(11, GPIO.OUT)
			GPIO.setup(12, GPIO.OUT)

			# Setup the initial state to high(off)
			GPIO.output(11, GPIO.HIGH)
			GPIO.output(12, GPIO.HIGH)

			self._logger.info("Start the timer now")
			self.startTimer(10.0)

		self._logger.info("Running on Pi? - %s" % self.isRaspi)

	def startTimer(self, interval):
		self._checkPwrStatusTimer = RepeatedTimer(interval, self.checkPwrStatus, None, None, True)
		self._checkPwrStatusTimer.start()

	def checkPwrStatus(self):
		# Check the GPIO status of our relays and set our message
		self.pwrOneStatus = GPIO.input(11)
		if self.pwrOneStatus:
		    self.rOneMessage = "%s: %s" % (self.relayOneName, self.pwrOffName)
		else:
		    self.rOneMessage = "%s: %s" % (self.relayOneName, self.pwrOnName)

		self.pwrTwoStatus = GPIO.input(12)
		if self.pwrTwoStatus:
                    self.rTwoMessage = "%s: %s" % (self.relayTwoName, self.pwrOffName)
                else:
                    self.rTwoMessage = "%s: %s" % (self.relayTwoName, self.pwrOnName)

		# Sent our status message
		self._plugin_manager.send_plugin_message(self._identifier, dict(messageOne=self.rOneMessage,
										messageOneShow=self.showPwrOneStatus,
										messageTwo=self.rTwoMessage,
										messageTwoShow=self.showPwrTwoStatus))

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(pwrOnName="On",
			    pwrOffName="Off",
			    relayOneName="Printer“,
			    relayTwoName="Light“,
			    showPwrOneStatus=True,
			    showPwrTwoStatus=False)

	def on_settings_save(self,data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		self.pwrOnName = self._settings.get(["pwrOnName"])
		self.pwrOffName = self._settings.get(["pwrOffName"])
		self.relayOneName = self._settings.get(["relayOneName"])
		self.relayTwoName = self._settings.get(["relayTwoName"])
		self.showPwrOneStatus = self._settings.get(["showPwrOneStatus"])
		self.showPwrTwoStatus = self._settings.get(["showPwrTwoStatus"])

		if self.showPwrOneStatus or self.showPwrTwoStatus and self.isRaspi:
		    interval = 10.0
		    self.startTimer(interval)
		else:
		    if self._checkPwrStatusTimer is not None:
			try:
			    self._checkPwrStatusTimer.cancel()
			except:
			    pass
		    self._plugin_manager.send_plugin_message(self._identifier, dict())

	##~~ AssetPlugin mixin

	def get_assets(self):
		return dict(
			js=["js/powerinfo.js"]
		)

	##~~ TemplatePlugin mixin

	def get_template_configs(self):
	    if self.isRaspi:	
		return [
			dict(type="sidebar", name="Powerinfo", icon="info"),
			dict(type="settings", name="Powerinfo", custom_bindings=False)
		]
	    else:
		return [
		]

	##~~ SimpleApiPlugin mixin

	def on_api_get(self, request):
		return flask.jsonify(dict(
			messageOne=self.rOneMessage,
			messageOneShow=self.showPwrOneStatus,
			messageTwo=self.rTwoMessage,
			messageTwoShow=self.showPwrTwoStatus
		))

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			powerinfo=dict(
				displayName="Powerinfo Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="konvader",
				repo="OctoPrint-Powerinfo",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/konvader/OctoPrint-Powerinfo/archive/{target_version}.zip"
			)
		)

__plugin_name__ = "Powerinfo Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = PowerinfoPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

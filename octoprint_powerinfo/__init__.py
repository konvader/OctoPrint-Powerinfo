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
		self.inOnePin = ""
		self.inTwoPin = ""
		self.isRaspi = False
		self.pwrOnName = ""
		self.pwrOffName = ""
		self.pwrOneStatus = ""
		self.pwrTwoStatus = ""
		self.relayOneName = ""
		self.relayTwoName = ""
		self.rOneMessage = ""
		self.rRate = ""
		self.rTwoMessage = ""
		self.showPwrOneStatus = False
		self.showPwrTwoStatus = False

	##~~ StartupPlugin mixin

	def on_after_startup(self):
		# Get our settings
		self.inOnePin = int(self._settings.get(["inOnePin"]))
		self.inTwoPin = int(self._settings.get(["inTwoPin"]))
		self.pwrOnName = self._settings.get(["pwrOnName"])
		self.pwrOffName = self._settings.get(["pwrOffName"])
		self.relayOneName = self._settings.get(["relayOneName"])
		self.relayTwoName = self._settings.get(["relayTwoName"])
		self.rRate = int(self._settings.get(["rRate"]))
                self.showPwrOneStatus = self._settings.get(["showPwrOneStatus"])
                self.showPwrTwoStatus = self._settings.get(["showPwrTwoStatus"])

		# Update the plugin helpers
                __plugin_helpers__.update(dict(
                    inOnePin=self.inOnePin,
                    inTwoPin=self.inTwoPin,
                    relayOneName=self.relayOneName,
                    relayTwoName=self.relayTwoName,
                    showPwrOneRelay=self.showPwrOneStatus,
                    showPwrTwoRelay=self.showPwrTwoStatus
                ))

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
			self._logger.debug("Pi 1")
			self.isRaspi = True
		    elif match.group(1) == 'BCM2709':
			self._logger.debug("Pi 2")
			self.isRaspi = True
		    elif match.group(1) == 'BCM2710':
			self._logger.debug("Pi 3")
			self.isRaspi = True

		    if self.showPwrOneStatus or self.showPwrTwoStatus and self.isRaspi:
			self._logger.debug("Initialize GPOI")

			# Set GPIO layout like pin-number
			GPIO.setmode(GPIO.BOARD)

			# Configure our GPIO outputs
			GPIO.setup(self.inOnePin, GPIO.OUT)
			GPIO.setup(self.inTwoPin, GPIO.OUT)

			# Setup the initial state to high(off)
			GPIO.output(self.inOnePin, GPIO.HIGH)
			GPIO.output(self.inTwoPin, GPIO.HIGH)

			self._logger.debug("Start the timer now")
			self.startTimer(self.rRate)

		self._logger.debug("Running on Pi? - %s" % self.isRaspi)

	def startTimer(self, interval):
		self._checkPwrStatusTimer = RepeatedTimer(interval, self.checkPwrStatus, None, None, True)
		self._checkPwrStatusTimer.start()

	def checkPwrStatus(self):
		# Check the GPIO status of our relays and set our message
		self.pwrOneStatus = GPIO.input(self.inOnePin)
		if self.pwrOneStatus:
		    self.rOneMessage = "%s: %s" % (self.relayOneName, self.pwrOffName)
		else:
		    self.rOneMessage = "%s: %s" % (self.relayOneName, self.pwrOnName)

		self.pwrTwoStatus = GPIO.input(self.inTwoPin)
		if self.pwrTwoStatus:
                    self.rTwoMessage = "%s: %s" % (self.relayTwoName, self.pwrOffName)
                else:
                    self.rTwoMessage = "%s: %s" % (self.relayTwoName, self.pwrOnName)

		# Send our status message
		self._plugin_manager.send_plugin_message(self._identifier, dict(messageOne=self.rOneMessage,
										messageOneShow=self.showPwrOneStatus,
										messageTwo=self.rTwoMessage,
										messageTwoShow=self.showPwrTwoStatus))

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			inOnePin="11",
			inTwoPin="12",
			pwrOnName="On",
			pwrOffName="Off",
			relayOneName="Printer",
			relayTwoName="Light",
			rRate="10",
			showPwrOneStatus=True,
			showPwrTwoStatus=False
		)

	def on_settings_save(self,data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

		self.inOnePin = int(self._settings.get(["inOnePin"]))
		self.inTwoPin = int(self._settings.get(["inTwoPin"]))
		self.pwrOnName = self._settings.get(["pwrOnName"])
		self.pwrOffName = self._settings.get(["pwrOffName"])
		self.relayOneName = self._settings.get(["relayOneName"])
		self.relayTwoName = self._settings.get(["relayTwoName"])
		self.rRate = int(self._settings.get(["rRate"]))
		self.showPwrOneStatus = self._settings.get(["showPwrOneStatus"])
		self.showPwrTwoStatus = self._settings.get(["showPwrTwoStatus"])

		# Update the plugin helpers
		__plugin_helpers__.update(dict(
                    inOnePin=self.inOnePin,
                    inTwoPin=self.inTwoPin,
                    relayOneName=self.relayOneName,
                    relayTwoName=self.relayTwoName,
                    showPwrOneRelay=self.showPwrOneStatus,
                    showPwrTwoRelay=self.showPwrTwoStatus
                ))

		if self.showPwrOneStatus or self.showPwrTwoStatus and self.isRaspi:
		    # Initialize the GPIO after a setting change
                    GPIO.cleanup()

		    # Set GPIO layout like pin-number
                    GPIO.setmode(GPIO.BOARD)

                    # Configure our GPIO outputs
                    GPIO.setup(self.inOnePin, GPIO.OUT)
                    GPIO.setup(self.inTwoPin, GPIO.OUT)

                    # Setup the initial state to high(off)
                    GPIO.output(self.inOnePin, GPIO.HIGH)
                    GPIO.output(self.inTwoPin, GPIO.HIGH)

		    # Start the timer
		    self.startTimer(self.rRate)
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
	plugin = PowerinfoPlugin()

	global __plugin_implementation__
	__plugin_implementation__ = plugin

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}

	global __plugin_helpers__
        __plugin_helpers__ = dict(
            inOnePin=plugin.inOnePin,
            inTwoPin=plugin.inTwoPin,
            relayOneName=plugin.relayOneName,
            relayTwoName=plugin.relayTwoName,
            showPwrOneRelay=plugin.showPwrOneStatus,
            showPwrTwoRelay=plugin.showPwrTwoStatus
	)

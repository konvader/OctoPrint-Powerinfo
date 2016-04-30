# OctoPrint-Powerinfo

## Caution

You are playing around with mains voltage here. Mains can kill you!
Errors can be fatal, so if you do not know !exactly! what you are doing, you shouldn't be doing it!

## Description

Powerinfo is a plugin for OctoPi to monitor the state of a 2 channel relay card (e.g. SainSmart)
You are able to configure input and output values for each relay within the settings. Changes will
take effect as soon as you click the Save button inside the Settings section. It is compatible
to all hardware revision of Raspberry Pi including Pi3.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/konvader/OctoPrint-Powerinfo/archive/master.zip

## Configuration

 - Select input gpio pin for each relay
 - Define the refresh rate of the plugin
 - Define a custom label for each relay
 - Define custom labels for On/Off state
 - Show/hide used/unused relays

## Relay control

Add system actions to your ~/.octoprint/config.yaml to control the printer like the following example:

system:
  actions:
  \- action: printer on
    command: gpio -g write 17 0
    name: Turn on the printer
  \- action: printer off
    command: gpio -g write 17 1
    confirm: You are about to turn off the printer.
    name: Turn off the printer

Note: As we've initialized our GPIOs within the plugin, it is not necessary to do this anywhere else!
      The command has to be executed on the GPIO number here. Within the settings you have to use
      the pi's pin number. Check if your relay is active on high or low output of the GPIO and change the
      commands accordingly. The SainSmart is low active but this might differ on other relay boards.

/*
 * View model for OctoPrint-Powerinfo
 *
 * Author: Daniel Konrad
 * License: AGPLv3
 */
$(function() {
    function PowerinfoViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];

        self.rOneMessage = ko.observable();
        self.rOneShow = ko.observable(false);
        self.rTwoMessage = ko.observable();
        self.rTwoShow = ko.observable(false);

        self.initMessage = function(data) {
            self.rOneMessage(data.messageOne);
            self.rOneShow(data.messageOneShow);
            self.rTwoMessage(data.messageTwo);
            self.rTwoShow(data.messageTwoShow);
        };

        self.onStartupComplete = function() {
            // WebApp started, get status
            $.ajax({
                url: API_BASEURL + "plugin/powerinfo",
                type: "GET",
                dataType: "json",
                success: self.initMessage
            });
        }

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "powerinfo") {
                return;
            }

            self.rOneMessage(data.messageOne);
            self.rOneShow(data.messageOneShow);
            self.rTwoMessage(data.messageTwo);
            self.rTwoShow(data.messageTwoShow);
        };
    }

    ADDITIONAL_VIEWMODELS.push([
        PowerinfoViewModel,
        ["settingsViewModel"],
        ["#powerinfo"]
    ]);
});

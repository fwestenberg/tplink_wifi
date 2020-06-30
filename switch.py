"""This component provides basic support for TP-Link WiFi router."""
import logging
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.components.switch import SwitchDevice, PLATFORM_SCHEMA
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_USERNAME, CONF_PASSWORD, ATTR_ENTITY_ID, STATE_ON, STATE_OFF, STATE_UNKNOWN
import requests
# from requests.auth import HTTPBasicAuth
import json
from custom_components.tplink_wifi.PyPi.tplink import routerDevice

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "TP-Link Router"
DOMAIN = "tplink_wifi"
DEFAULT_USERNAME = "admin"
FREQ_2G = "2g"
FREQ_5G = "5g"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
    }
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up a TP-Link WiFi Router."""
    add_entities([TPLinkRouter(config, FREQ_2G), TPLinkRouter(config, FREQ_5G)], update_before_add=True)

class TPLinkRouter(SwitchDevice):
    """An implementation of a TP-Link WiFi Router."""

    def __init__(self, config, frequency):
        super().__init__()

        self._host = config.get(CONF_HOST)
        self._username = config.get(CONF_USERNAME)
        self._password = config.get(CONF_PASSWORD)
        self._name = f"{config.get(CONF_NAME)}_{frequency}"
        self._state = STATE_UNKNOWN
        self._frequency = frequency
        self._manager = routerDevice(self._host, self._username, self._password)

    @property
    def name(self):
        """Return the name of the switch if any."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        if self._state == STATE_ON:
            return True
        else:
            return False

    @property
    def icon(self):
        """Return the icon of device based on its type."""
        if self._state == STATE_ON:
            return "mdi:wifi"
        else: 
            return "mdi:wifi-off"

    @property
    def available(self):
        """Return true if switch is available."""
        if self._state == STATE_UNKNOWN:
            return False
        else:
            return True

    def turn_on(self, **kwargs):
        """Turn the WiFi on."""
        self._manager.set_wifi_state(self._frequency, STATE_ON)

    def turn_off(self, **kwargs):
        """Turn the WiFi off."""
        self._manager.set_wifi_state(self._frequency, STATE_OFF)

    def update(self):
        """Update the state"""
        self._manager.get_wifi_state(self._frequency, True)
        self._state = self._manager._state

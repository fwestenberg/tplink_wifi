"""This component provides basic support for TP-Link WiFi router."""
import logging
import voluptuous as vol
from homeassistant.const import STATE_ON, STATE_OFF, STATE_UNKNOWN
import requests
import json
import base64

FREQ_2G = "2g"
FREQ_5G = "5g"
NO_SUCCESS = "false"

_LOGGER = logging.getLogger(__name__)

class routerDevice():
    """An implementation of a TP-Link WiFi Router."""

    def __init__(self, host, username, password):
        super().__init__()

        self._host = host
        self._username = username
        self._password = password
        self._state = STATE_OFF
        self._json_data = None
        self._session = None
        self._cookies = None

    def login(self):
        # self._session = None

        auth = f"{self._username}:{self._password}"

        self._cookies = {'Authorization': 'Basic {token}'.format(
            token=base64.b64encode(auth.encode()).decode('ascii'))
        }

        self._headers = {
            "Origin": f"http://{self._host}/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": f"http://{self._host}/",
            "X-Requested-With": "XMLHttpRequest",
            "Connection": "keep-alive",
            "DNT": "1"
        }

        with requests.Session() as s:
            try:
                r = s.post(
                    "http://%s/data/login.json" % self._host, 
                    headers=self._headers, 
                    cookies=self._cookies, 
                    data=[("operation", "login")], 
                    auth=(self._username, self._password),
                    timeout=10
                )
            except requests.exceptions.RequestException: 
                _LOGGER.debug(f"Error while connecting with TP-Link IP {self._host}")
                self._state = STATE_UNKNOWN
                return False

            json_data = json.loads(r.text)
            success = json_data["success"]
            
            if success == NO_SUCCESS:
                _LOGGER.error(f"Login failed at TP-Link IP {self._host}")
                self._state = STATE_UNKNOWN
                return False
            else:    
                self._session = s
                return True

    def logout(self):
        if self._session is not None:
            self._session.close()
            self._session = None

    def get_wifi_state(self, frequency, keepAlive=False):
        if self._session is None:
            if not self.login():
                return self._state

        if frequency == FREQ_5G:
            url = f"http://{self._host}/admin/wireless?form=wireless_5g"
        else:
            url = f"http://{self._host}/admin/wireless?form=wireless_2g"

        try:
            r = self._session.post(
                url,
                headers=self._headers,
                cookies=self._cookies,
                data=[("operation", "read")],
                timeout=10
            )
        except requests.exceptions.RequestException: 
            _LOGGER.error(f"Error while connecting with TP-Link IP {self._host}")
            self.logout()
            self._state = STATE_UNKNOWN
            return self._state

        self._json_data = json.loads(r.text)
        success = self._json_data["success"]
        
        if success == NO_SUCCESS:
            _LOGGER.error(f"Failed to get the current state at TP-Link IP {self._host}")
            self.logout()
            self._state = STATE_UNKNOWN
            return self._state
        
        value = self._json_data["data"]["enable"] 
        _LOGGER.debug("Current state value: " + value)
        
        if value == STATE_ON:
            self._state = STATE_ON
        else:
            self._state = STATE_OFF
        
        if not keepAlive:
            self.logout()

        return self._state

    def set_wifi_state(self, frequency, setState):
        if self._session is None:
            if not self.login():
                return self._state

        if frequency == FREQ_5G:
            url = f"http://{self._host}/admin/wireless?form=wireless_5g"
        else:
            url = f"http://{self._host}/admin/wireless?form=wireless_2g"

        if self.get_wifi_state(frequency, True) == STATE_UNKNOWN:
            return

        payload = self._json_data["data"]
        payload["operation"] = "write"
        payload["enable"] = setState

        try:
            r = self._session.post(
                url,
                headers=self._headers,
                cookies=self._cookies,
                data=payload,
                timeout=10
                )
        except requests.exceptions.RequestException: 
            _LOGGER.error(f"Error while connecting with TP-Link IP {self._host}")
            self.logout()
            setState = STATE_UNKNOWN

        # self.logout()

        json_data = json.loads(r.text)        
        success = json_data["success"]
        
        if success == NO_SUCCESS:
            _LOGGER.error(f"Failed to change the WiFi state at TP-Link IP {self._host}")
        else:
            self._state = setState


# {
#    "success":true,
#    "timeout":true,
#    "data":{
#       "enable":"on",
#       "ssid":"TestWifi",
#       "hidden":"off",
#       "encryption":"psk",
#       "psk_version":"auto",
#       "psk_cipher":"aes",
#       "psk_key":"123test",
#       "wpa_version":"auto",
#       "wpa_cipher":"auto",
#       "server":"0.0.0.0",
#       "port":"1812",
#       "wpa_key":"",
#       "wep_mode":"open",
#       "wep_select":"1",
#       "wep_format1":"hex",
#       "wep_type1":"64",
#       "wep_key1":"",
#       "wep_format2":"hex",
#       "wep_type2":"64",
#       "wep_key2":"",
#       "wep_format3":"hex",
#       "wep_type3":"64",
#       "wep_key3":"",
#       "wep_format4":"hex",
#       "wep_type4":"64",
#       "wep_key4":"",
#       "hwmode":"ng",
#       "htmode":"auto",
#       "channel":"auto",
#       "disabled":"off",
#       "txpower":"high"
#    }
# }
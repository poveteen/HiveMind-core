import json
import logging
import sys
import time

import requests
from requests.exceptions import ConnectionError
# filter warnings, this should be removed once we stop using self signed
# certs for debug
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

platform = "JarbasHttpsCliTerminalv0.1"
logger = logging.getLogger(platform)
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel("INFO")


class JarbasMicroServicesAPI(object):
    def __init__(self, key, url="https://0.0.0.0:6712/", lang="en-us"):
        self.key = key
        self.headers = {"Authorization": key}
        self.lang = lang
        self.url = url
        self.timeout = 10
        self.wait_time = 0.5

    def hello_world(self):
        try:
            response = requests.get(
                self.url,
                headers=self.headers, verify=False
            )
            return response.text
        except ConnectionError as e:
            raise ConnectionError("Could not connect: " + str(e))

    def new_user(self, key, mail, name):
        ''' add a new user, requires admin api '''
        try:
            response = requests.put(
                self.url + "new_user/" + key + "/" + mail + "/" + name,
                headers=self.headers, verify=False
            )
            try:
                return response.json()
            except:
                logger.error(response.text)
                raise ValueError("Invalid admin api key")
        except ConnectionError as e:
            raise ConnectionError("Could not connect: " + str(e))

    def revoke_key(self, key):
        ''' add a new user, requires admin api '''
        try:
            response = requests.put(
                self.url + "revoke_key/" + key,
                headers=self.headers, verify=False
            )
            try:
                return response.json()
            except:
                logger.error(response.text)
                raise ValueError("Invalid admin api key")
        except ConnectionError as e:
            raise ConnectionError("Could not connect: " + str(e))

    def generate_key(self):
        ''' get an api key string, requires admin api '''
        try:
            response = requests.get(
                self.url + "generate_key",
                headers=self.headers, verify=False
            )
            try:
                return response.json()["key"]
            except:
                logger.info(response.text)
                raise ValueError("Invalid admin api key")
        except ConnectionError as e:
            raise ConnectionError("Could not connect: " + str(e))

    def ask_mycroft(self, utterance, lang=None):
        ''' ask something to mycroft '''
        lang = lang or self.lang
        try:
            response = requests.put(
                self.url + "ask/" + lang + "/" + utterance,
                headers=self.headers, verify=False
            )
            try:
                ans = response.json()
                if ans["status"] == "processing":
                    # start waiting
                    start = time.time()
                    while ans["status"] == "processing":
                        time.sleep(self.wait_time)
                        if time.time() - start > self.timeout:
                            try:
                                response = requests.put(
                                    self.url + "cancel",
                                    headers=self.headers, verify=False
                                )
                            except Exception as e:
                                logger.error(e)

                            return {"type": "speak",
                                    "data": {"utterance": "server timed out"},
                                    "context": {"source": "hivemind_flask",
                                                "destination": self.key}}
                        try:
                            response = requests.get(
                                self.url + "get_answer",
                                headers=self.headers, verify=False
                            )
                            ans = response.json()
                        except Exception as e:
                            raise ValueError("Unexpected Error: " + str(e))
                    return json.loads(ans["answer"])
                else:
                    raise ValueError("Received unexpected status from "
                                     "server: " + str(ans))
            except:
                logger.error(response.text)
                raise ValueError("Invalid api key: " + str(self.key))
        except ConnectionError as e:
            raise ConnectionError("Could not connect: " + str(e))


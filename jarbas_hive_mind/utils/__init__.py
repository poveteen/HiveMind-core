import json
import random
from os import makedirs
from os.path import exists, join
from socket import gethostname

from OpenSSL import crypto


def merge_dict(base, delta):
    """
        Recursively merging configuration dictionaries.

        Args:
            base:  Target for merge
            delta: Dictionary to merge into base
    """

    for k, dv in delta.items():
        bv = base.get(k)
        if isinstance(dv, dict) and isinstance(bv, dict):
            merge_dict(bv, dv)
        else:
            base[k] = dv


def load_commented_json(filename):
    """ Loads an JSON file, ignoring comments

    Supports a trivial extension to the JSON file format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.

    NOTE: A file created with these style comments will break strict JSON
          parsers.  This is similar to but lighter-weight than "human json"
          proposed at https://hjson.org

    Args:
        filename (str):  path to the commented JSON file

    Returns:
        obj: decoded Python object
    """
    with open(filename) as f:
        contents = f.read()

    return json.loads(uncomment_json(contents))


def uncomment_json(commented_json_str):
    """ Removes comments from a JSON string.

    Supporting a trivial extension to the JSON format.  Allow comments
    to be embedded within the JSON, requiring that a comment be on an
    independent line starting with '//' or '#'.

    Example...
       {
         // comment
         'name' : 'value'
       }

    Args:
        commented_json_str (str):  a JSON string

    Returns:
        str: uncommented, legal JSON
    """
    lines = commented_json_str.splitlines()
    # remove all comment lines, starting with // or #
    nocomment = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("//") or stripped.startswith("#"):
            continue
        nocomment.append(line)

    return " ".join(nocomment)


def create_echo_function(name, whitelist=None):
    def echo(message):
        """Listen for messages and echo them for logging"""
        from jarbas_hive_mind.utils.log import LOG
        from jarbas_hive_mind.utils.configuration import Configuration
        blacklist = Configuration.get().get("ignore_logs")
        try:
            js_msg = json.loads(message)

            if whitelist and js_msg.get("type") not in whitelist:
                return

            if blacklist and js_msg.get("type") in blacklist:
                return

            if js_msg.get("type") == "registration":
                # do not log tokens from registration messages
                js_msg["data"]["token"] = None
                message = json.dumps(js_msg)
        except Exception:
            pass
        LOG(name).debug(message)

    return echo


def create_self_signed_cert(cert_dir, name="jarbas_hivemind"):
    """
    If name.crt and name.key don't exist in cert_dir, create a new
    self-signed cert and key pair and write them into that directory.
    """

    CERT_FILE = name + ".crt"
    KEY_FILE = name + ".key"
    cert_path = join(cert_dir, CERT_FILE)
    key_path = join(cert_dir, KEY_FILE)

    if not exists(join(cert_dir, CERT_FILE)) \
            or not exists(join(cert_dir, KEY_FILE)):
        # create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 1024)

        # create a self-signed cert
        cert = crypto.X509()
        cert.get_subject().C = "PT"
        cert.get_subject().ST = "Europe"
        cert.get_subject().L = "Mountains"
        cert.get_subject().O = "Jarbas AI"
        cert.get_subject().OU = "Powered by Mycroft-Core"
        cert.get_subject().CN = gethostname()
        cert.set_serial_number(random.randint(0, 2000))
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha1')
        if not exists(cert_dir):
            makedirs(cert_dir)
        open(cert_path, "wt").write(
            crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
        open(join(cert_dir, KEY_FILE), "wt").write(
            crypto.dump_privatekey(crypto.FILETYPE_PEM, k))

    return cert_path, key_path


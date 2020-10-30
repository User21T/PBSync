import os
import sys
import configparser
from xml.etree.ElementTree import parse
from functools import lru_cache

from pbpy import pbtools

# Singleton Config
config = None

user_config = None

def get(key):
    if key is None or config is None or config.get(str(key)) is None:
        pbtools.error_state(f"Invalid config get request: {key}", hush=True)

    return config.get(str(key))


@lru_cache()
def get_user_config_filename():
    config_key = 'ue4v_ci_config' if get("is_ci") else 'ue4v_user_config'
    return get(config_key)


def init_user_config():
    global user_config
    user_config = configparser.ConfigParser()
    user_config.read(get_user_config_filename())
    if not user_config.has_section("ue4v-user"):
        user_config["ue4v-user"] = {}


def get_user_config():
    if user_config is None:
        init_user_config()
    return user_config

def get_user(section, key, default=None):
    return get_user_config().get(section, key, fallback=default)


def shutdown():
    with open(get_user_config_filename(), 'w') as user_config_file:
        get_user_config().write(user_config_file)


def generate_config(config_path, parser_func):
    # Generalized config generator. parser_func is responsible with returning a valid config object
    global config

    if config_path is not None and os.path.isfile(config_path):
        tree = parse(config_path)
        if tree is None:
            return False
        root = tree.getroot()
        if root is None:
            return False

        # Read config xml
        try:
            config = parser_func(root)
        except Exception as e:
            print(f"Config exception: {e}")
            return False

        # Add CI information
        is_ci = os.environ.get('PBSYNC_CI', None) is not None

        config["is_ci"] = is_ci

        return True

    return False

import psycopg2
import os
import couchbeans
import json


config_file_loc = os.environ.get("GRIPPY_CONFIG_FILE", "config.json")
sys_config = {}
with open(config_file_loc, "r") as f:
    sys_config = json.load(f)

def try_get_config_prop(property_name, alternate=None):
    if property_name in sys_config:
        return sys_config[property_name]
    return alternate

couch_user = os.environ.get("COUCHDB_USER", try_get_config_prop("couchdb_user"))
couch_password = os.environ.get("COUCHDB_PASSWORD", try_get_config_prop("couchdb_password"))
couch_host = os.environ.get("COUCHDB_HOST", try_get_config_prop("couchdb_host", "localhost"))
couch_port = os.environ.get("COUCHDB_PORT", try_get_config_prop("couchdb_port", 5984))
couch_base_uri = "http://" + couch_user + ":" + couch_password + "@" + couch_host + ":" + str(couch_port) + "/"

conn_string = 'host=' + os.environ.get("POSTGRES_HOST") + ' dbname=' + os.environ.get("POSTGRES_DB") + ' user=' + os.environ.get("POSTGRES_USER") + ' password=' + os.environ.get("POSTGRES_PASSWORD") + ''

def get_couch_client():
    return couchbeans.CouchClient(couch_base_uri)

def get_couch_base_uri():
    return couch_base_uri

def get_postgres():
    return psycopg2.connect(conn_string)


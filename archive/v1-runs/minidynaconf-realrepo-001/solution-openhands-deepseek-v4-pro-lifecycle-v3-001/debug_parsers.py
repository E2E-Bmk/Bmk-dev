import json, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from minidynaconf import parse_toml, parse_ini, parse_yaml, parse_json

# Test TOML
toml = '''
title = "My App"
[server]
host = "0.0.0.0"
port = 8080
debug = true
[server.tls]
enabled = true
'''
print("TOML result:", json.dumps(parse_toml(toml), indent=2))

# Test INI
ini = '''
[server]
host = 127.0.0.1
port = 9090
[database]
name = testdb
'''
print("\nINI result:", json.dumps(parse_ini(ini), indent=2))

# Test YAML
yaml = '''
server:
  host: yamlhost
  port: 7070
features:
  - auth
  - logging
data:
  nested:
    key: value
'''
print("\nYAML result:", json.dumps(parse_yaml(yaml), indent=2))

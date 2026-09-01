module spec2repo.local/go25v18/oracle

go 1.23.0

require (
	github.com/fsnotify/fsnotify v1.9.0
	github.com/go-viper/mapstructure/v2 v2.4.0
	github.com/knadh/koanf/maps v0.1.2
	github.com/knadh/koanf/parsers/json v0.0.0
	github.com/knadh/koanf/parsers/yaml v0.0.0
	github.com/knadh/koanf/providers/confmap v0.0.0
	github.com/knadh/koanf/providers/file v0.0.0
	github.com/knadh/koanf/providers/rawbytes v0.0.0
	github.com/knadh/koanf/v2 v2.3.6
	github.com/mitchellh/copystructure v1.2.0
	github.com/mitchellh/reflectwalk v1.0.2
	go.yaml.in/yaml/v3 v3.0.3
)

replace github.com/knadh/koanf/v2 => ../../controls/upstream

replace github.com/knadh/koanf/maps => ../../controls/upstream/maps

replace github.com/knadh/koanf/parsers/json => ../../controls/upstream/parsers/json

replace github.com/knadh/koanf/parsers/yaml => ../../controls/upstream/parsers/yaml

replace github.com/knadh/koanf/providers/confmap => ../../controls/upstream/providers/confmap

replace github.com/knadh/koanf/providers/file => ../../controls/upstream/providers/file

replace github.com/knadh/koanf/providers/rawbytes => ../../controls/upstream/providers/rawbytes

replace github.com/go-viper/mapstructure/v2 => ../../reference/third_party/mapstructure

replace github.com/mitchellh/copystructure => ../../reference/third_party/copystructure

replace github.com/mitchellh/reflectwalk => ../../reference/third_party/reflectwalk

replace github.com/fsnotify/fsnotify => ../../reference/third_party/fsnotify

replace go.yaml.in/yaml/v3 => ../../reference/third_party/yaml

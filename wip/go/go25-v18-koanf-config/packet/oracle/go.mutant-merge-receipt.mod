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

replace github.com/knadh/koanf/v2 => ../../controls/mutants/merge-receipt

replace github.com/knadh/koanf/maps => ../../controls/mutants/merge-receipt/maps

replace github.com/knadh/koanf/parsers/json => ../../controls/mutants/merge-receipt/parsers/json

replace github.com/knadh/koanf/parsers/yaml => ../../controls/mutants/merge-receipt/parsers/yaml

replace github.com/knadh/koanf/providers/confmap => ../../controls/mutants/merge-receipt/providers/confmap

replace github.com/knadh/koanf/providers/file => ../../controls/mutants/merge-receipt/providers/file

replace github.com/knadh/koanf/providers/rawbytes => ../../controls/mutants/merge-receipt/providers/rawbytes

replace github.com/go-viper/mapstructure/v2 => ../../controls/mutants/merge-receipt/third_party/mapstructure

replace github.com/mitchellh/copystructure => ../../controls/mutants/merge-receipt/third_party/copystructure

replace github.com/mitchellh/reflectwalk => ../../controls/mutants/merge-receipt/third_party/reflectwalk

replace github.com/fsnotify/fsnotify => ../../controls/mutants/merge-receipt/third_party/fsnotify

replace go.yaml.in/yaml/v3 => ../../controls/mutants/merge-receipt/third_party/yaml

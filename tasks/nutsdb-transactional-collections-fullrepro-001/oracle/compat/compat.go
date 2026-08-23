package compat

import (
	"errors"
	"fmt"
	"reflect"

	nutsdb "github.com/nutsdb/nutsdb"
)

var errorType = reflect.TypeOf((*error)(nil)).Elem()

func call(target any, name string, args ...any) (out []reflect.Value, err error) {
	m := reflect.ValueOf(target).MethodByName(name)
	if !m.IsValid() {
		return nil, fmt.Errorf("missing public method %s", name)
	}
	defer func() {
		if recovered := recover(); recovered != nil {
			out = nil
			err = fmt.Errorf("call %s: %v", name, recovered)
		}
	}()
	in := make([]reflect.Value, len(args))
	for i, arg := range args {
		v := reflect.ValueOf(arg)
		var want reflect.Type
		if m.Type().IsVariadic() && i >= m.Type().NumIn()-1 {
			want = m.Type().In(m.Type().NumIn() - 1).Elem()
		} else {
			want = m.Type().In(i)
		}
		if v.Type() != want && v.Type().ConvertibleTo(want) {
			v = v.Convert(want)
		}
		in[i] = v
	}
	return m.Call(in), nil
}

func resultError(out []reflect.Value) error {
	if len(out) == 0 {
		return nil
	}
	last := out[len(out)-1]
	if last.Type().Implements(errorType) && !last.IsNil() {
		return last.Interface().(error)
	}
	return nil
}

func bytesResult(v reflect.Value) ([]byte, error) {
	if b, ok := v.Interface().([]byte); ok {
		return append([]byte(nil), b...), nil
	}
	for v.Kind() == reflect.Interface || v.Kind() == reflect.Pointer {
		if v.IsNil() {
			return nil, errors.New("nil value")
		}
		v = v.Elem()
	}
	if v.Kind() == reflect.Struct {
		field := v.FieldByName("Value")
		if field.IsValid() {
			if b, ok := field.Interface().([]byte); ok {
				return append([]byte(nil), b...), nil
			}
		}
	}
	return nil, fmt.Errorf("unsupported value result %s", v.Type())
}

func Get(tx *nutsdb.Tx, bucket string, key []byte) ([]byte, error) {
	out, err := call(tx, "Get", bucket, key)
	if err != nil {
		return nil, err
	}
	if err := resultError(out); err != nil {
		return nil, err
	}
	if len(out) < 1 {
		return nil, errors.New("Get returned no value")
	}
	return bytesResult(out[0])
}

func MSet(tx *nutsdb.Tx, bucket string, ttl uint32, pairs ...[]byte) error {
	m := reflect.ValueOf(tx).MethodByName("MSet")
	if !m.IsValid() {
		return errors.New("missing public method MSet")
	}
	args := []any{bucket}
	if m.Type().NumIn() == 3 {
		args = append(args, ttl)
	}
	for _, pair := range pairs {
		args = append(args, pair)
	}
	out, err := call(tx, "MSet", args...)
	if err != nil {
		return err
	}
	return resultError(out)
}

func MGet(tx *nutsdb.Tx, bucket string, keys ...[]byte) ([][]byte, error) {
	args := []any{bucket}
	for _, key := range keys {
		args = append(args, key)
	}
	out, err := call(tx, "MGet", args...)
	if err != nil {
		return nil, err
	}
	if err := resultError(out); err != nil {
		return nil, err
	}
	if len(out) < 1 || out[0].Kind() != reflect.Slice {
		return nil, errors.New("MGet returned incompatible values")
	}
	values := make([][]byte, out[0].Len())
	for i := 0; i < out[0].Len(); i++ {
		value, err := bytesResult(out[0].Index(i))
		if err != nil {
			return nil, err
		}
		values[i] = value
	}
	return values, nil
}

func GetSet(tx *nutsdb.Tx, bucket string, key, value []byte, ttl uint32) ([]byte, error) {
	m := reflect.ValueOf(tx).MethodByName("GetSet")
	if !m.IsValid() {
		return nil, errors.New("missing public method GetSet")
	}
	args := []any{bucket, key, value}
	if m.Type().NumIn() == 4 {
		args = append(args, ttl)
	}
	out, err := call(tx, "GetSet", args...)
	if err != nil {
		return nil, err
	}
	if err := resultError(out); err != nil {
		return nil, err
	}
	if len(out) < 1 {
		return nil, errors.New("GetSet returned no value")
	}
	return bytesResult(out[0])
}

func GetAll(tx *nutsdb.Tx, bucket string) ([][]byte, [][]byte, error) {
	out, err := call(tx, "GetAll", bucket)
	if err != nil {
		return nil, nil, err
	}
	if err := resultError(out); err != nil {
		return nil, nil, err
	}
	if len(out) == 3 {
		keys, okKeys := out[0].Interface().([][]byte)
		values, okValues := out[1].Interface().([][]byte)
		if !okKeys || !okValues {
			return nil, nil, errors.New("GetAll returned incompatible projections")
		}
		return keys, values, nil
	}
	if len(out) == 2 {
		values, ok := out[0].Interface().([][]byte)
		if !ok {
			return nil, nil, errors.New("GetAll returned incompatible values")
		}
		keyOut, keyErr := call(tx, "GetKeys", bucket)
		if keyErr != nil {
			return nil, nil, keyErr
		}
		if err := resultError(keyOut); err != nil {
			return nil, nil, err
		}
		keys, ok := keyOut[0].Interface().([][]byte)
		if !ok {
			return nil, nil, errors.New("GetKeys returned incompatible keys")
		}
		return keys, values, nil
	}
	return nil, nil, fmt.Errorf("GetAll returned %d results", len(out))
}

func IteratorValue(iterator any) ([]byte, error) {
	out, err := call(iterator, "Value")
	if err != nil {
		return nil, err
	}
	if err := resultError(out); err != nil {
		return nil, err
	}
	if len(out) < 1 {
		return nil, errors.New("Value returned no bytes")
	}
	return bytesResult(out[0])
}

func IteratorMove(iterator any, method string, args ...any) (bool, error) {
	out, err := call(iterator, method, args...)
	if err != nil {
		return false, err
	}
	if err := resultError(out); err != nil {
		return false, err
	}
	if len(out) > 0 && out[0].Kind() == reflect.Bool {
		return out[0].Bool(), nil
	}
	valid, err := call(iterator, "Valid")
	if err != nil || len(valid) != 1 || valid[0].Kind() != reflect.Bool {
		return false, errors.New("iterator Valid returned incompatible result")
	}
	return valid[0].Bool(), nil
}

func IterateBuckets(tx *nutsdb.Tx, ds nutsdb.DataStructure, pattern string, callback func(string) bool) error {
	m := reflect.ValueOf(tx).MethodByName("IterateBuckets")
	if !m.IsValid() {
		return errors.New("missing public method IterateBuckets")
	}
	args := []any{pattern, callback}
	if m.Type().NumIn() == 3 {
		args = []any{ds, pattern, callback}
	}
	out, err := call(tx, "IterateBuckets", args...)
	if err != nil {
		return err
	}
	return resultError(out)
}

func LRem(tx *nutsdb.Tx, bucket string, key []byte, count int, value []byte) error {
	out, err := call(tx, "LRem", bucket, key, count, value)
	if err != nil {
		return err
	}
	return resultError(out)
}

func Watch(db *nutsdb.DB, bucket string, key []byte, callback func(*nutsdb.Message) error, options ...nutsdb.WatchOptions) error {
	m := reflect.ValueOf(db).MethodByName("Watch")
	if !m.IsValid() {
		return errors.New("missing public method Watch")
	}
	args := []any{bucket, key, callback}
	if len(options) > 0 {
		if !m.Type().IsVariadic() && m.Type().NumIn() == 3 {
			return errors.New("Watch does not accept callback timeout options")
		}
		args = append(args, options[0])
	}
	out, err := call(db, "Watch", args...)
	if err != nil {
		return err
	}
	return resultError(out)
}

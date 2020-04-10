// Copyright 2019 The Fuchsia Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

package runtests

import (
	"path"
	"reflect"
	"testing"
)

type fakeViewer struct {
	s           TestSummary
	copiedFiles map[string]string
}

func (v fakeViewer) summary(_ string) (*TestSummary, error) {
	return &v.s, nil
}

func (v fakeViewer) copyFile(remote, local string) error {
	v.copiedFiles[remote] = local
	return nil
}

func (v fakeViewer) close() error {
	return nil
}

func TestCopyDataSinks(t *testing.T) {
	expectedSinks := DataSinkMap{
		"sink": {
			{
				Name: "sink1",
				File: "a/b/c/sink1",
			},
			{
				Name: "sink2",
				File: "a/d/e/sink2",
			},
		},
	}
	summary := TestSummary{
		Tests: []TestDetails{
			{
				Name:      "foo_test",
				DataSinks: expectedSinks,
			},
		},
	}

	viewer := fakeViewer{s: summary, copiedFiles: map[string]string{}}
	copier := DataSinkCopier{viewer: viewer, remoteDir: "REMOTE_DIR"}
	dataSinks, err := copier.GetReference()
	if err != nil {
		t.Fatalf("failed to get data sinks: %s", err)
	} else if !reflect.DeepEqual(DataSinkMap(dataSinks), expectedSinks) {
		t.Errorf("got data sinks %v, expected %v", dataSinks, expectedSinks)
	}
	_, err = copier.Copy([]DataSinkReference{dataSinks}, "LOCAL_DIR")
	if err != nil {
		t.Fatalf("failed to copy data sinks: %s", err)
	}

	for _, sink := range dataSinks["sink"] {
		src := path.Join("REMOTE_DIR", sink.File)
		expectedDest := path.Join("LOCAL_DIR", sink.File)
		actualDest, ok := viewer.copiedFiles[src]
		if !ok {
			t.Errorf("sink %q was not copied", sink.File)
		}
		if expectedDest != actualDest {
			t.Errorf("sink %q was copied to the wrong destination:\nexpected: %s\nactual %s",
				sink.File, expectedDest, actualDest)
		}
	}
}

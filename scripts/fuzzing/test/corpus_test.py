#!/usr/bin/env python
# Copyright 2019 The Fuchsia Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import unittest

import test_env
from test_case import TestCaseWithFuzzer


class CorpusTest(TestCaseWithFuzzer):

    def test_find_on_device(self):
        data = self.ns.data('corpus')
        resource = self.ns.resource('//src/fake/package1/target2-corpus')

        self.corpus.find_on_device()
        self.assertEqual(self.corpus.nspaths, [data])

        self.create_fuzzer('fake-package1/fake-target2')
        self.corpus.find_on_device()
        self.assertEqual(self.corpus.nspaths, [data, resource])

    def test_add_from_host(self):
        # Invalid directory
        local_path = 'corpus_dir'
        self.assertError(
            lambda: self.corpus.add_from_host(local_path),
            'No such directory: {}'.format(local_path))
        self.host.mkdir(local_path)

        # Fuzzer is running
        corpus_element = os.path.join(local_path, 'element')
        self.host.touch(corpus_element)
        self.set_running(self.fuzzer.executable_url, duration=10)
        self.assertError(
            lambda: self.corpus.add_from_host(local_path),
            'fake-package1/fake-target1 is running and must be stopped first.')
        self.host.sleep(10)

        # Valid
        added = self.corpus.add_from_host(local_path)
        self.assertEqual(len(added), 1)
        self.assertScpTo(
            corpus_element, self.ns.data_abspath(self.corpus.nspaths[0]))

    def test_reset(self):
        self.corpus.reset()
        self.assertSsh('rm', '-rf', self.ns.data_abspath('corpus'))

    def test_add_from_gcs(self):
        # Note: this takes advantage of the fact that the FakeCLI always returns
        # the same name for temp_dir().
        with self.host.temp_dir() as temp_dir:
            gcs_url = 'gs://bucket'
            cmd = ['gsutil', '-m', 'cp', gcs_url + '/*', temp_dir.pathname]
            process = self.get_process(cmd)
            process.succeeds = False
            self.assertError(
                lambda: self.corpus.add_from_gcs(gcs_url),
                'Failed to download corpus from GCS.',
                'You can skip downloading from GCS with the "--local" flag.')

            process.succeeds = True
            corpus_element = os.path.join(temp_dir.pathname, 'element')
            self.host.touch(corpus_element)
            added = self.corpus.add_from_gcs(gcs_url)
            self.assertEqual(len(added), 1)
            self.assertRan(*cmd)
            self.assertScpTo(
                corpus_element, self.ns.data_abspath(self.corpus.nspaths[0]))

    def test_measure(self):
        self.touch_on_device(self.ns.data_abspath('corpus/deadbeef'), size=1000)
        self.touch_on_device(self.ns.data_abspath('corpus/feedface'), size=729)
        sizes = self.corpus.measure()
        self.assertEqual(sizes, (2, 1 + 1728))

    def test_generate_buildfile_zero_corpus_elements(self):
        # Fuzzer with empty corpus
        fuzzer = self.create_fuzzer('fake-package1/fake-target2')
        srcdir = self.buildenv.abspath(fuzzer.corpus.srcdir)
        self.host.mkdir(srcdir)

        build_gn = self.buildenv.abspath(srcdir, 'BUILD.gn')
        self.assertFalse(self.host.isfile(build_gn))
        self.assertEqual(fuzzer.corpus.generate_buildfile(), [])
        self.assertTrue(self.host.isfile(build_gn))

        pkgdir = self.buildenv.srcpath(fuzzer.corpus.srcdir)[2:]
        with self.host.open(build_gn) as f:
            self.assertEqual(
                f.read().split('\n'), [
                    '# Copyright 2020 The Fuchsia Authors. All rights reserved.',
                    '# Use of this source code is governed by a BSD-style license that can be',
                    '# found in the LICENSE file.',
                    '',
                    '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
                    '',
                    'import("//build/dist/resource.gni")',
                    '',
                    '# Generated using `fx fuzz update fake-package1/fake-target2`.',
                    'resource("corpus") {',
                    '  sources = []',
                    '  outputs = [ "data/{}/{{{{source_file_part}}}}" ]'.format(
                        pkgdir),
                    '}',
                    '',
                ])

    def test_generate_buildfile_one_corpus_element(self):
        # Fuzzer with empty corpus
        fuzzer = self.create_fuzzer('fake-package1/fake-target2')
        srcdir = self.buildenv.abspath(fuzzer.corpus.srcdir)
        self.host.mkdir(srcdir)
        self.host.touch(self.buildenv.abspath(srcdir, 'foo'))
        self.assertEqual(fuzzer.corpus.generate_buildfile(), ['foo'])

        build_gn = self.buildenv.abspath(srcdir, 'BUILD.gn')
        pkgdir = self.buildenv.srcpath(fuzzer.corpus.srcdir)[2:]
        self.assertTrue(self.host.isfile(build_gn))
        with self.host.open(build_gn) as f:
            self.assertEqual(
                f.read().split('\n'), [
                    '# Copyright 2020 The Fuchsia Authors. All rights reserved.',
                    '# Use of this source code is governed by a BSD-style license that can be',
                    '# found in the LICENSE file.',
                    '',
                    '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
                    '',
                    'import("//build/dist/resource.gni")',
                    '',
                    '# Generated using `fx fuzz update fake-package1/fake-target2`.',
                    'resource("corpus") {',
                    '  sources = [ "foo" ]',
                    '  outputs = [ "data/{}/{{{{source_file_part}}}}" ]'.format(
                        pkgdir),
                    '}',
                    '',
                ])

    def test_generate_buildfile_two_or_more_corpus_elements(self):
        # Add elements to corpus and update
        fuzzer = self.create_fuzzer('fake-package1/fake-target2')
        srcdir = self.buildenv.abspath(fuzzer.corpus.srcdir)
        self.host.mkdir(srcdir)
        self.host.touch(self.buildenv.abspath(srcdir, 'foo'))
        self.host.touch(self.buildenv.abspath(srcdir, 'bar'))
        self.assertEqual(fuzzer.corpus.generate_buildfile(), ['bar', 'foo'])

        build_gn = self.buildenv.abspath(srcdir, 'BUILD.gn')
        pkgdir = self.buildenv.srcpath(fuzzer.corpus.srcdir)[2:]
        self.assertTrue(self.host.isfile(build_gn))
        with self.host.open(build_gn) as f:
            self.assertEqual(
                f.read().split('\n'), [
                    '# Copyright 2020 The Fuchsia Authors. All rights reserved.',
                    '# Use of this source code is governed by a BSD-style license that can be',
                    '# found in the LICENSE file.',
                    '',
                    '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
                    '',
                    'import("//build/dist/resource.gni")',
                    '',
                    '# Generated using `fx fuzz update fake-package1/fake-target2`.',
                    'resource("corpus") {',
                    '  sources = [',
                    '    "bar",',
                    '    "foo",',
                    '  ]',
                    '  outputs = [ "data/{}/{{{{source_file_part}}}}" ]'.format(
                        pkgdir),
                    '}',
                    '',
                ])

    def test_generate_buildfile_update_corpus(self):
        # Add elements to corpus and update
        fuzzer = self.create_fuzzer('fake-package1/fake-target2')
        srcdir = self.buildenv.abspath(fuzzer.corpus.srcdir)

        # Start with an existing GN file (with an older copyright).
        lines_out = [
            '# Copyright 2019 The Fuchsia Authors. All rights reserved.',
            '# Use of this source code is governed by a BSD-style license that can be',
            '# found in the LICENSE file.',
            '',
            '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
            '',
            'import("//build/dist/resource.gni")',
            '',
            '# Not a matching comment',
            'resource("corpus") {',
            '  sources = []',
            '  outputs = [ "data/corpus/{{source_file_part}}" ]',
            '}',
            '',
        ]
        build_gn = self.buildenv.abspath(srcdir, 'BUILD.gn')
        with self.host.open(build_gn, 'w') as f:
            f.write('\n'.join(lines_out))

        self.host.mkdir(srcdir)
        self.host.touch(self.buildenv.abspath(srcdir, 'foo'))
        self.host.touch(self.buildenv.abspath(srcdir, 'bar'))
        self.host.touch(self.buildenv.abspath(srcdir, 'baz'))
        self.assertEqual(
            fuzzer.corpus.generate_buildfile(), ['bar', 'baz', 'foo'])
        pkgdir = self.buildenv.srcpath(fuzzer.corpus.srcdir)[2:]
        self.assertTrue(self.host.isfile(build_gn))
        with self.host.open(build_gn) as f:
            self.assertEqual(
                f.read().split('\n'), [
                    '# Copyright 2019 The Fuchsia Authors. All rights reserved.',
                    '# Use of this source code is governed by a BSD-style license that can be',
                    '# found in the LICENSE file.',
                    '',
                    '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
                    '',
                    'import("//build/dist/resource.gni")',
                    '',
                    '# Generated using `fx fuzz update fake-package1/fake-target2`.',
                    'resource("corpus") {',
                    '  sources = [',
                    '    "bar",',
                    '    "baz",',
                    '    "foo",',
                    '  ]',
                    '  outputs = [ "data/{}/{{{{source_file_part}}}}" ]'.format(
                        pkgdir),
                    '}',
                    '',
                ])

    def test_generate_buildfile_with_build_gn(self):
        # Use a GN file in a different location.
        fuzzer = self.create_fuzzer('fake-package1/fake-target2')
        srcdir = self.buildenv.abspath(fuzzer.corpus.srcdir)
        pkgdir = self.buildenv.srcpath(fuzzer.corpus.srcdir)[2:]
        self.host.mkdir(srcdir)
        self.host.touch(self.buildenv.abspath(srcdir, 'foo'))
        self.host.touch(self.buildenv.abspath(srcdir, 'bar'))

        build_gn = self.buildenv.abspath('src', 'fake', 'new.gn')
        relpath = os.path.relpath(srcdir, os.path.dirname(build_gn))
        self.assertEqual(
            fuzzer.corpus.generate_buildfile(build_gn=build_gn), [
                '{}/bar'.format(relpath),
                '{}/foo'.format(relpath),
            ])
        self.assertTrue(self.host.isfile(build_gn))
        with self.host.open(build_gn) as f:
            self.assertEqual(
                f.read().split('\n'), [
                    '# Copyright 2020 The Fuchsia Authors. All rights reserved.',
                    '# Use of this source code is governed by a BSD-style license that can be',
                    '# found in the LICENSE file.',
                    '',
                    '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
                    '',
                    'import("//build/dist/resource.gni")',
                    '',
                    '# Generated using `fx fuzz update {} -o {}`.'.format(
                        str(fuzzer), self.buildenv.srcpath(build_gn)),
                    'resource("corpus") {',
                    '  sources = [',
                    '    "{}/bar",'.format(relpath),
                    '    "{}/foo",'.format(relpath),
                    '  ]',
                    '  outputs = [ "data/{}/{{{{source_file_part}}}}" ]'.format(
                        pkgdir),
                    '}',
                    '',
                ])

    def test_generate_buildfile_append_to_existing(self):
        # Add elements to corpus and update
        fuzzer = self.create_fuzzer('fake-package1/fake-target2')
        srcdir = self.buildenv.abspath(fuzzer.corpus.srcdir)

        # Start with an existing GN file (with an older copyright).
        lines_out = [
            '# Copyright 2019 The Fuchsia Authors. All rights reserved.',
            '# Use of this source code is governed by a BSD-style license that can be',
            '# found in the LICENSE file.',
            '',
            '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
            '',
            'import("//build/dist/resource.gni")',
            '',
            '# A distinct corpus',
            'resource("corpus") {',
            '  sources = [ "untouched" ]',
            '  outputs = [ "data/corpus/{{source_file_part}}" ]',
            '}',
            '',
        ]

        build_gn = self.buildenv.abspath(srcdir, 'BUILD.gn')
        with self.host.open(build_gn, 'w') as f:
            f.write('\n'.join(lines_out))

        # Use the same BUILD.gn for another fuzzer.
        fuzzer = self.create_fuzzer('fake-package1/fake-target3')
        srcdir = self.buildenv.abspath(fuzzer.corpus.srcdir)
        relpath = os.path.relpath(srcdir, os.path.dirname(build_gn))
        pkgdir = self.buildenv.srcpath(fuzzer.corpus.srcdir)[2:]
        self.host.mkdir(srcdir)
        self.host.touch(self.buildenv.abspath(srcdir, 'baz'))
        self.assertEqual(
            fuzzer.corpus.generate_buildfile(build_gn=build_gn),
            ['{}/baz'.format(relpath)])

        self.assertTrue(self.host.isfile(build_gn))
        with self.host.open(build_gn) as f:
            self.assertEqual(
                f.read().split('\n'), [
                    '# Copyright 2019 The Fuchsia Authors. All rights reserved.',
                    '# Use of this source code is governed by a BSD-style license that can be',
                    '# found in the LICENSE file.',
                    '',
                    '# WARNING: AUTOGENERATED FILE. DO NOT EDIT BY HAND.',
                    '',
                    'import("//build/dist/resource.gni")',
                    '',
                    '# A distinct corpus',
                    'resource("corpus") {',
                    '  sources = [ "untouched" ]',
                    '  outputs = [ "data/corpus/{{source_file_part}}" ]',
                    '}',
                    '',
                    '# Generated using `fx fuzz update {} -o {}`.'.format(
                        str(fuzzer), self.buildenv.srcpath(build_gn)),
                    'resource("target3-corpus") {',
                    '  sources = [ "{}/baz" ]'.format(relpath),
                    '  outputs = [ "data/{}/{{{{source_file_part}}}}" ]'.format(
                        pkgdir),
                    '}',
                    '',
                ])

    def test_generate_buildfile_bad_directory(self):
        # Fuzzer without corpus directory specified in its metadata, and bad directory
        fuzzer = self.create_fuzzer('fake-package1/fake-target1')
        srcdir = 'no-such-dir'
        self.set_input(srcdir)
        self.assertError(
            lambda: fuzzer.corpus.generate_buildfile(),
            'No such directory: {}'.format(self.buildenv.abspath(srcdir)))

    def test_generate_buildfile_needs_manual_update(self):
        # No corresponding fuzzer BUILD.gn
        fuzzer = self.create_fuzzer('fake-package1/fake-target1')
        srcdir = 'shared-corpus'
        self.host.mkdir(self.buildenv.abspath(srcdir))
        self.set_input(srcdir)
        self.assertError(
            lambda: fuzzer.corpus.generate_buildfile(),
            'Failed to automatically add \'corpus = "{}"\'.'.format(
                self.buildenv.srcpath(srcdir)),
            'Please add the corpus parameter to {} manually.'.format(
                str(fuzzer)))

    def test_generate_buildfile_auto_updates(self):
        # No corpus specified in fuzzer's BUILD.gn when metadata was generated.
        fuzzer = self.create_fuzzer('fake-package1/fake-target1')
        label_parts = fuzzer.label.split(':')
        fuzzer_gn = self.buildenv.abspath(label_parts[0], 'BUILD.gn')
        lines_out = [
            'fuzzer("{}") {{'.format(label_parts[1]),
            '  sources = [ "fuzzer.cc" ]',
            '  deps = [ ":my-lib" ]',
            '}',
        ]
        with self.host.open(fuzzer_gn, 'w') as f:
            f.write('\n'.join(lines_out))
        self.host.cwd = self.buildenv.abspath('//current_dir')
        srcdir = 'shared-corpus'
        self.host.mkdir(self.buildenv.abspath(srcdir))
        self.set_input(srcdir)
        self.assertEqual(fuzzer.corpus.generate_buildfile(), [])

        with self.host.open(fuzzer_gn) as f:
            self.assertEqual(
                f.read().split('\n'), [
                    'fuzzer("{}") {{'.format(label_parts[1]),
                    '  sources = [ "fuzzer.cc" ]',
                    '  deps = [ ":my-lib" ]',
                    '  corpus = "{}"'.format(self.buildenv.srcpath(srcdir)),
                    '}',
                ])


if __name__ == '__main__':
    unittest.main()

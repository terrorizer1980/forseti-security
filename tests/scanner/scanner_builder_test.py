# Copyright 2017 The Forseti Security Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests the pipeline builder."""

import os
import unittest.mock as mock

from tests.unittest_utils import ForsetiTestCase
from google.cloud.forseti.scanner import scanner_builder
from tests.scanner.test_data import fake_runnable_scanners


FAKE_TIMESTAMP = '20001225T121212Z'
FAKE_GLOBAL_CONFIGS = {
    'db_host': 'foo',
    'db_user': 'bar',
    'db_name': 'baz'
}


class ScannerBuilderTest(ForsetiTestCase):
    """Tests for the scanner builder."""

    @mock.patch('google.cloud.forseti.scanner.scanners.iam_rules_scanner.iam_rules_engine',
                autospec=True)
    @mock.patch('google.cloud.forseti.scanner.scanners.cloudsql_rules_scanner.cloudsql_rules_engine',
                autospec=True)
    @mock.patch('google.cloud.forseti.scanner.scanners.bucket_rules_scanner.buckets_rules_engine',
                autospec=True)
    @mock.patch('google.cloud.forseti.scanner.scanners.bigquery_scanner.bigquery_rules_engine',
                autospec=True)
    @mock.patch('google.cloud.forseti.scanner.scanner_builder.LOGGER',
                autospec=True)
    def testAllEnabled(self,
                       mock_bigquery_rules_engine,
                       mock_bucket_rules_engine,
                       mock_cloudsql_rules_engine,
                       mock_iam_rules_engine,
                       mock_logger):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS, fake_runnable_scanners.ALL_ENABLED,
            mock.MagicMock(), '', FAKE_TIMESTAMP)
        runnable_pipelines = builder.build()
        self.assertFalse(mock_logger.called)
        self.assertEqual(4, len(runnable_pipelines))

        expected_pipelines = ['BigqueryScanner', 'BucketsAclScanner',
                              'CloudSqlAclScanner', 'IamPolicyScanner']
        for pipeline in runnable_pipelines:
            self.assertTrue(type(pipeline).__name__ in expected_pipelines)

    def testConfigValidator(self):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS, fake_runnable_scanners.CONFIG_VALIDATOR_ENABLED,
            mock.MagicMock(), '', FAKE_TIMESTAMP)
        runnable_pipelines = builder.build()

        self.assertEqual(1, len(runnable_pipelines))
        expected_pipelines = ['ConfigValidatorScanner']
        for pipeline in runnable_pipelines:
            self.assertTrue(type(pipeline).__name__ in expected_pipelines)

    def testAllDisabled(self):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS, fake_runnable_scanners.ALL_DISABLED,
            mock.MagicMock(), '', FAKE_TIMESTAMP)
        runnable_pipelines = builder.build()

        self.assertEqual(0, len(runnable_pipelines))

    @mock.patch('google.cloud.forseti.scanner.scanners.iam_rules_scanner.iam_rules_engine',
                autospec=True)
    def testOneEnabled(self, mock_iam_rules_engine):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS, fake_runnable_scanners.ONE_ENABLED,
            mock.MagicMock(), '', FAKE_TIMESTAMP)
        runnable_pipelines = builder.build()

        self.assertEqual(1, len(runnable_pipelines))
        expected_pipelines = ['IamPolicyScanner']
        for pipeline in runnable_pipelines:
            self.assertTrue(type(pipeline).__name__ in expected_pipelines)

    @mock.patch('google.cloud.forseti.scanner.scanners.iam_rules_scanner.iam_rules_engine',
                autospec=True)
    @mock.patch('google.cloud.forseti.scanner.scanners.bucket_rules_scanner.buckets_rules_engine',
                autospec=True)
    def testTwoEnabled(self, mock_bucket_rules_engine, mock_iam_rules_engine):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS, fake_runnable_scanners.TWO_ENABLED,
            mock.MagicMock(), '', FAKE_TIMESTAMP)
        runnable_pipelines = builder.build()
        self.assertEqual(2, len(runnable_pipelines))
        expected_pipelines = ['BucketsAclScanner', 'IamPolicyScanner']
        for pipeline in runnable_pipelines:
            self.assertTrue(type(pipeline).__name__ in expected_pipelines)

    @mock.patch('google.cloud.forseti.scanner.scanner_builder.LOGGER',
                autospec=True)
    def testNonExistentScannerIsHandled(self, mock_logger):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS, fake_runnable_scanners.NONEXISTENT_ENABLED,
            mock.MagicMock(), '', FAKE_TIMESTAMP)
        runnable_pipelines = builder.build()
        mock_logger.error.assert_called_with(
            'Configured scanner is undefined '
            'in scanner requirements map : %s', 'non_exist_scanner')

        self.assertEqual(1, len(runnable_pipelines))
        expected_pipelines = ['BucketsAclScanner']
        for pipeline in runnable_pipelines:
            self.assertTrue(type(pipeline).__name__ in expected_pipelines)

    @mock.patch('google.cloud.forseti.scanner.scanners.external_project_access_scanner.epa_rules_engine',
                autospec=True)
    def testCanBuildOneSpecificScanner(self, mock_rules_engine):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS,
            fake_runnable_scanners.EXTERNAL_PROJECT_ACCESS_ENABLED,
            mock.MagicMock(),
            '',
            FAKE_TIMESTAMP,
            'external_project_access_scanner')
        runnable_pipelines = builder.build()

        expected_scanner_name = 'ExternalProjectAccessScanner'
        actual_scanner_name = type(runnable_pipelines[0]).__name__
        self.assertEqual(expected_scanner_name, actual_scanner_name)

    @mock.patch('google.cloud.forseti.scanner.scanner_builder.LOGGER',
                autospec=True)
    def testNonExistentScannerRulesIsHandled(self, mock_logger):
        builder = scanner_builder.ScannerBuilder(
            FAKE_GLOBAL_CONFIGS,
            fake_runnable_scanners.NONEXISTENT_RULES_ENABLED,
            mock.MagicMock(),
            '',
            FAKE_TIMESTAMP)

        runnable_scanners = builder.build()

        rules_path = os.path.join(fake_runnable_scanners.test_rules_path,
                                  'firewall_rules.yaml')
        mock_logger.error.assert_called_with(
            f'Rules file for Scanner firewall_rule does not '
            f'exist. Rules path: {rules_path}')

        self.assertEqual(0, len(runnable_scanners))

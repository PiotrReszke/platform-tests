#
# Copyright (c) 2015 Intel Corporation
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
#

from datetime import datetime
import os

from constants.services import ServiceLabels
from service_tools import PsqlTable, PsqlColumn, PsqlRow
from constants.tap_components import TapComponent as TAP
from test_utils import cloud_foundry as cf, app_source_utils, config
from test_utils.remote_logger.remote_logger_decorator import log_components
from objects import Organization, Application, ServiceInstance, ServiceType
from runner.tap_test_case import TapTestCase, cleanup_after_failed_setup
from runner.decorators import priority, components


@log_components()
@components(TAP.service_catalog)
class Postgres(TapTestCase):

    APP_REPO_NAME = "psql-api-example"
    PSQL_APP_DIR = os.path.normpath(os.path.join("../../{}/psql-api-example".format(config.CONFIG["repository"])))
    NAME = datetime.now().strftime("%Y%m%d_%H%M%S")

    test_table_name = "oh_hai"
    test_columns = [{"name": "col0", "type": "character varying", "max_len": 15},
                    {"name": "col1", "type": "integer", "is_nullable": False},
                    {"name": "col2", "type": "boolean", "is_nullable": True}]
    row_value_list = [[{"column_name": "col0", "value": "kitten"}, {"column_name": "col1", "value": 42},
                       {"column_name": "col2", "value": True}],
                      [{"column_name": "col1", "value": 0}],
                      [{"column_name": "col0", "value": None}, {"column_name": "col1", "value": 9000},
                       {"column_name": "col2", "value": None}]]

    @classmethod
    def create_postgres_instance(cls, test_org, test_space):
        cls.step("Create postgres instance")
        marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)
        psql = next(service for service in marketplace if service.label == ServiceLabels.PSQL)
        psql_instance = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.PSQL,
            name="psql_" + cls.NAME,
            service_plan_guid=psql.service_plan_guids[0]
        )
        return psql_instance.name

    @classmethod
    @cleanup_after_failed_setup(Organization.cf_api_tear_down_test_orgs)
    def setUpClass(cls):
        cls.step("Clone or Pull {}".format(cls.APP_REPO_NAME))
        app_source_utils.clone_or_pull_repository(cls.APP_REPO_NAME, cls.PSQL_APP_DIR)
        cls.step("Create test org and test space")
        test_org = Organization.api_create(space_names=("test_name",))
        test_space = test_org.spaces[0]
        cls.step("Login to the new organization")
        cf.cf_login(test_org.name, test_space.name)
        postgres_instance_name = cls.create_postgres_instance(test_org, test_space)
        cls.step("Push psql api app to cf")
        cls.psql_app = Application.push(
            space_guid=test_space.guid,
            source_directory=cls.PSQL_APP_DIR,
            bound_services=(postgres_instance_name,)
        )

    def tearDown(self):
        for table in PsqlTable.TABLES:
            table.delete()

    @priority.medium
    def test_create_table(self):
        test_table = PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        table_list = PsqlTable.get_list(self.psql_app)
        self.assertIn(test_table, table_list)

    @priority.medium
    def test_delete_table(self):
        test_table = PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        test_table.delete()
        table_list = PsqlTable.get_list(self.psql_app)
        self.assertNotIn(test_table, table_list)

    @priority.medium
    def test_get_table_columns(self):
        test_table = PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_columns = [PsqlColumn.from_json_definition(c) for c in self.test_columns]
        expected_columns.append(PsqlColumn("id", "integer", False, None))
        columns = test_table.get_columns()
        self.assertEqual(len(columns), len(expected_columns))
        for column in expected_columns:
            self.assertIn(column, columns)

    @priority.medium
    def test_post_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        for row_id, row_values in list(enumerate(self.row_value_list)):
            with self.subTest(row=row_values):
                row_id += 1  # psql's 1-based indexing
                new_row = PsqlRow.post(self.psql_app, self.test_table_name, row_values)
                row_list = PsqlRow.get_list(self.psql_app, self.test_table_name)
                self.assertIn(new_row, row_list)
                row = PsqlRow.get(self.psql_app, self.test_table_name, row_id)
                self.assertEqual(row, new_row)

    @priority.low
    def test_post_multiple_rows(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        expected_rows = [PsqlRow.post(self.psql_app, self.test_table_name, rv) for rv in self.row_value_list]
        rows = PsqlRow.get_list(self.psql_app, self.test_table_name)
        self.assertListEqual(rows, expected_rows)

    @priority.medium
    def test_put_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        rows = [PsqlRow.post(self.psql_app, self.test_table_name, rv) for rv in self.row_value_list]
        new_values = [{"column_name": "col0", "value": "oh hai"}, {"column_name": "col2", "value": True}]
        rows[1].put(new_values)
        row = PsqlRow.get(self.psql_app, self.test_table_name, row_id=2)
        self.assertEqual(rows[1], row)

    @priority.medium
    def test_delete_row(self):
        PsqlTable.post(self.psql_app, self.test_table_name, self.test_columns)
        posted_rows = [PsqlRow.post(self.psql_app, self.test_table_name, rv) for rv in self.row_value_list]
        posted_rows[1].delete()
        rows = PsqlRow.get_list(self.psql_app, self.test_table_name)
        self.assertNotIn(posted_rows[1], rows)

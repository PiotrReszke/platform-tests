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

from collections import namedtuple
from datetime import datetime
import os

from constants.services import ServiceLabels
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
    NAME_PREFIX = datetime.now().strftime("%Y%m%d_%H%M%S")

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
    def _create_postgres_instance(cls, test_org, test_space):
        cls.step("Create postgres instance")
        marketplace = ServiceType.api_get_list_from_marketplace(test_space.guid)
        psql = next(s for s in marketplace if s.label == ServiceLabels.PSQL)
        psql_instance = ServiceInstance.api_create(
            org_guid=test_org.guid,
            space_guid=test_space.guid,
            service_label=ServiceLabels.PSQL,
            name="psql_" + cls.NAME_PREFIX,
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
        postgres_instance_name = cls._create_postgres_instance(test_org, test_space)
        cls.step("Push psql api app to cf")
        cls.psql_app = Application.push(
            space_guid=test_space.guid,
            source_directory=cls.PSQL_APP_DIR,
            bound_services=(postgres_instance_name,)
        )

    def tearDown(self):
        for table in PsqlTable.TEST_TABLES:
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



class PsqlColumn(namedtuple("PsqlColumn", ["name", "data_type", "is_nullable", "max_len"])):

    def __new__(cls, name, data_type, is_nullable=None, max_len=None):
        is_nullable = True if is_nullable is None else is_nullable
        return super().__new__(cls, name, data_type, is_nullable, max_len)

    @classmethod
    def from_json_definition(cls, column_json):
        return cls(column_json["name"], column_json["type"], column_json.get("is_nullable"),
                   column_json.get("max_len"))


class PsqlTable(namedtuple("PsqlTable", ["psql_app", "name"])):

    TEST_TABLES = []

    @classmethod
    def post(cls, psql_app, table_name, column_json):
        body = {"table_name": table_name, "columns": column_json}
        psql_app.api_request(method="POST", path="tables", body=body)
        table = cls(psql_app, table_name)
        cls.TEST_TABLES.append(table)
        return table

    @classmethod
    def get_list(cls, psql_app):
        response = psql_app.api_request(method="GET", path="tables")
        tables = []
        for item in response["tables"]:
            tables.append(cls(psql_app, item["table_name"]))
        return tables

    def delete(self):
        self.psql_app.api_request(method="DELETE", path="tables/{}".format(self.name))
        self.TEST_TABLES.remove(self)

    def get_columns(self):
        response = self.psql_app.api_request(method="GET", path="tables/{}/columns".format(self.name))
        columns = []
        for item in response["columns"]:
            columns.append(PsqlColumn(item["name"], item["data_type"], item["is_nullable"], item["max_len"]))
        return columns


class PsqlRow(namedtuple("PsqlRow", ["psql_app", "table_name", "id", "values"])):

    @classmethod
    def post(cls, psql_app, table_name, cols_and_values):
        response = psql_app.api_request(method="POST", path="tables/{}/rows".format(table_name),
                                        body=cols_and_values)
        return cls(psql_app, table_name, response["id"], response["values"])

    @classmethod
    def get(cls, psql_app, table_name, row_id):
        response = psql_app.api_request(method="GET", path="tables/{}/rows/{}".format(table_name, row_id))
        return cls(psql_app, table_name, response["id"], response["values"])

    @classmethod
    def get_list(cls, psql_app, table_name):
        response = psql_app.api_request(method="GET", path="tables/{}/rows".format(table_name))
        return [cls(psql_app, table_name, item["id"], item["values"]) for item in response["rows"]]

    def put(self, cols_and_values):
        for new in cols_and_values:
            for old in self.values:
                if new["column_name"] == old["column_name"]:
                   old["value"] = new["value"]
        self.psql_app.api_request(method="PUT", path="tables/{}/rows/{}".format(self.table_name, self.id),
                                  body=cols_and_values)

    def delete(self):
        self.psql_app.api_request(method="DELETE", path="tables/{}/rows/{}".format(self.table_name, self.id))





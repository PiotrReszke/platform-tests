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

from ..logger import get_logger

logger = get_logger("hive calls")

APP_NAME = "hive"


def api_publish_dataset(client, category, creationTime, dataSample, format, is_public,
                        org_guid, recordCount, size, source, target_uri, title):
    """POST /rest/tables"""
    logger.info("------------------ Publish dataset {} ------------------".format(title))
    return client.call(APP_NAME, "publish_dataset", body={"category": category, "creationTime": creationTime,
                                                                    "dataSample": dataSample, "format": format,
                                                                    "isPublic": is_public, "orgUUID": org_guid,
                                                                    "recordCount": recordCount, "size": size,
                                                                    "sourceUri": source, "targetUri": target_uri,
                                                                    "title": title})

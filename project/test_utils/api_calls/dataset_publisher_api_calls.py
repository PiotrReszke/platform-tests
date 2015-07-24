from test_utils import get_logger


APP_NAME = "hive"
logger = get_logger("dataset-publisher calls")


def api_publish_in_hive(client, category, creation_time, data_sample, format, id, is_public, org_guid, record_count,
                        size, source_uri, target_uri, title):
    """POST /rest/tables"""
    logger.debug("------------------ Publish data set {} ------------------".format(id))
    raise NotImplementedError("Please create schema for this method in dataset_publisher_swagger.json")

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

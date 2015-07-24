import test_utils.cli.cloud_foundry as cf


class ServiceInstance(object):

    def __init__(self, guid, name, type, url, org_guid, space_guid, service_plan_guid, credentials):
        self.guid = guid
        self.name = name
        self.type = type
        self.url = url
        self.org_guid = org_guid
        self.space_guid = space_guid
        self.service_plan_guid = service_plan_guid
        self.credentials = credentials

    @classmethod
    def from_cf_api_response(cls, org_guid, response):
        return cls(guid=response["metadata"]["guid"], name=response["entity"]["name"], type=response["entity"]["type"],
                   url=response["metadata"]["url"], org_guid=org_guid, space_guid=response["entity"]["space_guid"],
                   service_plan_guid=response["entity"]["service_plan_guid"], credentials=response["entity"]["credentials"])

    @classmethod
    def cf_api_get_service_instances(cls, org_guid):
        service_instance_data = cf.cf_api_get_service_instances(org_guid)
        service_instances = []
        for data in service_instance_data:
            service_instances.append(cls.from_cf_api_response(org_guid, data))
        return service_instances

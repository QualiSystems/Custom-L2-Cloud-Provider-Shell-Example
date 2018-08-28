from cloudshell.cp.core import DriverRequestParser
from cloudshell.cp.core.models import DriverResponse, DeployApp, DeployAppResult, PrepareCloudInfra, CreateKeys, \
    PrepareSubnet, RemoveVlan, SetVlan
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.cp.core.models import DriverResponse
from cloudshell.shell.core.driver_context import InitCommandContext, AutoLoadCommandContext, ResourceCommandContext, \
    AutoLoadAttribute, AutoLoadDetails, CancellationContext, ResourceRemoteCommandContext

from cloudshell.shell.core.session.cloudshell_session import CloudShellSessionContext

from cloudshell.shell.core.session.logging_session import LoggingSessionContext

from data_model import *
from sdk.heavenly_cloud_service import *
from heavenly_cloud_service_wrapper import HeavenlyCloudServiceWrapper
from cloudshell.core.context.error_handling_context import ErrorHandlingContext
import json
# from data_model import *  # run 'shellfoundry generate' to generate data model classes



class L2HeavenlyCloudShellDriver(ResourceDriverInterface):

    def __init__(self):
        """
        ctor must be without arguments, it is created with reflection at run time
        """
        self.request_parser = DriverRequestParser()

    def initialize(self, context):
        """
        Initialize the driver session, this function is called everytime a new instance of the driver is created
        This is a good place to load and cache the driver configuration, initiate sessions etc.
        :param InitCommandContext context: the context the command runs on
        """
        self.request_parser = DriverRequestParser()
        self.request_parser.add_deployment_model(HeavenlyCloudAngelDeploymentModel)
        self.request_parser.add_deployment_model(HeavenlyCloudManDeploymentModel)


    # <editor-fold desc="Discovery">

    def get_inventory(self, context):

        # uncomment - if there is nothing to validate
        # return AutoLoadDetails([], [])

        # read from context
        cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)

        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            self._log(logger, 'get_inventory_context_json', context)

            # validating
            if cloud_provider_resource.name == 'evil':
                raise ValueError('evil cannot use heaven ')

            if cloud_provider_resource.region == 'sun':
                raise ValueError('invalid region, sorry ca\'nt deploy instances on the sun')

            # using your cloud provider sdk
            if not HeavenlyCloudService.can_connect(cloud_provider_resource.user, cloud_provider_resource.password,
                                                     context.resource.address):  # TODO add address to resource (gal shellfoundry team)
                raise ValueError('could not connect using given credentials')

            # discovering - using your prefered custom cloud service you can discover and then update values
            if not cloud_provider_resource.heaven_cloud_color:
                cloud_provider_resource.heaven_cloud_color = HeavenlyCloudService.get_prefered_cloud_color()

            return cloud_provider_resource.create_autoload_details()

    # </editor-fold>

    # <editor-fold desc="Mandatory Commands">

    def Deploy(self, context, request=None, cancellation_context=None):
        """
       Deploy
       :param ResourceCommandContext context:
       :param str request: A JSON string with the list of requested deployment actions
    :param CancellationContext cancellation_context:
       :return:
       :rtype: str
       """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            with CloudShellSessionContext(context) as cloudshell_session:
                self._log(logger, 'deploy_request', request)
                self._log(logger, 'deploy_context', context)

                # parse the json strings into action objects
                cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)
                actions = self.request_parser.convert_driver_request_to_actions(request)

                # extract DeployApp action
                deploy_action = single(actions, lambda x: isinstance(x, DeployApp))

                # if we have multiple supported deployment options use the 'deploymentPath' property
                # to decide which deployment option to use.
                deployment_name = deploy_action.actionParams.deployment.deploymentPath

                if deployment_name == 'L2HeavenlyCloudShell.HeavenlyCloudAngelDeployment':
                    deploy_result = HeavenlyCloudServiceWrapper.deploy_angel(context, cloudshell_session, cloud_provider_resource, deploy_action, cancellation_context)
                elif deployment_name == 'L2HeavenlyCloudShell.HeavenlyCloudManDeployment':
                    deploy_result = HeavenlyCloudServiceWrapper.deploy_man(context, cloudshell_session,cloud_provider_resource,deploy_action, cancellation_context)
                else:
                    raise ValueError(deployment_name + ' deployment option is not supported.')

                self._log(logger, 'deployment_name', deployment_name)
                self._log(logger, 'deploy_result', deploy_result)


                return DriverResponse([deploy_result]).to_driver_response_json()

    def PowerOn(self, context, ports):
        """
        Will power on the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            self._log(logger, 'power_on_context', context)
            self._log(logger, 'power_on_ports', ports)

            cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)
            resource_ep =  context.remote_endpoints[0]
            deployed_app_dict = json.loads(resource_ep.app_context.deployed_app_json)

            HeavenlyCloudServiceWrapper.power_on(cloud_provider_resource, deployed_app_dict['vmdetails']['uid'])

    def PowerOff(self, context, ports):
        """
        Will power off the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            self._log(logger, 'power_off_context', context)
            self._log(logger, 'power_off_ports', ports)

            cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)
            resource_ep =  context.remote_endpoints[0]
            deployed_app_dict = json.loads(resource_ep.app_context.deployed_app_json)

            HeavenlyCloudServiceWrapper.power_off(cloud_provider_resource, deployed_app_dict['vmdetails']['uid'])

    def PowerCycle(self, context, ports, delay):
        pass

    def DeleteInstance(self, context, ports):
        """
        Will delete the compute resource
        :param ResourceRemoteCommandContext context:
        :param ports:
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            self._log(logger, 'DeleteInstance_context', context)
            self._log(logger, 'DeleteInstance_ports', ports)

            cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)
            resource_ep =  context.remote_endpoints[0]
            deployed_app_dict = json.loads(resource_ep.app_context.deployed_app_json)

            HeavenlyCloudServiceWrapper.delete_instance(cloud_provider_resource, deployed_app_dict['vmdetails']['uid'])


    def GetVmDetails(self, context, requests, cancellation_context):
        """

        :param ResourceCommandContext context:
        :param str requests:
        :param CancellationContext cancellation_context:
        :return:
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            self._log(logger, 'GetVmDetails_context', context)
            self._log(logger, 'GetVmDetails_requests', requests)
            cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)
            result = HeavenlyCloudServiceWrapper.get_vm_details(logger, cloud_provider_resource, cancellation_context,
                                                                 requests)
            result_json = json.dumps(result, default=lambda o: o.__dict__, sort_keys=True, separators=(',', ':'))

            self._log(logger, 'GetVmDetails_result', result_json)

            return result_json


    def remote_refresh_ip(self, context, ports, cancellation_context):
        """
        Will update the address of the computer resource on the Deployed App resource in cloudshell
        :param ResourceRemoteCommandContext context:
        :param ports:
        :param CancellationContext cancellation_context:
        :return:
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            with CloudShellSessionContext(context) as cloudshell_session:
                self._log(logger, 'remote_refresh_ip_context', context)
                self._log(logger, 'remote_refresh_ip_ports', ports)
                self._log(logger, 'remote_refresh_ip_cancellation_context', cancellation_context)
                cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)
                deployed_app_dict = json.loads(context.remote_endpoints[0].app_context.deployed_app_json)
                remote_ep =  context.remote_endpoints[0]
                deployed_app_private_ip = remote_ep.address
                deployed_app_public_ip = None

                public_ip_att = first_or_default(deployed_app_dict['attributes'],lambda x:x['name'] == 'Public IP')

                if public_ip_att:
                    deployed_app_public_ip = public_ip_att['value']

                deployed_app_fullname = remote_ep.fullname
                vm_instance_id = deployed_app_dict['vmdetails']['uid']

                HeavenlyCloudServiceWrapper.remote_refresh_ip(cloud_provider_resource, cancellation_context, cloudshell_session, deployed_app_fullname, vm_instance_id, deployed_app_private_ip, deployed_app_public_ip)

    def ApplyConnectivityChanges(self, context, request):
        """
        Configures VLANs on multiple ports or port-channels
        :param ResourceCommandContext context: The context object for the command with resource and reservation info
        :param str request: A JSON string with the list of requested connectivity changes
        :return: a json object with the list of connectivity changes which were carried out by the driver
        :rtype: str
        """
        with LoggingSessionContext(context) as logger, ErrorHandlingContext(logger):
            self._log(logger, 'ApplyConnectivityChanges_request', request)
            self._log(logger, 'ApplyConnectivityChanges_context', context)

            # parse the json strings into action objects
            cloud_provider_resource = L2HeavenlyCloudShell.create_from_context(context)
            actions = self.request_parser.convert_driver_request_to_actions(request)

            # extract Set/Remove vlan actions
            remove_vlan_actions = filter(lambda x: isinstance(x, RemoveVlan), actions)
            remove_vlan_results = HeavenlyCloudServiceWrapper.disconnect_all(logger, cloud_provider_resource, remove_vlan_actions)

            set_vlan_actions = filter(lambda x: isinstance(x, SetVlan), actions)
            set_vlan_results = HeavenlyCloudServiceWrapper.connect_all(logger, cloud_provider_resource, set_vlan_actions)

            return DriverResponse(remove_vlan_results + set_vlan_results).to_driver_response_json()

    # </editor-fold>


    def SetAppSecurityGroups(self, context, request):
        """

        :param ResourceCommandContext context:
        :param str request:
        :return:
        :rtype: str
        """
        pass

    # </editor-fold>

    def cleanup(self):
        """
        Destroy the driver session, this function is called everytime a driver instance is destroyed
        This is a good place to close any open sessions, finish writing to log files, etc.
        """
        pass

    def _log(self, logger, name, obj):

        if not obj:
            logger.info(name + 'Value  is None')

        if not self._is_primitive(obj):
            name = name + '__json_serialized'
            obj = json.dumps(obj, default=lambda o: o.__dict__, sort_keys=True, separators=(',', ':'))

        logger.info(name)
        logger.info(obj)

    def _is_primitive(self, thing):
        primitive = (int, str, bool, float, unicode)
        return isinstance(thing, primitive)
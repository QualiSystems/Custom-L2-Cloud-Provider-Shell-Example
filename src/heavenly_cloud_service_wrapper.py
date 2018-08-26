import uuid
import os
from cloudshell.cp.core.models import *
from data_model import *
from sdk.heavenly_cloud_service import HeavenlyCloudService
import json
from typing import List

class HeavenlyCloudServiceWrapper(object):

    @staticmethod
    def deploy_angel(context, cloudshell_session, cloud_provider_resource,deploy_app_action, cancellation_context):
        """
        :param ResourceCommandContext context:
        :param CloudShellAPISession cloudshell_session:
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param DeployApp deploy_app_action:
        :param CancellationContext cancellation_context:
        """

        if cancellation_context.is_cancelled:
            HeavenlyCloudService.rollback()
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False,
                                   errorMessage='Operation canceled')

        # deployment_model type : HeavenlyCloudAngelDeploymentModel
        deployment_model = deploy_app_action.actionParams.deployment.customModel

        # generate unique name to avoid name collisions
        vm_unique_name = deploy_app_action.actionParams.appName + '__' + str(uuid.uuid4())[:6]

        input_user = deploy_app_action.actionParams.appResource.attributes['User']
        input_password = cloudshell_session.DecryptPassword(deploy_app_action.actionParams.appResource.attributes['Password']).Value

        new_pass = HeavenlyCloudService.create_new_password(cloud_provider_resource,input_user,input_password)

        try:
            # using cloud provider SDK, creating the instance
            vm_instance = HeavenlyCloudService.create_angel_instance(input_user,new_pass,cloud_provider_resource,vm_unique_name,
                                                                      deployment_model.wing_count,
                                                                      deployment_model.flight_speed,
                                                                      deployment_model.cloud_size,
                                                                      deployment_model.cloud_image_id)
        except Exception as e:
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False, errorMessage=e.message)

        # Creating VmDetailsData
        vm_details_data = HeavenlyCloudServiceWrapper.extract_vm_details(vm_instance)

        # result must include the action id it results for, so server can match result to action
        action_id = deploy_app_action.actionId


        # optional
        # deployedAppAttributes contains the attributes on the deployed app
        # use to override attributes default values
        deployed_app_attributes = []
        deployed_app_attributes.append(Attribute('Password',input_password + '_decrypted'))


        # optional
        # deployedAppAdditionalData can contain dynamic data on the deployed app
        # similar to AWS tags
        deployed_app_additional_data_dict = {'Reservation Id': context.reservation.reservation_id , 'CreatedBy' : str(os.path.abspath(__file__))}

        return DeployAppResult(actionId=action_id, success=True, vmUuid=vm_instance.id, vmName=vm_unique_name,
                               deployedAppAddress=vm_instance.private_ip, deployedAppAttributes=deployed_app_attributes,
                               deployedAppAdditionalData=deployed_app_additional_data_dict,
                               vmDetailsData=vm_details_data)

    @staticmethod
    def deploy_man(context, cloudshell_session, cloud_provider_resource, deploy_app_action, cancellation_context):
        """
        :param ResourceCommandContext context:
        :param CloudShellAPISession cloudshell_session:
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param DeployApp deploy_app_action:
        :param CancellationContext cancellation_context:
        """

        if cancellation_context.is_cancelled:
            HeavenlyCloudService.rollback()
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False,
                                   errorMessage='Operation canceled')

        # deployment_model type : HeavenlyCloudAngelDeploymentModel
        deployment_model = deploy_app_action.actionParams.deployment.customModel

        # generate unique name to avoid name collisions
        vm_unique_name = deploy_app_action.actionParams.appName + '__' + str(uuid.uuid4())[:6]

        input_user = deploy_app_action.actionParams.appResource.attributes['User']
        encrypted_pass = deploy_app_action.actionParams.appResource.attributes['Password']

        # decrypt password using cloudshell session
        input_password = cloudshell_session.DecryptPassword(encrypted_pass).Value
        new_pass = HeavenlyCloudService.create_new_password(cloud_provider_resource, input_user, input_password)

        try:
            # using cloud provider SDK, creating the instance
            vm_instance = HeavenlyCloudService.create_man_instance(input_user, new_pass, cloud_provider_resource,
                                                                   vm_unique_name,
                                                                   deployment_model.weight,
                                                                   deployment_model.height,
                                                                   deployment_model.cloud_size,
                                                                   deployment_model.cloud_image_id)
        except Exception as e:
            return DeployAppResult(actionId=deploy_app_action.actionId, success=False, errorMessage=e.message)

        # Creating VmDetailsData
        vm_details_data = HeavenlyCloudServiceWrapper.extract_vm_details(vm_instance)

        # result must include the action id it results for, so server can match result to action
        action_id = deploy_app_action.actionId

        # optional
        # deployedAppAttributes contains the attributes on the deployed app
        # use to override attributes default values
        deployed_app_attributes = []
        deployed_app_attributes.append(Attribute('Password', input_password + '_decrypted'))

        # optional
        # deployedAppAdditionalData can contain dynamic data on the deployed app
        # similar to AWS tags
        deployed_app_additional_data_dict = {'Reservation Id': context.reservation.reservation_id,
                                             'CreatedBy': str(os.path.abspath(__file__))}

        return DeployAppResult(actionId=action_id, success=True, vmUuid=vm_instance.id, vmName=vm_unique_name,
                               deployedAppAddress=vm_instance.private_ip, deployedAppAttributes=deployed_app_attributes,
                               deployedAppAdditionalData=deployed_app_additional_data_dict,
                               vmDetailsData=vm_details_data)

    @staticmethod
    def extract_vm_details(vm_instance):
        """
        :param HeavenResidentInstance vm_instance:
        """
        vm_instance_data = HeavenlyCloudServiceWrapper.extract_vm_instance_data(vm_instance)
        vm_network_data =  HeavenlyCloudServiceWrapper.extract_vm_instance_network_data(vm_instance)

        return VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data)


    @staticmethod
    def extract_vm_instance_data(vm_instance):
        """
        :param HeavenResidentInstance vm_instance:
        """
        data = [
            VmDetailsProperty(key='Cloud Size', value='not so big'),
            VmDetailsProperty(key='Instance Name', value='dummy' if not vm_instance else vm_instance.name),
            VmDetailsProperty(key='Hidden stuff', value='something not for UI',hidden=True),
        ]

        return data

    @staticmethod
    def extract_vm_instance_network_data(vm_instance):
        """
        :param HeavenResidentInstance vm_instance:
        """
        network_interfaces = []

        # for each network interface
        for i in range(2):
            network_data = [
                VmDetailsProperty(key='Device Index', value=str(i)),
                VmDetailsProperty(key='MAC Address', value=str(uuid.uuid4())),
                VmDetailsProperty(key='Speed', value='1KB'),
            ]

            current_interface = VmDetailsNetworkInterface(interfaceId=i, networkId=i,
                                                          isPrimary=i == 0,  # specifies whether nic is the primary interface
                                                          isPredefined=False, # specifies whether network existed before reservation
                                                          networkData=network_data,

                                                          privateIpAddress='10.0.0.' + str(i),
                                                          publicIpAddress='8.8.8.' + str(i))
            network_interfaces.append(current_interface)

        return network_interfaces

    @staticmethod
    def get_vm_details(cloud_provider_resource, cancellation_context, requests_json):

        """
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param CancellationContext cancellation_context:
        :param str requests_json:
        :param str vm_id:
        """
        requests = json.loads(requests_json)

        results = []

        for request in requests[u'items']:

            if cancellation_context.is_cancelled:
                break

            vm_name = request[u'deployedAppJson'][u'name']
            vm_uid =  request[u'deployedAppJson'][u'vmdetails'][u'uid']
            address = request[u'deployedAppJson'][u'address']

            vm_instance = HeavenlyCloudService.get_instance(cloud_provider_resource, vm_name, vm_uid, address)
            vm_instance_data = HeavenlyCloudServiceWrapper.extract_vm_instance_data(vm_instance)
            vm_network_data = HeavenlyCloudServiceWrapper.extract_vm_instance_network_data(vm_instance)

            # example of reading custom data created via deployed_app_additional_data_dict at delpoy stage
            # created_by = next((deployed_app_additional_data['value'] for deployed_app_additional_data in request[u'deployedAppJson'][u'vmdetails'][u'vmCustomParams'] if
            #                    deployed_app_additional_data['name'] == 'CreatedBy'), None)
            # if created_by:
            #     vm_instance_data.append(VmDetailsProperty(key='CreatedBy',value=created_by))

            # TODO when prepare connectivity is finished uncomment
            # currently we get error: Check failed because resource is connected to more than one subnet, while reservation doesn't have any subnet services
            # result = VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data, appName=vm_name)
            result = VmDetailsData(vmInstanceData=vm_instance_data, vmNetworkData=vm_network_data, appName=vm_name)
            results.append(result)

        return results

    @staticmethod
    def power_on(cloud_provider_resource, vm_id):
        """
         :param L2HeavenlyCloudShell cloud_provider_resource:
         :param str vm_id:
         """
        HeavenlyCloudService.power_on(cloud_provider_resource,vm_id)

    @staticmethod
    def power_off(cloud_provider_resource, vm_id):
        """
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param str vm_id:
        """
        HeavenlyCloudService.power_off(cloud_provider_resource, vm_id)

    @staticmethod
    def remote_refresh_ip(cloud_provider_resource, cancellation_context, cloudshell_session, resource_full_name, vm_id, deployed_app_private_ip, deployed_app_public_ip):
        """
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param CancellationContext cancellation_context:
        :param CloudShellAPISession cloudshell_session:
        :param str resource_full_name:
        :param str vm_id:
        :param str deployed_app_private_ip:
        :param str deployed_app_public_ip:
        """
        curr_ip = HeavenlyCloudService.remote_refresh_ip(cloud_provider_resource, cancellation_context, resource_full_name,vm_id)

        if deployed_app_private_ip != curr_ip:
            cloudshell_session.UpdateResourceAddress(resource_full_name, curr_ip)

        if not deployed_app_public_ip:
            cloudshell_session.SetAttributeValue(resource_full_name, "Public IP", '1.1.1.1')

    @staticmethod
    def delete_instance(cloud_provider_resource, vm_id):
        HeavenlyCloudService.delete_instance(cloud_provider_resource, vm_id)

    @staticmethod
    def prepare_sandbox_infra(logger, cloud_provider_resource, prepare_infa_action, create_keys_action,
                              prepare_subnet_actions):
        """
        :param logging.Logger logger:
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param PrepareCloudInfra prepare_infa_action:
        :param CreateKeys create_keys_action:
        :param List[PrepareSubnet] prepare_subnet_actions:
        :return:
        :rtype:
        """

        results = []

        # handle PrepareInfraAction - extract sandbox CIDR and create/allocate a network in the cloud provider with
        # an address range of the provided CIDR
        cidr = prepare_infa_action.actionParams.cidr
        logger.info("Received CIDR {0} from server".format(cidr))
        results.append(PrepareCloudInfraResult(prepare_infa_action.actionId))

        # handle CreateKeys - generate key pair or get it from the cloud provider and save it in a secure location
        # that will be accessible from the Deploy method
        results.append(CreateKeysActionResult(create_keys_action.actionId, accessKey='my_ssh_key'))

        # handle prepareSubnets

    @staticmethod
    def connect(logger, cloud_provider_resource, set_vlan_action):
        """
        :param logging.Logger logger:
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param SetVlan set_vlan_action:
        :return:
        :rtype: SetVlanResult
        """
        try:
            vnic_name = '' if not 'Vnic Name'  in set_vlan_action.customActionAttributes else set_vlan_action.customActionAttributes['Vnic Name']
            interface_id = HeavenlyCloudService.connect_vlan(cloud_provider_resource, set_vlan_action)

            return SetVlanResult(actionId=set_vlan_action.actionId, success=True,infoMessage=vnic_name + ' requested', updatedInterface=interface_id)
        except Exception as e:
            return SetVlanResult(actionId=set_vlan_action.actionId, success=False, errorMessage=e.message)

    @staticmethod
    def connect_all(logger, cloud_provider_resource, set_vlan_actions):
        """
        :param logging.Logger logger:
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param [SetVlan] set_vlan_actions:
        :return:
        :rtype: [SetVlanResult]
        """

        # vlan_type = cloud_provider_resource.vlan_type
        # vlan_type "VLAN" : cloudshell will allow VLAN ids in the 2-4096 range
        # vlan_type "XVLAN"  cloudshell will allow VLAN ids to be allocated in range 2-16,000,000
        # the default value is VLAN
        if not set_vlan_actions:
            return []

        actions_results = []
        for set_vlan_action in set_vlan_actions:
            actions_results.append(HeavenlyCloudServiceWrapper.connect(logger, cloud_provider_resource, set_vlan_action))

        return actions_results

    @staticmethod
    def disconnect(cloud_provider_resource, remove_vlan_action):
        """
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param RemoveVlan remove_vlan_action:
        :return:
        :rtype: RemoveVlanResult
        """

        try:

            disconnect_interface_id = remove_vlan_action.connectorAttributes['Interface']
            vm_instance_id = remove_vlan_action.customActionAttributes['VM_UUID']

            HeavenlyCloudService.disconnect_vlan(cloud_provider_resource,disconnect_interface_id, vm_instance_id)

            return RemoveVlanResult(actionId=remove_vlan_action.actionId, success=True, updatedInterface=disconnect_interface_id)
        except Exception as e:
            return RemoveVlanResult(actionId=remove_vlan_action.actionId, success=False,errorMessage=e.message)


    @staticmethod
    def disconnect_all(logger, cloud_provider_resource, remove_vlan_actions):
        """
        :param logging.Logger logger:
        :param L2HeavenlyCloudShell cloud_provider_resource:
        :param [RemoveVlan] remove_vlan_actions:
        :return:
        :rtype: [RemoveVlanResult]
        """

        if not remove_vlan_actions:
            return []

        actions_results = []

        for remove_vlan_action in remove_vlan_actions:
            actions_results.append(HeavenlyCloudServiceWrapper.disconnect(cloud_provider_resource, remove_vlan_action))

        return actions_results
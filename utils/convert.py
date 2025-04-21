from utils import get_k8s_object
import datetime
import time
from baseclasses.Pod import Pod
from baseclasses.Node import Node


def mem_convert_to_int(resource_string):
    """
    将资源字符串转换为整数(字节)

    参数:
        resource_string (str):资源字符串

    返回:
        (int):从资源字符串转换的字节数

    Examples:
        '2Gi' --> 2147483648
    """
    if 'Ki' in resource_string:
        return int(resource_string.split('K')[0]) * 1024
    elif 'Mi' in resource_string:
        return int(resource_string.split('M')[0]) * (1024 ** 2)
    elif 'Gi' in resource_string:
        return int(resource_string.split('G')[0]) * (1024 ** 3)


def cpu_convert_to_milli_value(resource_string):
    """将cpu资源字符串转换为整数(字节)
    参数:
        resource (str): Cpu资源字符串

    返回:
        (int):从cpu资源字符串转换的milli_value的个数

    Examples:
            '2' --> 2000
        """
    if 'm' in resource_string:
        return int(resource_string.split('m')[0])
    else:
        return int(resource_string) * 1000


# datetime对象转换为时间戳
def convert_to_timestamp(dt):
    # 将 datetime 对象转换为 UTC 时间
    dt = dt.astimezone(datetime.timezone.utc)
    # 将 datetime 对象转换为时间戳
    timestamp = time.mktime(dt.timetuple())
    return timestamp


# k8s_pod对象转换为我的Pod对象
def convert_k8s_pod_to_my_pod(k8s_pod):
    mem_req = get_k8s_object.get_k8s_pod_memory_request(k8s_pod)
    cpu_req = get_k8s_object.get_k8s_pod_cpu_request(k8s_pod)
    start_time = convert_to_timestamp(k8s_pod.metadata.creation_timestamp)
    if k8s_pod.metadata.labels and 'execution_time' in k8s_pod.metadata.labels:
        execution_time = k8s_pod.metadata.labels['execution_time']
        load = 1
    else:
        execution_time = 0
        load = 0
    return Pod(name=k8s_pod.metadata.name, node=k8s_pod.spec.node_name, k8s_pod=k8s_pod,
               start_time=start_time, execution_time=execution_time,
               load=load, memory_request=mem_req, cpu_request=cpu_req)


# 所有k8s_node对象转换为我的Node对象
def convert_all_k8s_nodes_to_my_nodes():
    nodes = get_k8s_object.k8s_nodes_available(only_name=False, is_edge=True)
    my_nodes = dict()
    for n in nodes:
        # print(n.status)
        my_nodes[n.metadata.name] = Node(ip=n.status.addresses[0].address, name=n.metadata.name, k8s_node=n,
                                         capacity_cpu=cpu_convert_to_milli_value(n.status.capacity['cpu']),
                                         allocatable_cpu=cpu_convert_to_milli_value(n.status.allocatable['cpu']),
                                         capacity_memory=mem_convert_to_int(n.status.capacity['memory']),
                                         allocatable_memory=mem_convert_to_int(n.status.allocatable['memory']))
    return my_nodes

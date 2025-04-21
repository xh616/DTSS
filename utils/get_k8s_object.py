from kubernetes import client
from config import config as custom_config
from utils import convert


def get_node_ip_by_name(name):
    for node_name, node_ip in custom_config.EDGE_NODES_IPs.items():
        if node_name == name:
            return node_ip
    return "node名称错误"


def get_node_name_by_ip(ip):
    for node_name, node_ip in custom_config.EDGE_NODES_IPs.items():
        if node_ip == ip:
            return node_name
    return "ip错误"


# 获取所有节点（名称/k8s_node对象， 是否只要边节点）
def k8s_nodes_available(only_name=False, is_edge=True):
    ready_nodes = []
    for n in client.CoreV1Api().list_node().items:
        if not n.spec.unschedulable:
            for status in n.status.conditions:
                if is_edge:
                    if 'node-role.kubernetes.io/edge' in n.metadata.labels.keys():
                        if status.status == "True" and status.type == "Ready":
                            if only_name:
                                ready_nodes.append(n.metadata.name)
                            else:
                                ready_nodes.append(n)
                else:
                    if status.status == "True" and status.type == "Ready":
                        if only_name:
                            ready_nodes.append(n.metadata.name)
                        else:
                            ready_nodes.append(n)
    return ready_nodes


# 获取pod所有容器的内存请求总和
def get_k8s_pod_memory_request(pod):
    return sum([convert.mem_convert_to_int(x.resources.requests['memory']) for x in pod.spec.containers if
                x.resources.requests is not None])


# 获取pod所有容器的CPU请求总和
def get_k8s_pod_cpu_request(pod):
    return sum([convert.cpu_convert_to_milli_value(x.resources.requests['cpu']) for x in pod.spec.containers if
                x.resources.requests is not None])


# 获取所有node上的所有pod
def get_node_pods():
    nodes = k8s_nodes_available(only_name=False, is_edge=True)
    node_pods = dict()
    for n in nodes:
        pods_object = []
        pods = client.CoreV1Api().list_pod_for_all_namespaces(field_selector=f'spec.nodeName='f'{n.metadata.name}')\
            .items
        for pod in pods:
            if pod.metadata.namespace == "k8s":
                pods_object.append(convert.convert_k8s_pod_to_my_pod(pod))
        node_pods[n.metadata.name] = pods_object
    return node_pods

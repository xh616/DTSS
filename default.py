import kubernetes as k8s
from kubernetes.client.rest import ApiException
from kubernetes import client, watch
import json
from utils import get_k8s_object
from config import config as custom_config
import rpd
import threading
import time


def watch_real_k8s_events():
    w = watch.Watch()
    v1 = client.CoreV1Api()
    for event in w.stream(v1.list_namespaced_pod, "k8s"):
        print(f"---->监听到pod ::{event['object'].metadata.name} 事件:: {event['type']}<----")
        if event['object'].status.phase == "Pending" and event['type'] == "ADDED":
            try:
                pod_name = event['object'].metadata.name
                print("创建 pod - named {}".format(pod_name))
                for p, t in custom_config.pod_time.items():
                    if pod_name == p:
                        print("启动定时线程")
                        # 开个线程定时杀短期pod
                        threading.Thread(target=remove_pod, args=(pod_name, t)).start()
            except client.rest.ApiException as e:
                print("异常:" + json.loads(e.body)['message'])
                pass
        if event['object'].status.phase == "Running" and event['type'] == "MODIFIED":
            print(f"记录数据")
            rpd.record(event['object'].metadata.name)
        elif event['type'] == "DELETED":
            print(f"删除pod")


def remove_pod(pod_name, wait_time):
    time.sleep(wait_time)
    try:
        client.CoreV1Api().delete_namespaced_pod(pod_name, "k8s")
    except ApiException as e:
        print("调用CoreV1Api->delete_namespaced_pod时发出警告: %s\n" % e)


def main():
    # 加载配置文件 这里的配置文件是集群中的$HOME/.kube/config 文件，直接去集群中粘贴过来即可
    k8s.config.load_kube_config(config_file=".kube/config")
    ready_nodes = {}
    nodes = get_k8s_object.k8s_nodes_available(only_name=True, is_edge=True)
    for n in nodes:
        ip = get_k8s_object.get_node_ip_by_name(n)
        ready_nodes[n] = ip
    print(ready_nodes)
    watch_real_k8s_events()


if __name__ == '__main__':
    main()

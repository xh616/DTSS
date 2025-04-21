import kubernetes as k8s
from kubernetes.client.rest import ApiException
from kubernetes import client, watch
import json
from baseclasses.Scheduler import CustomScheduler
from utils import get_k8s_object
from config import config as custom_config
import threading


def watch_real_k8s_events(scheduler):
    w = watch.Watch()
    # 持续监听命名空间下的对象的状态变化，判断pod的状态是否处于”Peng“、事件类型是否是添加、指定的调度器是都是本程序的自定义调度器名称
    for event in w.stream(scheduler.v1.list_namespaced_pod, "k8s"):
        print(f"---->监听到pod ::{event['object'].metadata.name} 事件:: {event['type']}<----")
        if event['object'].status.phase == "Pending" and event['type'] == "ADDED" and \
                event['object'].spec.scheduler_name == scheduler.scheduler_name:
            try:
                pod_name = event['object'].metadata.name
                print("创建 pod - named {}".format(pod_name))
                scheduler.schedule(event['object'])
                for p, t in custom_config.pod_time.items():
                    if pod_name == p:
                        # 开个线程定时杀短期pod
                        threading.Thread(target=scheduler.remove_pod, args=(pod_name, t)).start()
            except client.rest.ApiException as e:
                print("异常:" + json.loads(e.body)['message'])
                pass
        if event['type'] == "DELETED" and event['object'].spec.scheduler_name == scheduler.scheduler_name:
            scheduler.update_node_pods(event['object'])


def main():
    # 加载配置文件 这里的配置文件是集群中的$HOME/.kube/config 文件，直接去集群中粘贴过来即可
    k8s.config.load_kube_config(config_file=".kube/config")
    ready_nodes = {}
    nodes = get_k8s_object.k8s_nodes_available(only_name=True, is_edge=True)
    for n in nodes:
        ip = get_k8s_object.get_node_ip_by_name(n)
        ready_nodes[n] = ip
    print(ready_nodes)
    scheduler = CustomScheduler()
    print("---->自定义调度器启动<---->")
    watch_real_k8s_events(scheduler)


if __name__ == '__main__':
    main()

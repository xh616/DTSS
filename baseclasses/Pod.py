class Pod(object):
    def __init__(self, name, node, k8s_pod, start_time, execution_time, load, memory_request=None,
                 cpu_request=None):
        # pod名称
        self.name = name
        # pod所在节点
        self.node = node
        # k8s的pod对象
        self.k8s_pod = k8s_pod
        # 任务的开始时间和执行时间
        self.start_time = start_time
        self.execution_time = int(execution_time)
        # 任务类型，1为短期任务负载，0为长期任务负载
        self.load = load
        # pod的内存请求
        self.memory_request = memory_request
        # pod的CPU请求
        self.cpu_request = cpu_request

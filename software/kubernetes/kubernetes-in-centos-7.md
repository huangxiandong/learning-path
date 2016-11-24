# kubernetes in centos 7 

# 安装 Guest Additions

vagrant plugin install vagrant-vbguest
#这时在 Vagrantfile 中不要设置目录映射, 添加以下配置

```
config.vbguest.auto_update = false
# do NOT download the iso file from a webserver
config.vbguest.no_remote = true
```

vagrant up
vagrant vbguest
// 这时会自动安装 Guest Additions， 再关闭vm，配置上目录映射，再up，就可以了
// 家里的网络连接 centos 官方的源，速度还行， 可以不用改成国内源。


# 国内源

sudo cp /etc/yum.repos.d/CentOS-Base.repo /etc/yum.repos.d/CentOS-Base.repo.bak

wget http://mirrors.163.com/.help/CentOS7-Base-163.repo -O CentOS-Base.repo
mv CentOS-Base.repo /etc/yum.repos.d/

sudo yum makecache
sudo yum update

# install docker

sudo tee /etc/yum.repos.d/docker.repo <<-'EOF'
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/centos/7/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF

sudo yum install docker-engine

sudo systemctl enable docker.service

sudo systemctl start docker

配置 http_proxy:

vim /lib/systemd/system/docker.service 在[Service]中添加：
EnvironmentFile=-/etc/docker/docker.conf
这里的 减号 表示如果文件不存在，则忽略错误

vim /etc/docker/docker.conf 添加：
http_proxy=192.168.0.2:7777
https_proxy=192.168.0.2:7777
no_proxy=localhost,127.0.0.1,192.168.0.2

重启 dockerd

# start etcd
etcd --listen-client-urls 'http://0.0.0.0:2379,http://0.0.0.0:4001' --advertise-client-urls 'http://192.168.0.2:2379,http://192.168.0.2:4001'  > /dev/null 2>&1 &

# install kube
去 github release page 下载最新的版本. 大约 1G.


# start master 

hyperkube apiserver --address=0.0.0.0 --etcd_servers=http://192.168.0.2:2379 --service-cluster-ip-range=10.10.0.0/16 --v=0 >apiserver.log 2>&1 &

hyperkube controller-manager --master=127.0.0.1:8080 --logtostderr=true >cm.log 2>&1 &

日志有有报错，pem 文件找不到，和下面这两个配置有关，需要搜索
--cluster-signing-cert-file string                                  Filename containing a PEM-encoded X509 CA certificate used to issue cluster-scoped certificates (default "/etc/kubernetes/ca/ca.pem")
--cluster-signing-key-file string                                   Filename containing a PEM-encoded RSA or ECDSA private key used to sign cluster-scoped certificates (default "/etc/kubernetes/ca/ca.key")

hyperkube scheduler --master=127.0.0.1:8080 > scheduler.log 2>&1 &

提示 Could not construct reference... due to: 'selfLink was empty, can't make reference'

# start node

建议先看 安装DNS，kubelet 要添加两个启动参数

hyperkube proxy --master=192.168.0.2:8080 --logtostderr=true >proxy.log 2>&1 &

hyperkube kubelet --api_servers=192.168.0.2:8080 --address=0.0.0.0 --hostname_override=192.168.0.3 --healthz-bind-address=0.0.0.0 --logtostderr=true >kubelet.log 2>&1 &

# 问题

启动 dashboard 的之前，需要 打开一段注释，args: - --apiserver-host=http://192.168.0.2:8080,
否则 dashboard 无法启动

kubectl describe pods/kubernetes-dashboard-3985220203-j043h --namespace=kube-system
看到event信息报错, 启动其他 image 的时候也有这个错，需要查找
MissingClusterDNS, kubelet does not have ClusterDNS IP configured and cannot create Pod using "ClusterFirst" policy. Falling back to DNSDefault policy.

kubelet log显示 CPUAccounting not allowed
这个问题估计是 systemd 控制的

# 安装 skyDNS
进入 kubernetes/cluster/addons/dns/ 目录， 需要使用到 skydns-rc.yaml.in, skydns-svc.yaml.in, 这两个文件。 

1. rc 需要替换的变量：
replica = 1
dns_domain = cluster.local

kube-dns 启动参数需要指定 master 的接口
```
args:
# command = "/kube-dns"
- --kube-master-url=http://192.168.0.2:8080
```

2. svc 需要替换的变量：
dns_server = 10.10.0.10 // 这个ip需要在 apiserver 的启动参数--service-cluster-ip-range设置的ip段 里面，随意定义一个.

用kubectl create -f 启动 rc , svc.

kubelet 启动参数需要加入 --cluster-dns=10.10.0.10 --cluster-domain=cluster.local

完整的启动命令为：
hyperkube kubelet --api_servers=192.168.0.2:8080 --address=0.0.0.0 --hostname_override=192.168.0.3 --healthz-bind-address=0.0.0.0 --logtostderr=true --cluster-dns=10.10.0.10 --cluster-domain=cluster.local >kubelet.log 2>&1 &

观察启动结果：
kubectl get rc --namespace=kube-system
kubectl get svc --namespace=kube-system

最后在 node机 上测试 DNS:
dig @10.10.0.10 hello.default.svc.cluster.local

```
;; ANSWER SECTION:
hello.default.svc.cluster.local. 30 IN  A   10.10.83.26
```

这里 hello 是 之前起的一个deploy

```
kind: Service
apiVersion: v1
metadata:
  labels:
    app: hello
  name: hello
spec:
  ports:
  - port: 9090
  selector:
    run: hello
---
apiVersion: extensions/v1beta1
kind: Deployment
metadata:
  name: hello
spec:
  replicas: 1
  template:
    metadata:
      labels:
        run: hello
    spec:
      containers:
      - name: hello
        image: silentred/alpine-hello:v1
        ports:
        - containerPort: 9090
```

如果想升级 image:
`kubectl set image deploy/hello hello=silentred/alpine-hello:v2`

进入容器内部:
```
docker exec -it CONTAINER_ID bash

// resolv.conf 的内容，估计是 dns 插件自动生成的
bash-4.4# cat /etc/resolv.conf
search default.svc.cluster.local svc.cluster.local cluster.local pek2.qingcloud.com.
nameserver 10.10.0.10
options ndots:5
```

安装完kube-dns插件后，在容器内部使用DNS查找到的ip为该 service 的 clusterIP, 在容器内部ping自身的name(hello)没有响应；并且删除svc/hello后，DNS就无法找到hello这个服务了。
无法ping通，但是 tcp 可以访问！ 这表示，在程序中直接使用 dial("hello"), 就能通过 service 去轮询各个 container, 可以不使用 grpc 自带的 LB 策略了。


# 结合 flannel

flannel 配置的子网范围 是否必须和 apiserver 的 clusterIP 一致？
听说可以不一致，clusterIP 的原理需要再看一下。



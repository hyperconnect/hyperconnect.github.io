---
layout: post
date: 2021-03-08
title: Bottlerocket in Production Kubernetes Cluster
author: sammie
tags: kubernetes cluster bottlerocket os
excerpt: AWS에서 container를 위해 새로 만든 운영체제인 Bottlerocket을 production Kubernetes cluster에 적용한 과정을 공유합니다.
last_modified_at: 2021-03-08
---

안녕하세요, DevOps 팀의 Sammie입니다. 이번 글에서는 Bottlerocket[[1]](https://aws.amazon.com/bottlerocket/)이라는 Linux 기반 OS를 소개하고, Hyperconnect의 production Kubernetes cluster의 node를 Amazon Linux 2에서 Bottlerocket으로 migration 하면서 겪은 문제와 해결 방법을 소개하려고 합니다.

다양한 Kubernetes의 기능과 모니터링 및 로그 수집 도구를 사용하고 있어 단순히 EC2 instance의 AMI를 변경하는 작업은 아니었습니다. Bottlerocket의 source code를 직접 수정하고 빌드한 만큼 개발 관련 지식이 없으면 이해하기 어려울 수 있습니다. 또한, Kubernetes component 관련 옵션을 몇 가지 수정했는데, 옵션 자체에 대한 상세한 설명은 분량 관계상 생략하였으므로 양해 부탁드립니다.

# What is Bottlerocket?
Bottlerocket은 VM이나, bare metal에서 container를 실행하기 위한 용도로 AWS가 제작한 OS입니다. Ubuntu나 Amazon Linux 같은 일반적인 Linux 배포판은 OS 업데이트 시 package manager를 사용해 package를 하나씩 업데이트를 합니다. 하지만, Bottlerocket은 한 번의 과정으로 OS를 업데이트할 수 있습니다. 또한, container를 실행하기 위해 만들어진 OS인 만큼, container 실행에 필요한 containerd[[2]](https://containerd.io/)나 Kubernetes node 관리에 필요한 kubelet[[3]](https://kubernetes.io/docs/concepts/overview/components/#kubelet), systemd[[4]](https://systemd.io/) 같은 핵심적인 binary나 library만 설치되어 있으며, 이 외에는 아무것도 설치되어 있지 않습니다.

따라서, Kubernetes node의 OS로 Bottlerocket을 사용하면 크게 2가지의 장점이 있습니다.

### 1 - 간단한 OS 업데이트
OS 업데이트와 롤백이 간단해지고, package간의 dependency 충돌이나 예상하지 못한 side-effect로 container 환경이 간섭받는 문제를 줄일 수 있습니다.
Hyperconnect에서는 Kubernetes cluster의 node group을 auto scaling group (ASG)으로 관리하고, lifecycle hook을 사용하여 node가 terminate 되기 전 Pod을 drain 하도록 만들었습니다. ASG는 Terraform[[5]](https://www.terraform.io/)을 사용하여 관리하므로, Kubernetes node의 OS 업데이트는 Terraform에서 ASG의 AMI 버전을 변경하기만 하면 자동으로 수행됩니다. (이 내용은 별도의 글로 소개할 예정입니다. 다음 글을 기다려주세요!)

따라서, Bottlerocket의 첫 번째 장점인 "OS 업데이트가 간편해진다"는 크게 매력적이지 않았습니다.

### 2 - 향상된 보안
보안은 항상 중요합니다. 특히 Kubernetes처럼 보안 전문가가 아닌 개발자가, 알 수 없는 container image를 마음껏 사용할 수 있는 platform에서는 더더욱 중요합니다. Hyperconnect에서는 container image를 제작할 때 지켜야 할 규칙과, container image scanning 등 다양한 도구를 사용하고 있습니다.
하지만, OS 자체의 보안은 보안 전문가가 아닌 DevOps 입장에서 다루기 어려웠고, 실제로 사용하는지 여부가 확실하지 않은 package 하나의 보안 취약점이 발생할 때마다 모든 Kubernetes node를 rolling update 하는 것은 현실적으로 힘들었기 때문에 잘 관리되지 않고 있었습니다.

Bottlerocket은 SELinux를 사용하고, SSH나 shell이 설치되어있지 않고, rootfs가 read-only로 mount 되어 있는 등 취약점을 찾아 공격하기 매우 어렵게[[6]](https://github.com/bottlerocket-os/bottlerocket/blob/develop/SECURITY_FEATURES.md) 구성되었습니다.

Bottlerocket의 두 번째 장점인 "향상된 보안"만으로도 Bottlerocket으로 migration 하기 충분한 이유가 된다고 생각했고, 작업을 시작했습니다.

# Bottlerocket Node 등록하기
### User Data
Bottlerocket은 user data를 사용하여 instance가 시작할 때 설정을 전달[[7]](https://github.com/bottlerocket-os/bottlerocket#using-user-data)할 수 있습니다. Amazon Linux나 Ubuntu 같은 일반적인 OS는 shell script를 전달하여 instance가 시작할 때 임의의 명령을 실행할 수 있지만, Bottlerocket은 보안을 위해 이를 허용하지 않습니다. 대신 미리 정의된 설정 구조가 있고, 이 구조를 지켜 toml 형식의 설정을 전달합니다. 기존 EC2 instance에서는 `/etc/eks/bootstrap.sh` [[8]](https://github.com/awslabs/amazon-eks-ami/blob/master/files/bootstrap.sh)을 실행하는 shell script를 user data로 사용하고 있어 변경이 필요합니다.

### EBS
Bottlerocket은 2개의 EBS를 사용합니다. EBS 하나는 rootfs로 사용됩니다. 이 volume은 read-only로 mount 되며, userspace에서 수정할 수 없습니다. 나머지 다른 EBS는 container 이미지를 저장하고, container에서 생성한 임시 파일을 저장하는 데 사용됩니다.

아래 shell output은 Bottlerocket host OS에서 몇 가지 명령을 실행한 결과입니다. `nvme0n1`은 OS의 이미지를 담고 있으며, `/`의 mount option에는 `ro` (readonly)가 포함된 것을 확인할 수 있습니다. 반면, `nvme1n1`은 runtime data를 저장하도록 `/local` directory에 `rw` (read-write)로 mount 된 것을 알 수 있습니다. 
```shell
bash-5.0# mount
/dev/dm-0 on / type ext4 (ro,relatime,seclabel)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
tmpfs on /etc type tmpfs (rw,nosuid,nodev,noexec,noatime,context=system_u:object_r:etc_t:s0,mode=755)
/dev/nvme1n1p1 on /local type ext4 (rw,nosuid,nodev,noatime,fscontext=system_u:object_r:local_t:s0,defcontext=system_u:object_r:local_t:s0,rootcontext=system_u:object_r:local_t:s0,seclabel)
# 일부 생략
bash-5.0# lsblk
NAME         MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
loop0          7:0    0  252K  1 loop /x86_64-bottlerocket-linux-gnu/sys-root/usr/share/licenses
loop1          7:1    0 10.9M  1 loop /local/var/lib/kernel-devel/lower
nvme1n1      259:0    0   50G  0 disk
`-nvme1n1p1  259:2    0   50G  0 part /local
nvme0n1      259:1    0    8G  0 disk
|-nvme0n1p1  259:3    0    4M  0 part
# 일부 생략
```

기존 EC2 instance는 EBS 하나만 생성하도록 구성되어 있었고, 이를 EBS 2개를 사용하도록 변경했습니다.

### Node Group 분리
테스트 시 `nodeSelector`를 사용하여 강제로 Pod을 Bottlerocket node에 배정하고, DevOps가 Bottlerocket node를 쉽게 식별할 수 있도록 `os=bottlerocket` 같은 label을 추가했습니다. 또한, 테스트를 하기 위해 지정된 Pod이 아닌 다른 Pod이 Bottlerocket node에 할당되는 것을 막기 위해 `os=bottlerocket:NoSchedule` 같은 taint를 붙였습니다.

## Result
최종적으로 사용한 toml 설정은 다음과 같습니다.
```toml
[settings.host-containers.admin]
enabled = true

[settings.kubernetes]
api-server = "https://eks..."
cluster-certificate = "BASE64_ENCODED_CERTIFICATE_AAAAA"
cluster-name = "hyperconnect-cluster"

[settings.kubernetes.node-labels]
os = "bottlerocket"

[settings.kubernetes.node-taints]
os = "bottlerocket:NoSchedule"
```
그리고 `kubectl get nodes` 명령을 통해 확인한 결과 node가 성공적으로 등록된 것을 확인했습니다.

# Bottlerocket - The Hard Way
Node가 성공적으로 등록된 것을 확인했지만, Bottlerocket을 도입하기 위해서는 아직 할 일이 많이 남았습니다. `kubectl get pods -A | grep <node>` 명령을 통해 본 Bottlerocket에 할당된 Pod의 상태는 Running이 아니었고, Amazon Linux 기반의 node에서 사용하던 설정을 추가해야 했습니다. 여기서 문제가 발생했습니다. 반드시 필요한 설정을 Bottlerocket 도입 당시 버전 (v1.0.4)에서 지원하지 않았습니다. Bottlerocket은 shell이 없으므로 임의의 명령을 실행할 수도 없었고, `/etc` directory 자체가 `tmpfs`이므로 직접 설정을 수정하는 것이 효과가 없어 직접 Bottlerocket에 기능을 추가해야 했습니다.

다행히 저는 개발자이고, Bottlerocket의 모든 source code는 [https://github.com/bottlerocket-os/bottlerocket](https://github.com/bottlerocket-os/bottlerocket)에 공개되어있습니다. 또한, build 방법에 대한 자세한 설명이 있어 local에서 source code를 clone 하고, rust를 설치하고, cargo 명령을 실행하는 등 일단 따라 해 볼 수 있었습니다.

처음에는 개인 노트북에서 build를 시도하였으나, Linux Kernel 등 많은 코드를 compile 하면서 CPU를 정말 많이 사용했습니다. `c5.2xlarge` (8vCPU) 정도의 EC2 instance를 하나 만들고, 그 위에서 개발환경을 구축했습니다. 몇 차례의 시도 끝에 정말 간단한 `build.sh` script와 `Infra.toml` 설정을 만들었습니다.
```bash
#!/bin/bash

if [[ "$1" == "" ]]; then
  echo "Usage: ./build.sh <version name>"
  exit 1
fi

ENV="-e BUILDSYS_VARIANT=aws-k8s-1.18 -e BUILDSYS_VERSION_BUILD=$1"
cargo make $ENV
cargo make ami $ENV
cargo make grant-ami $ENV -e GRANT_TO_USERS=<aws-account-1>,<aws-account-2>,...
```
이 `build.sh` 파일은 현재의 source를 Kubernetes 1.18용으로 build 하여 OS image를 만들고, 이 image를 사용하여 AMI를 만들어서, 생성된 AMI를 다른 계정이 사용할 수 있도록 권한을 주는 script입니다.

```toml
[aws]
regions = ["ap-northeast-1", "us-west-1", "us-east-1", "other-region-codes"]
```
이 `Infra.toml` 파일은 Bottlerocket AMI build 과정에서 자동으로 참조하는 파일입니다. `aws.regions`을 설정하여 AMI를 복제할 region을 정할 수 있습니다.

이제 build 환경이 구축되었으니, 필요한 기능을 추가하기 위한 본격적인 개발을 시작했습니다. 다음 3가지의 기능을 추가했는데, 한 단락씩 나누어 설명하겠습니다.
1. CRI Registry Credentials
2. Kubelet Settings 
3. ec2-instance-connect

## Feature 1 - CRI Registry Credentials
Hyperconnect에서는 private container registry로 [Kubernetes에 Microservice 배포하기](https://hyperconnect.github.io/2020/06/13/microsrv-deploy-1.html) 시리즈에서 잠시 소개했던 Harbor[[9]](https://goharbor.io/)를 사용합니다. Private container registry에서 container image를 사용하기 위해서는 `imagePullSecrets` 설정[[10]](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)이 필요하지만, node에 접근 권한이 있다면 단순히 아래 shell script를 실행하여 `/root/.docker/config.json`에 계정 정보를 입력하면, `imagePullSecrets` 없이 image를 다운로드할 수 있습니다.
```shell
mkdir /root/.docker
DOCKER_CONFIG=$(cat <<EOT
{
   "auths":{
      "harbor.hyperconnect.com":{
         "username":"account",
         "password":"1234567890",
         "email":"account@hyperconnect.com",
         "auth":"..."
      }
   }
}
EOT)
echo $DOCKER_CONFIG > /root/.docker/config.json
```
`config.json`에서 사용하는 계정을 cluster별로 분리하고, DevOps 외의 인원에게 host의 SSH 접근 권한을 부여하지 않으며, Pod이 `/tmp` directory 이외의 다른 host volume을 mount 하지 못하게 차단한다면 안전하게 credential을 지키면서도 편하게 private container registry를 사용할 수 있습니다.

안타깝게도 Bottlerocket은 Docker 없이 containerd를 직접 사용하므로 이 방법을 사용할 수 없습니다. 다만, containerd는 CRI plugin을 사용하여 registry auth 정보를 저장하는 것을 지원[[11]](https://github.com/containerd/containerd/blob/master/docs/cri/registry.md#configure-registry-credentials)하므로 이 방법을 사용해서 동일한 기능을 구현할 수 있었습니다. 2단계에 걸쳐 설명하겠습니다.

### Model 추가
Bottlerocket은 사전에 정의된 내용만 `toml` 설정으로 사용할 수 있습니다. 이 "사전에 정의된" model은 `mod.rs`에 있습니다. Kubernetes 1.18용 이미지가 필요하므로, `sources/models/src/aws-k8s-1.18/mod.rs` 파일을 수정하면 됩니다. 나중을 위해 여러 개의 credential이 필요할 수 있으므로 `Vec` 타입으로 `RegistryAuth` 구조체를 받도록 만들었습니다. 
```diff
 #[model(rename = "settings", impl_default = true)]
 struct Settings {
     motd: String,
     kubernetes: KubernetesSettings,
+    cri_registry_auths: Vec<RegistryAuth>,
     updates: UpdatesSettings,
```

`RegistryAuth` 구조체는 추후 다른 타입의 이미지에서도 사용할 수 있도록 `sources/models/src/lib.rs`에 추가했습니다. 
```rust
struct RegistryAuth {
    name: SingleLineString,
    username: SingleLineString,
    password: SingleLineString,
    auth: SingleLineString,
}
```

다음으로, 이 설정이 적용되는 서비스를 `sources/models/src/aws-k8s-1.18/override-defaults.toml` 파일에 명시했습니다. 기본 값을 정의하지 않으면 빈 `Vec`로 초기화됩니다.
```toml
[metadata.settings.cri-registry-auths]
affected-services = ["kubernetes", "containerd"]
```

### Containerd Config 수정
이제 Containerd의 config template를 수정하여 주입된 설정을 사용하도록 만들어야 합니다. Bottlerocket에서는 template language로 Handlebars[[12]](https://docs.rs/handlebars/3.5.2/handlebars/)를 사용합니다.  따라서, `packages/containerd/containerd-config-toml_aws-k8s` 파일에 다음 내용을 추가했습니다. 
```text
{% raw %}
{{#if settings.cri-registry-auths}}
{{#each settings.cri-registry-auths}}
[plugins."io.containerd.grpc.v1.cri".registry.auths."{{this.name}}"]
username = "{{this.username}}"
password = "{{this.password}}"
auth = "{{this.auth}}"
{{/each}}
{{/if}}
{% endraw %}
```

### Result
몇 시간의 노력으로 `ImagePullErr` 상태의 Pod이 없어졌습니다! 설정을 새로 추가하는 방법을 알았으므로, 이제 비슷한 기능을 쉽게 개발할 수 있게 되었습니다.

## Feature 2 - Kubelet Settings
kubelet에는 많은 설정이 있습니다. Amazon Linux를 사용할 때에는 `/etc/eks/bootstrap.sh --kubelet-extra-args "${kubelet_option}"`을 실행하여 command line argument로 설정을 전달했으나, config 파일을 수정하여 설정[[13]](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/) 할 수도 있습니다. Kubernetes 공식 문서에서도 config 파일로 설정하는 것이 권장되고, Handlebars template을 사용할 수 있다는 장점이 있어 이 방식으로 kubelet을 설정했습니다.

Containerd에 registry auth를 추가한 것처럼, `sources/models/src/lib.rs`에 정의된 `KubernetesSettings`에 필요한 설정을 추가하고, `packages/kubernetes-1.18/kubelet-config`의 kubelet config 파일을 수정했습니다. Hyperconnect에서는 다음 설정을 추가해서 사용하고 있습니다.
- `featureGates`: alpha나 beta 상태의 추가 기능을 사용하거나, 사용하지 않습니다.
- `containerLogMaxSize`: container log가 저장되는 최대 크기를 지정합니다. 이 크기가 넘어가면 rotate 됩니다.
- `containerLogMaxFiles`: container log가 저장되는 최대 파일 개수를 지정합니다.
- `kubeReserved`: kubelet 등 Kubernetes component가 사용할 리소스를 지정합니다.
- `systemReserved`: Kubernetes component가 아닌 다른 system 구성 component가 사용할 리소스를 지정합니다.
- `evictionHard`: Pod eviction을 trigger 할 조건을 지정합니다.
- `topologyManagerPolicy`: NUMA node 대응을 위해 추가했습니다. 자세한 설명은 생략합니다.
- `cpuManagerPolicy`: NUMA node 대응을 위해 추가했습니다. 자세한 설명은 생략합니다.

더 자세한 설명은 kubelet CLI option[[14]](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)이나 kubelet source code를 참고하시기 바랍니다.

### Dynamic - Pluto
kubelet config는 대부분 user data를 통해 넣은 정적인 값으로 구성되어있습니다. 하지만, `maxPods` 설정과 같이 동적으로 계산이 필요한 값도 존재합니다. AWS VPC CNI[[15]](https://github.com/aws/amazon-vpc-cni-k8s)를 사용하는 경우, EC2 instance에 attach 할 수 있는 ENI 개수에 따라 할당 가능한 IP가 제한됩니다. 따라서, Bottlerocket은 instance가 시작할 때 instance type을 가져와 `maxPods` 설정을 계산합니다. 동적인 설정은 Pluto라는 component를 사용하여 계산하며, `sources/api/pluto/src/main.rs`에서 구현을 찾아볼 수 있습니다.

`kubeReserved` 설정은 [https://github.com/awslabs/amazon-eks-ami/blob/v20210208/files/bootstrap.sh#L370](https://github.com/awslabs/amazon-eks-ami/blob/v20210208/files/bootstrap.sh#L370) 에서 구현되어있듯이 할당 가능한 최대 Pod 개수와 사용 가능한 CPU core의 수에 따라 동적으로 계산됩니다. Bottlerocket 도입 당시 버전인 v1.0.4에는 이 구현이 없었으므로 직접 추가했습니다. 먼저 `sources/api/pluto/src/main.rs` 파일에 다음 내용을 추가했습니다.
```rust
fn get_kube_reserved_cpu(client: &Client, session_token: &str) -> Result<String> {
    let cores = num_cpus::get();
    let mut cpu = 0;
    // some logic - calculate cpu using cores
    Ok(format!("{}m", cpu))
}

fn get_kube_reserved_memory(client: &Client, session_token: &str) -> Result<String> {
    let max_pod = get_max_pods(client, session_token);
    match max_pod {
        Ok(v) => Ok(format!("{}Mi", v.parse::<i32>().unwrap() * 11 + 255)),
        Err(e) => Err(e)
    }
}

fn run() -> Result<()> {
    // code stripped
    let setting = match setting_name.as_ref() {
        "kube-reserved-cpu" => get_kube_reserved_cpu(&client, &imds_session_token),
        "kube-reserved-memory" => get_kube_reserved_memory(&client, &imds_session_token).map_err(|_| process::exit(2)),
        // code stripped
```

그리고 `kubeReserved` 설정이 pluto를 사용하여 동적으로 생성되도록 `sources/models/src/aws-k8s-1.18/override-defaults.toml`를 수정했습니다.
```toml
[metadata.settings.kubernetes.kube-reserved]
cpu.setting-generator = "pluto kube-reserved-cpu"
memory.setting-generator = "pluto kube-reserved-memory"
affected-services = ["kubernetes"]
```
### Result
이미지를 빌드하고 Kubernetes node를 띄운 뒤 `/etc/kubernetes/kubelet/config` 파일을 열어보았고, 설정이 잘 적용된 것을 확인했습니다! 이렇게 동적인 설정도 추가하는 방법을 배웠습니다. 

## Feature 3 - ec2-instance-connect
Bottlerocket은 debug를 위한 admin-container라는 구성 요소가 있으며, 이 구성 요소를 활성화한 경우 host의 22번 port를 admin-container의 SSH port로 forwarding 하여 host에 SSH 연결을 가능하게 합니다. 또한, 이 admin-container는 host의 filesystem을 mount 하고 있으며, host와 일부 namespace를 공유하고 있으므로 다양한 debugging을 할 수 있습니다.

Production 환경에서는 보안 문제로 admin-container를 사용할 일이 없지만, 개발이나 stage 환경에서는 debug를 위해 host에 직접 접근해야 하는 경우가 있습니다. 또한, 기본 admin-container는 용량을 최대한 줄이기 위해 `ps`, `netstat` 등 debugging에 필요한 최소한의 도구도 설치되어있지 않습니다. Hyperconnect에서는 ec2-instance-connect[[16]](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Connect-using-EC2-Instance-Connect.html)를 사용하여 모든 개발자들의 EC2 SSH 접근을 관리하고 있는데, 이 package도 설치되어있지 않습니다. 따라서, 직접 admin-container의 이미지를 변경해서 필요한 package를 설치하고, ec2-instance-connect을 사용할 수 있도록 만들었습니다.

### Build Setup
Bottlerocket 자체를 build 하는 것보다 상당히 간단합니다. [https://github.com/bottlerocket-os/bottlerocket-admin-container](https://github.com/bottlerocket-os/bottlerocket-admin-container)를 clone 한 뒤, `Dockerfile`을 build 하면 됩니다.
```shell
#!/bin/bash

make build

ACCOUNT=123456789012
VERSION=$(cat VERSION)
REGIONS=( "ap-northeast-1" "us-west-1" "us-east-1" ... )
for REGION in "${REGIONS[@]}"; do
  aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
  AWS_TAG="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/bottlerocket-admin:$VERSION"
  docker tag "bottlerocket-admin:$VERSION" "$AWS_TAG"
  docker push "$AWS_TAG"
done
```
`Dockerfile`을 build 하고, 여러 region에 이미지를 upload 하는 간단한 script를 만들었습니다. Kubernetes에 설치된 Harbor에 장애가 발생한 경우에도 Kubernetes node를 debugging 하는데 문제가 없도록 예외적으로 ECR에 저장했습니다.


### ec2-instance-connect
EC2 instance connect를 사용하기 위해서는 yum을 사용해서 ec2-instance-connect package를 설치하면 됩니다. 하지만, admin-container는 container 환경에서 동작하므로 추가적인 작업이 필요합니다. 먼저 [https://github.com/aws/aws-ec2-instance-connect-config](https://github.com/aws/aws-ec2-instance-connect-config) repo를 보며 package가 어떻게 동작하는지 확인했습니다. 필요한 작업은 다음 4가지였습니다.

1. `eic_harvest_host_keys` 실행 
2. sshd host key 설정
3. `sshd_config` 설정 추가
4. Dependency 설치

#### 1. `eic_harvest_host_keys` 실행
이 script는 sshd host key를 읽어 AWS EC2 Instance Connect Service에 전송합니다. ec2-instance-connect package가 설치되면 다음 service가 설치되며, 이 script를 딱 한 번 실행합니다.
```text
[Unit]
Description=EC2 Instance Connect Host Key Harvesting
Before=sshd.service
After=network.target sshd-keygen.service

[Install]
WantedBy=multi-user.target

[Service]
Type=oneshot
ExecStart=/opt/aws/bin/eic_harvest_hostkeys
```

안타깝게도 container 환경에서는 systemd를 사용할 수 없으므로, admin-container의 진입점인 `start_admin_sshd.sh`에 다음 내용을 추가했습니다.
```bash
if [ ! -f "${ssh_host_key_dir}/harvest" ]; then
    if ! /opt/aws/bin/eic_harvest_hostkeys; then
        echo "Failure to harvest hostkeys" >&2
        exit 1
    fi
    touch "${ssh_host_key_dir}/harvest"
fi
```

#### 2. sshd host key 설정
`eic_harvest_hostkeys` script는 다음 코드를 실행하여 `/etc/ssh` directory의 host key를 읽습니다.
```bash
#Iterates overs /etc/ssh to get the host keys
for file in /etc/ssh/*.pub; do
    /usr/bin/test -r "${file}" || continue
    key=$(/usr/bin/awk '{$1=$1};1' < "${file}")
    keys="${keys:+${keys},}\"${key}\""
done
```

하지만, admin-container는 재시작되어도 동일한 host key를 사용하도록 `/.bottlerocket/host-containers/admin/etc/ssh`에 host key를 생성합니다. 따라서, host key를 생성하거나 존재하는지 검사하는 과정에서 `/etc/ssh`에 symbolic link를 생성하도록 `start_admin_sshd.sh`에 다음 내용을 추가했습니다.
```bash
sshd_config_dir="/etc/ssh"
for key in rsa ecdsa ed25519; do
    # some bash script
    ln -sf "${ssh_host_key_dir}/ssh_host_${key}_key.pub" "${sshd_config_dir}/ssh_host_${key}_key.pub"
done
```

#### 3. `sshd_config` 설정 추가
ec2-instance-connect가 설치되면 `sshd_config`에 다음 내용이 추가됩니다.
```bash
AuthorizedKeysCommand /opt/aws/bin/eic_run_authorized_keys %u %f
AuthorizedKeysCommandUser ec2-instance-connect
```
SSH 키를 검증하는 과정에서 `eic_run_authorized_keys` script가 호출되며, 사용자가 전송한 키가 ec2-instance-connect를 통해 등록된 키인지 확인합니다. 이 설정도 동일하게 `sshd_config`에 추가했습니다.

#### 4. Dependency 설치
`eic_parse_authorized_keys`에는 인증서 검사 로직이 포함되어있는데, 이 과정에서 `openssl` cli가 필요합니다. `Dockerfile`을 수정해서 `openssl`이 설치되도록 변경했습니다.

### Result
`settings.host-containers.admin.source`에 직접 build 한 admin-container의 주소를 넣고 Kubernetes node를 생성했습니다. EC2 instance connect를 사용하여 연결을 할 수 있었으며, `ps`나 `netstat` 등 필요한 기본 debugging 도구도 잘 설치된 것을 확인했습니다. 아래 console 출력 화면에서 `hp ssh` 도구는 ec2-instance-connect를 호출하고, ssh를 실행하는 in-house 도구입니다.
```text
% hp ssh kube-<redacted>
you are connecting to i-<redacted> using ec2 instance connect.
> exec ssh -oStrictHostKeyChecking=no   sammie-hpcnt@10.<redacted>
Warning: Permanently added '10.<redacted>' (ECDSA) to the list of known hosts.
Welcome to Bottlerocket's admin container!

[sammie-hpcnt@ip-10-<redacted> ~]$ ps
    PID TTY          TIME CMD
 563058 pts/0    00:00:00 bash
 563546 pts/0    00:00:00 ps
[sammie-hpcnt@ip-10-<redacted>~]$ netstat
Active Internet connections (w/o servers)
```

추가 작업으로, Bottlerocket의 `sources/models/defaults.toml`을 변경하여 새로 build 한 이미지를 기본 admin-container source로 설정했습니다.
```toml
[metadata.settings.host-containers.admin.source]
setting-generator = "schnauzer settings.host-containers.admin.source"
template = "<redacted>.dkr.ecr.{{ settings.aws.region }}.amazonaws.com/bottlerocket-admin:<redacted>"
```

## Logging System 호환 작업
이제 개발 작업은 어느 정도 마무리되었습니다. 하지만, Bottlerocket 자체에 기능을 추가하는 것 외에도 Kubernetes cluster 차원에서 추가하거나 변경해야 할 사항이 있었습니다.

### System Log
[대규모 Cloud 환경에서 Zabbix 사용 Tip](https://hyperconnect.github.io/2018/10/22/monitoring-cloud-with-zabbix.html) 글에서 소개했듯이 Hyperconnect에서는 Zabbix Agent를 모든 EC2 instance에 설치하여 기본 metric을 monitoring 하고 있습니다. Bottlerocket 특성상 host에 직접 Zabbix agent를 설치하는 것이 불가능하므로, Zabbix agent container image[[17]](https://hub.docker.com/r/zabbix/zabbix-agent2)를 사용해서 Bottlerocket node에서만 실행되도록 DaemonSet을 만들었습니다.

Zabbix 수집 항목에는 `/var/log/messages` 파일이 있습니다. 하지만 Bottlerocket은 `/var/log/messages`에 로그를 적재하지 않으므로, `journalctl`로 host의 journal을 읽어 파일로 남겨주는 sidecar도 추가하여 사용했습니다. 물론 `/var/log/messages` 파일을 rotate 시켜주는 logrotate sidecar도 추가하여 사용하고 있습니다.

### Docker to Containerd Log Format
기존에 Docker를 사용할 때는 `/etc/docker/daemon.json`에 다음 내용을 추가하여 container의 로그가 모두 json 형식으로 출력되도록 했습니다.
```json
{
  "log-driver": "json-file"
}
```
그 결과, Fluentbit [[18]](https://fluentbit.io/) DaemonSet에서 다음 parser 설정을 사용하여 parsing 할 수 있었습니다.
```text
[PARSER]
    Name        docker
    Format      json
    Time_Key    time
    Time_Format %Y-%m-%dT%H:%M:%S.%L
```
하지만, containerd의 로그 출력은 json이 아닌 다른 형태이므로 parser 설정을 다음과 같이 변경했습니다.
```text
[PARSER]
    Name        cri
    Format      regex
    Regex       ^(?<time>[^ ]+) (?<stream>stdout|stderr) (?<logtag>[^ ]*) (?<log>.*)$
    Time_Key    time
    Time_Format %Y-%m-%dT%H:%M:%S.%L%z
```

Parser 설정이 다른 Fluentbit DaemonSet 2개를 배포하였습니다. Amazon Linux에서 사용하는 DaemonSet은 `affinity.nodeAffinity.requiredDuringSchedulingIgnoredDuringExecution`을 사용하여 Bottlerocket label이 없는 node에서만 실행되도록 강제하였고, Bottlerocket에서 사용하는 DaemonSet은 `nodeSelector`를 사용해서 Bottlerocket node에서만 실행되도록 강제했습니다. 


# Wrap Up
Bottlerocket을 Kubernetes cluster에서 사용하기 위해 Bottlerocket과 admin-container의 코드를 수정하고, 빌드하여 배포했습니다. 이 과정에서 직접 추가한 기능은 AWS에서 배포한 Bottlerocket에 존재하지 않는 기능입니다.
- 별도의 `imagePullSecrets` 없이 private registry에서 container image를 가져올 수 있도록 containerd 설정에 cri registry auth를 추가했습니다.
- 기존에 사용하고 있던 `systemReserved`, `topologyManagerPolicy` 등 kubelet 설정 몇 개를 Bottlerocket에 추가했습니다.
- Amazon Linux 기반 EKS AMI에서 동적으로 설정하던 `kubeReserved` 설정을 Bottlerocket에 pluto를 사용하여 구현했습니다.
- 추가적인 설치 없이 `ps`나 `netstat` 같은 cli 도구를 사용할 수 있고, ec2-instance-connect를 사용하여 ssh 접근을 할 수 있도록 admin-container를 수정했습니다.

결과적으로, Hyperconnect의 production 및 stage Kubernetes cluster의 대부분의 node를 Bottlerocket으로 교체할 수 있었습니다. 이 작업을 통해 더 안전한 OS를 기반으로 서비스를 더 안전하게 운영할 수 있게 되었고, Bottlerocket이 지원하지 않는 containerd나 kubelet 옵션을 아무 두려움 없이 사용할 수 있게 되었습니다.

아직 source code patch 전체를 공개하거나 upstream에 pull request를 보내지는 못했지만, Bottlerocket 도입을 고민하고 계신 분들께 많은 도움이 되었으면 좋겠습니다.

긴 글 읽어주셔서 감사합니다 :)

<br>
<br>
언제나 글 마지막은 채용공고입니다. 이렇게 재미있는(?) 일을 같이할 DevOps와 보안 전문가, Backend 개발자분들의 많은 지원 부탁드립니다. [채용공고 바로가기](https://career.hyperconnect.com/jobs/)

# References
[1] [https://aws.amazon.com/bottlerocket/](https://aws.amazon.com/bottlerocket/)

[2] [https://containerd.io/](https://containerd.io/)

[3] [https://kubernetes.io/docs/concepts/overview/components/#kubelet](https://kubernetes.io/docs/concepts/overview/components/#kubelet)

[4] [https://systemd.io/](https://systemd.io/)

[5] [https://www.terraform.io/](https://www.terraform.io/)

[6] [https://github.com/bottlerocket-os/bottlerocket/blob/develop/SECURITY_FEATURES.md](https://github.com/bottlerocket-os/bottlerocket/blob/develop/SECURITY_FEATURES.md)

[7] [https://github.com/bottlerocket-os/bottlerocket#using-user-data](https://github.com/bottlerocket-os/bottlerocket#using-user-data)

[8] [https://github.com/awslabs/amazon-eks-ami/blob/master/files/bootstrap.sh](https://github.com/awslabs/amazon-eks-ami/blob/master/files/bootstrap.sh)

[9] [https://goharbor.io/](https://goharbor.io/)

[10] [https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)

[11] [https://github.com/containerd/containerd/blob/master/docs/cri/registry.md#configure-registry-credentials](https://github.com/containerd/containerd/blob/master/docs/cri/registry.md#configure-registry-credentials)

[12] [https://docs.rs/handlebars/3.5.2/handlebars/](https://docs.rs/handlebars/3.5.2/handlebars/)

[13] [https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/](https://kubernetes.io/docs/tasks/administer-cluster/kubelet-config-file/)

[14] [https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/](https://kubernetes.io/docs/reference/command-line-tools-reference/kubelet/)

[15] [https://github.com/aws/amazon-vpc-cni-k8s](https://github.com/aws/amazon-vpc-cni-k8s)

[16] [https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Connect-using-EC2-Instance-Connect.html](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Connect-using-EC2-Instance-Connect.html)

[17] [https://hub.docker.com/r/zabbix/zabbix-agent2](https://hub.docker.com/r/zabbix/zabbix-agent2)

[18] [https://fluentbit.io/](https://fluentbit.io/)

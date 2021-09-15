---
layout: post
date: 2021-09-15
title: Shell 없는 Container, Live 환경에서 Debugging해보기!
author: sammie
tags: kubernetes bottlerocket debug kubectl
excerpt: Live Pod을 debugging 하기 위해 사용한 kubectl-debug라는 open-source 도구에 대해 소개하고, 이 도구를 Bottlerocket에서 쓰기 위해 패치한 과정을 공유합니다.
last_modified_at: 2021-09-15
---

안녕하세요, DevOps 팀의 Sammie입니다. 이번 글에서는 필요한 디버그 도구가 없거나, 심지어는 shell이 존재하지 않는 Kubernetes 위의 container를 현재 상태 그대로 디버깅하기 위해 open-source 도구인 kubectl-debug[[1]](https://github.com/aylei/kubectl-debug)를 사용한 경험을 공유합니다. 또한, Hyperconnect에서 운영하는 대부분의 Kubernetes node는 Bottlerocket[[2]](https://aws.amazon.com/bottlerocket/)이라는 Linux 기반 OS를 사용하는데, kubectl-debug를 이 OS 위에서도 정상적으로 실행할 수 있도록 수정한 내용에 대해 소개하려고 합니다.

Bottlerocket에 대한 설명은 분량 관계상 생략했으며, 이전 기술 블로그 글 - [Bottlerocket in Production Kubernetes Cluster](https://hyperconnect.github.io/2021/03/08/bottlerocket-on-kubernetes.html)을 참고하시기 바랍니다. Container 기술이나 golang에 대한 지식이 없으면 이해하기 어려울 수 있어 양해 부탁드립니다.

# Why Live Debugging?
사실 Kubernetes에서 이미 실행되고 있는 container에 접속하여 명령을 실행하는 것은 테스트 목적을 제외하고는 권장하지 않습니다. 특히 그 대상이 production traffic을 받고 있는 workload라면 안정성에 심각한 영향을 미칠 수 있어 더더욱 권장하지 않습니다. 그러나 개발환경과 운영환경을 완벽히 동일하게 맞추기는 어렵고, 때로는 개발환경에서 쉽게 재현할 수 없는 버그가 있습니다. 따라서, 가끔씩 `k exec -it -n <namespace> <pod-name> -c <container-name> -- /bin/bash` 와 같은 명령을 사용해 실행 중인 container에 접속하고, 디버그를 위한 몇 가지 명령을 입력해보고는 합니다. 예를 들어, Hyperconnect에서는 운영 환경에서 JVM의 heap dump나 thread dump를 떠서 가져오거나 curl과 같은 명령어로 network 연결을 확인해보고는 합니다.

그러나, 이 방법에는 몇 가지 문제가 있습니다.
1. 기본적으로 container image에는 경량화를 위해 많은 디버그 도구가 생략되어 있습니다. `nc`나 `ip` 같은 네트워크 도구는 보통 없을 것이고, `curl`이나 `wget` 모두 존재하지 않아 네트워크 연결을 테스트해 볼 수 없는 이미지가 있으며, Alpine[[3]](https://alpinelinux.org/) 기반 이미지의 경우 `bash`가 존재하지 않아 다른 shell을 사용해야 합니다.
2. Container를 root로 실행하는 것은 위험하며, 권장하지 않습니다[[4]](https://kubernetes.io/blog/2018/07/18/11-ways-not-to-get-hacked/#8-run-containers-as-a-non-root-user). 그러나, 시스템 설정이나 데이터를 읽는 도구는 대부분 root 권한을 요구하므로 사용할 수 없습니다. 또한 `yum`이나 `apk` 같은 package manager 역시 root 권한을 사용하므로 디버그에 필요한 패키지를 ad-hoc 하게 설치할 수 없습니다.
3. 아예 어떤 shell이나 기본적인 utility 조차 없는 이미지가 있습니다. Attack surface를 최대한 줄이기 위해 Google은 language runtime을 제외하고 아무것도 존재하지 않는 distroless[[5]](https://github.com/GoogleContainerTools/distroless)를 만들었습니다.

따라서, 현재 실행 중인 Kubernetes container를 debugging하는 일은 대상 container의 이미지에 따라 매우 힘든 일이 될 수 있습니다. 물론 임시로 각종 패키지와 shell이 설치된 디버그용 이미지를 만들어서 배포한 다음 디버깅하면 되겠지만, 시간과 노력을 필요로 하는 귀찮은 작업입니다.

## Container에서 다른 Container의 환경 사용하기
다행히, 새 이미지를 만들 필요가 없이 현재 상태 그대로 디버깅할 수 있는 방법이 있습니다. 이를 설명하기 위해 먼저 Kubernetes와 Linux 환경에서 container가 어떻게 실행되는지 알아야 합니다.

Linux의 container는 process의 group이고, 논리적으로 OS의 resource를 분리하기 위해 namespace[[6]](https://man7.org/linux/man-pages/man7/namespaces.7.html)이라는 기술을 사용합니다. 서로 다른 Kubernetes Pod끼리는 어떠한 namespace도 공유하지 않으므로, 모든 자원이 격리됩니다. 하지만, 같은 Kubernetes Pod 내의 container는 network 같은 일부 namespace를 공유하여 container 간 localhost 주소로 network 통신이 가능합니다. 이를 사용하여 main application에서 들어오고 나가는 모든 traffic을 처리하는 proxy[[7]](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/#example-2-ambassador-containers)를 만들어 사용할 수 있게 됩니다.

따라서, 다음과 같은 전략을 사용하여 실행 중인 Pod의 container를 어떠한 조작도 없이 현재 상태 그대로 디버깅할 수 있습니다.
1. 먼저 debugging 도구가 잔뜩 설치되어 있는 이미지를 만듭니다.
2. 위에서 만든 이미지를 원하는 Pod에 추가하여 root 권한으로 실행합니다.
3. 2에서 추가한 새 container는 Pod 내의 다른 container와 몇몇 namespace를 공유하므로 동일 환경에서 디버깅이 가능합니다!

![pod, container and namespace]({{"/assets/2021-09-15-kubectl-debug-on-bottlerocket/00-container-ns.png"}}){: height="250px" .center-image }

물론 2번째 단계를 실행하는 것은 불가능합니다. Pod 내의 container definition을 포함한 대부분의 spec은 immutable[[8]](https://kubernetes.io/docs/concepts/workloads/pods/#pod-update-and-replacement)하므로 한 번 생성된 이후에는 수정 할 수 없습니다. 

# Ephemeral Containers (KEP #277)
하지만, 이와 같은 "임시" container의 필요성은 예전부터 지속적으로 요구되었고, "Ephemeral Container"[[9]](https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/) 라는 이름으로 KEP #277[[10]](https://github.com/kubernetes/enhancements/issues/277) 에서 논의되고 있고, Kubernetes 1.16 버전을 기준으로 일부 기능이 구현되어 alpha 상태입니다.

이 글을 쓰는 시점에서 ephemeralContainer는 일반 container와 달리, 추가만 가능하고, port나 각종 probe를 가질 수 없으며, resource를 지정할 수 없는 등 일부 기능에 제약이 있습니다. 또한 일반적인 `kubectl edit`으로 추가할 수 없고, 별도의 API를 사용해야 합니다. 위에 참조한 Kubernetes 공식 문서를 보면 `/ephemeralcontainers` API를 사용하여 실행 중인 Pod에 container를 추가하고, `kubectl attach` 명령을 사용해서 shell에 접속하는 방법을 설명하고 있습니다.

kubectl 1.18부터 `kubectl-debug` [[11]](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-running-pod/#ephemeral-container) 라는 command를 사용할 수 있습니다. 이 command는 위의 명령을 wrapping 하여 한 줄의 명령으로 쉽게 debug container를 생성하고 바로 shell에 접속할 수 있도록 합니다. 대상 Pod을 copy 하고, container의 명령을 바꿔주는 옵션도 제공하고 있어 CrashLoopBackOff 상태에 빠진 Pod도 쉽게 디버깅할 수 있도록 합니다.

## Problems?
하지만 문제는 여전히 해결되지 않았습니다. EKS의 정책에 의해 alpha 기능은 제공되지 않으며, 이 글을 쓰는 현재 Kubernetes 1.23에서 ephemeral containr의 beta graduation이 논의[[12]](https://github.com/kubernetes/enhancements/issues/277#issuecomment-824886449)되고 있습니다.

Kubernetes와 EKS의 release cycle을 생각해 볼 때, 이 기능을 사용하려면 적어도 1년은 더 기다려야 합니다. 심지어 live container debugging이 필요해서 작업을 시작한 시점은 1년 전이었고, 그때는 beta graduation 조차 기약이 없는 상황이었어서 계속 기다리기만 할 수 없었습니다.

# Non-official kubectl debug!
없으면 직접 만들면 되지만, 다행히도 이 세상에는 좋은 open-source 도구가 많습니다. 앞서 설명한 것과 거의 동일한 원리로 동작하는 non-official kubectl debug인 [https://github.com/aylei/kubectl-debug](https://github.com/aylei/kubectl-debug)를 찾았고, 테스트 해 본 결과 완벽하게 작동했습니다.

좀 더 자세하게 이 도구의 원리를 설명하자면 다음과 같습니다.
1. 먼저, debug-agent라고 부르는 Pod을 대상 container와 동일한 node에 띄웁니다. debug-agent는 webserver가 내장되어 있어 사용자의 요청을 받습니다.
2. kubectl-debug가 debug-agent에게 target container의 정보를 보냅니다.
3. 그러면 debug-agent는 kubelet처럼 target container와 동일한 namespace를 가지는 debugging container를 생성합니다. debug-agent Pod은 node의 Docker socket을 mount 하고 있으므로 직접 container를 조작할 수 있습니다.
4. 이제 debug-agent는 debugging container와의 ssh 연결을 proxying 합니다.

![kubectl-debug]({{"/assets/2021-09-15-kubectl-debug-on-bottlerocket/01-kubectl-debug.png"}}){: height="350px" .center-image }

다만, ephemeral container를 사용하는 native kubectl-debug는 kubelet에서 직접 target container와 동일한 namespace를 가지는 debugging container를 생성하는 반면, 이 도구는 별도의 Pod을 띄워 debugging container를 생성한다는 것이 차이점입니다.

## Customize
이 도구를 production cluster에서 사용하는 것은 매우 조심해야 합니다. Node의 Docker socket을 mount 하므로 다른 container에 무제한으로 접근할 수 있으며, namespace 관련 operation을 수행하기 위해 반드시 root 권한으로 실행되어야 합니다. 또한 이 도구는 사용자 인증이 없으므로 Node의 port가 외부로 expose 되거나, Kubernetes namespace 격리를 넘어 권한이 없는 타 namespace의 Pod에 접근하는 문제가 발생할 수 있습니다.

Hyperconnect에서는 이 도구를 수정하고, debug-agent image를 직접 빌드했습니다.
- debug-agent의 webserver가 NodePort로 expose 되지 않도록 설정했습니다.
- OPA Gatekeeper[[13]](https://github.com/open-policy-agent/gatekeeper)을 사용해서 debug-agent를 포함한 일부 container image만 Docker socket을 mount 할 수 있도록 제한했습니다.
- debug-agent Pod의 command나 argument를 변경할 수 없도록 설정했습니다.

# With Bottlerocket
Bottlerocket의 도입은 kubectl-debug를 처참하게 파괴했습니다. Docker socket을 mount 할 수 없다는 메시지와 함께 debug-agent container가 시작조차 되지 않았습니다. Bottlerocket은 Docker 대신 containerd[[14]](https://containerd.io/)를 사용하기 때문에 당연했습니다. 어떻게 containerd도 지원하도록 만들 수 있을까 고민하며 kubectl-debug 코드를 보던 중, 이미 containerd를 지원[[15]](https://github.com/aylei/kubectl-debug/pull/99)하고 있다는 사실을 발견했습니다.

이제 kubectl-debug를 디버그 할 차례입니다. 몇 시간의 초과근무 끝에 Bottlerocket에서 작동하는 kubectl-debug 패치를 완성했습니다. 패치 과정 중 발생한 4가지 큰 이슈에 대해서 설명해보겠습니다. 이 글을 쓰는 시점에서 최신 버전인 [`24842b00e65449fb35bb33900f5c32d05bbac7a9`](https://github.com/aylei/kubectl-debug/tree/24842b00e65449fb35bb33900f5c32d05bbac7a9)를 기준으로 작성했습니다.

## 1. Containerd Socket Mount하기
kubectl-debug에는 다음과 같이 ([`pkg/agent/config.go`](https://github.com/aylei/kubectl-debug/blob/24842b00e65449fb35bb33900f5c32d05bbac7a9/pkg/agent/config.go)) containerd의 socket 주소가 hard-coding 되어 있습니다.
```go
var (
	DefaultConfig = Config{	
		DockerEndpoint:        "unix:///var/run/docker.sock",
		ContainerdEndpoint:    "/run/containerd/containerd.sock",
```
하지만, Bottlerocket의 containerd endpoint는 `/run/dockershim.sock`이므로 변경했습니다.

그리고, kubectl-debug 명령을 통해 debug-agent Pod을 생성하는 [`pkg/plugin/cmd.go:955`](https://github.com/aylei/kubectl-debug/blob/24842b00e65449fb35bb33900f5c32d05bbac7a9/pkg/plugin/cmd.go#L955) 부분을 변경해줘야 합니다. Amazon Linux 기반의 Docker를 사용하는 node에서도 정상적으로 작동해야 하므로 상호 호환이 되도록 작성해야 했습니다. 다행히 Hyperconnect의 node convention에 따라 Bottlerocket node에는 `node.hpcnt.com/os=bottlerocket`이라는 label이 붙어 있으므로, 대상 Pod이 떠 있는 node의 정보를 읽어 Bottlerocket node인지 Amazon Linux node인지 알 수 있었습니다.

Bottlerocket의 경우 다음 4개의 파일 또는 directory를 가져와야 합니다.
- `/run/dockershim.sock`: containerd API를 사용할 수 있는 socket 파일입니다.
- `/var/lib/containerd`: container에 필요한 영구적인 데이터를 보관하는 곳입니다. Container image 등을 저장합니다.
- `/run/containerd`: containerd가 임시 데이터를 저장하는 곳입니다. socket이나 pid 파일 등이 저장됩니다.
- `/etc/containerd/config.toml`: debugging container의 image를 private registry로부터 가져오기 위한 credential이 저장된 파일입니다. 다음 주제에서 자세히 설명합니다.

이 경로는 전부 Bottlerocket 소스 코드나 `/etc/containerd/config.toml` 에서 확인할 수 있습니다.
```toml
root = "/var/lib/containerd"
state = "/run/containerd"
disabled_plugins = [
    "io.containerd.internal.v1.opt",
    "io.containerd.snapshotter.v1.aufs",
    "io.containerd.snapshotter.v1.devmapper",
    "io.containerd.snapshotter.v1.native",
    "io.containerd.snapshotter.v1.zfs",
]

[grpc]
address = "/run/dockershim.sock"
```
처음에는 `/run/dockershim.sock` 만 mount 했으나, 이렇게 하면 debugging container를 실행할 때 존재하지 않는 `/tmp/containerd-mount` directory를 찾을 수 없다는 이상한 에러가 나며 container가 실행되지 않습니다.

필요한 모든 directory를 mount하니 드디어 debug-agent Pod이 뜨고, debug-agent의 코드가 실행되었습니다. 하지만, debugging container를 생성하는데 실패했다는 메시지를 보게 되었습니다.

## 2. Registry Secret 불러오기
Hyperconnect에서는 Harbor로 구축된 사내 Docker registry에 접근할 때 `imagePullSecret`을 사용할 필요가 없도록 `/root/.docker/config.json`에 credentials를 넣어 사용하고 있습니다. Bottlerocket에서도 마찬가지로 `/etc/containerd/config.toml` 파일에 `[plugins."io.containerd.grpc.v1.cri".registry.auths."registry-name"]` 설정을 주입하여 사용하고 있습니다.

debug-agent가 debugging container의 image를 Harbor로부터 잘 가져올 수 있도록 약간의 코드 작업을 해주었습니다. 먼저, 해당 설정 파일을 읽는 코드를 추가했습니다.
```go
package agent

import (
	"github.com/BurntSushi/toml"
	"io/ioutil"
	"os"
)

func LoadContainerdConfig() (map[string]interface{}, error) {
	configFilePath := "/etc/containerd/config.toml"
	var configFile map[string]interface{}

	file, err := os.Open(configFilePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()
	data, err := ioutil.ReadAll(file)
	if err != nil {
		return nil, err
	}

	if _, err := toml.Decode(string(data), &configFile); err != nil {
		return nil, err
	}
	return configFile, nil
}
```

그다음으로, [`pkg/agent/runtime.go:L530`](https://github.com/aylei/kubectl-debug/blob/24842b00e65449fb35bb33900f5c32d05bbac7a9/pkg/agent/runtime.go#L530)의 `func (c *ContainerdContainerRuntime) PullImage`를 수정했습니다. kubectl-debug에는 imagePullSecret을 전달하는 기본 기능이 있고, 이렇게 전달된 credential은 parsing 되어 username과 password가 `crds`에 차례로 저장됩니다. 이 변수의 길이가 2 미만이라면, credential이 전달되지 않은 것이므로 containerd 설정 파일을 읽어 `crds`를 채우도록 했습니다.
```go
if len(crds) < 2 {
	var config map[string]interface{}
	config, err := LoadContainerdConfig()
	if err != nil {
		return err
	}
	keys := []string{"plugins", "io.containerd.grpc.v1.cri", "registry", "auths", "<registry-name>"}
	for _, key := range keys {
		configNested, ok := config[key]
		if !ok {
			return errors.New(fmt.Sprintf("no such key: %s", key))
		}
		config, ok = configNested.(map[string]interface{})
		if !ok {
			return errors.New(fmt.Sprintf("cannot parse config as dict at key: %s", key))
		}
	}
	username := config["username"].(string)
	password := config["password"].(string)
	crds = []string{username, password}
}
```

이 문제와 앞의 1번 문제를 해결하면 드디어 debugging container가 뜬 것을 볼 수 있습니다. 그런데, shell을 시작하자마자 **파일을 쓸 수 없다는 메시지가 뜹니다.** 분명히 root인데 권한이 부족하다고 나옵니다.

## 3. ReadOnly Root 해결하기
이는 SELinux 문제입니다. Bottlerocket에서는 SELinux가 활성화되어있으므로 container를 실행하거나 rootfs를 mount 할 때 특정 label을 붙입니다. 실제로 Bottlerocket node에서 실행 중인 container에 접속하면 다음과 같이 rootfs가 mount 된 것을 볼 수 있습니다.
```
overlay on /run/containerd/io.containerd.runtime.v2.task/k8s.io/1002a06bb5cb9f1d49dd50ffab4380aa7571f4cbda0b379af37ccdcf75c0875a/rootfs
type overlay (rw,relatime,context=system_u:object_r:local_t:s0,
lowerdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/422/fs:...:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/265/fs,
upperdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/426/fs,
workdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/426/work)
```

하지만, debugging container에서 확인하면 다음과 같이 `context=` 부분이 없습니다.
```
overlay on /run/containerd/io.containerd.runtime.v2.task/kctldbg/6914eded-37e5-4ef8-bd61-2d5cf5cfe212/rootfs
type overlay (rw,relatime,seclabel,
lowerdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/352/fs:...:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/343/fs,
upperdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/427/fs,
workdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/427/work)
```

### Bottlerocket Source 확인
Bottlerocket의 source code를 받아 [`packages/selinux-policy/lxc_contexts`](https://github.com/bottlerocket-os/bottlerocket/blob/v1.2.0/packages/selinux-policy/lxc_contexts) 파일을 확인해보면 다음과 같이 process와 rootfs를 mount 할 때 사용하는 SELinux policy를 확인해볼 수 있고, 위 output의 context인 `system_u:object_r:local_t:s0`와 정확히 일치합니다. 
```
# Runtimes that use the Go SELinux implementation, such as Docker and
# the containerd CRI plugin, will apply the 'process' label to the
# initial process for unprivileged containers, unless the option for
# automatic labeling is disabled.
process = "system_u:system_r:container_t:s0"

# The 'file' label should always be applied to the container's root
# filesystem, regardless of privileged status or automatic labeling.
file = "system_u:object_r:local_t:s0"

# The 'ro_file' label is not currently used by the above runtimes.
ro_file = "system_u:object_r:cache_t:s0"
```

### kubectl-debug 패치
먼저, process에 알맞은 label을 붙이기 위해 다음 코드를 [`pkg/agent/runtime.go`](https://github.com/aylei/kubectl-debug/blob/24842b00e65449fb35bb33900f5c32d05bbac7a9/pkg/agent/runtime.go) 파일의 `func (c *ContainerdContainerRuntime) RunDebugContainer`에 추가했습니다.
```go
spcOpts = append(spcOpts, oci.WithSelinuxLabel("system_u:system_r:container_t:s0"))
```

그리고 mount 하는 모든 volume이 올바른 label을 가지도록 위와 같은 파일에 다음과 같은 helper function을 추가했습니다.
```go
func WithMountLabel(label string) oci.SpecOpts {
	return func(_ context.Context, _ oci.Client, _ *containers.Container, s *oci.Spec) error {
		s.Linux.MountLabel = label
		return nil
	}
}
```

마지막으로 `RunDebugContainer` 함수에 방금 전에 작성한 helper function을 사용하는 코드를 넣었습니다.
```go
spcOpts = append(spcOpts, WithMountLabel("system_u:object_r:local_t:s0"))
```

그리고 몇 시간의 디버깅 지옥이 시작되었습니다. 위 코드는 rootfs를 제외한 모든 volume에 잘 적용되었지만, **rootfs에만 적용되지 않았습니다.** rootfs에 mount option을 지정하려면 [container.go#L246](https://github.com/containerd/containerd/blob/v1.3.3/container.go#L246)의 `m.Options`에 label을 넣어야 하는데, `NewTaskOpts` 인자를 전달하는 방법으로는 해당 부분을 수정할 수 없었던 것이었습니다.

### Bottlerocket 패치 재확인
containerd 코드를 수정해야 하나 생각하던 중, Bottlerocket의 kubelet은 어떻게 container를 정상적으로 띄우는지 궁금해졌습니다. 1시간의 추가적인 노력 끝에 Bottlerocket의 과거 버전에서 [패치](https://github.com/bottlerocket-os/bottlerocket/blob/v1.0.4/packages/containerd/0001-Use-spec-s-mountLabel-when-mounting-the-rootfs.patch)를 발견했습니다.
```patch
@@ -242,7 +243,17 @@ func (c *container) NewTask(ctx context.Context, ioCreate cio.Creator, opts ...N
 		if err != nil {
 			return nil, err
 		}
+		spec, err := c.Spec(ctx)
+		if err != nil {
+			return nil, err
+		}
 		for _, m := range mounts {
+			if spec.Linux != nil && spec.Linux.MountLabel != "" {
+				context := label.FormatMountLabel("", spec.Linux.MountLabel)
+				if context != "" {
+					m.Options = append(m.Options, context)
+				}
+			}
```
패치 내용은 제가 하고 싶었던 패치와 정확하게 일치했습니다. 몇 분 지나지 않아, 최신 Bottlerocket 버전에 패치가 없는 이유는 해당 패치가 containerd upstream에 merge 되었기 때문이라는 것을 알아냈습니다. 곧바로 kubectl-debug가 사용하는 containerd library 버전을 v1.3.3에서 v1.4.3으로 올리고 실행해봤습니다.

shell 초기화 오류 문구가 보이지 않았습니다. `mount`를 입력했을 때도 rootfs에 `context=` 정보가 잘 보였습니다. 신나서 `touch a.txt` 같은 명령어도 입력해 보고, `apk add htop` 같이 패키지를 설치해보기도 했습니다. **잠깐, apk 명령어가 작동하지 않습니다.**

## 4. /etc/resolv.conf 추가하기
침착하게 `curl google.com`을 입력해봤습니다. 작동하지 않았습니다. `curl 1.1.1.1`을 입력했습니다. 작동했습니다. DNS가 잘못 설정된 것이 분명했습니다.

DNS 설정을 확인하기 위해 `cat /etc/resolv.conf`을 입력해봤는데, 파일을 찾을 수 없다는 오류 메시지가 나왔습니다. Docker는 기본적으로 host의 `/etc/resolv.conf`를 넣어 주는데 [[16]](https://docs.docker.com/config/containers/container-networking/#dns-services), containerd는 아무것도 해주지 않기 때문에 이 문제가 발생했습니다.

`/etc/resolv.conf` 파일을 Pod spec과 coredns ClusterIP를 찾아 만들어 넣어줘야 하나? kubelet 코드를 뜯어봐야 하나? 등등 여러 가지 고민을 시작하다가, 문득 debug-agent의 stdout으로 Pod이 mount 하고 있는 모든 volume이 보였다는 기억이 떠올랐습니다. [`pkg/agent/runtime.go:L666`](https://github.com/aylei/kubectl-debug/blob/24842b00e65449fb35bb33900f5c32d05bbac7a9/pkg/agent/runtime.go#L666)에서 대상 container의 모든 mount 정보를 출력하고 있었습니다.

Mount label을 수정할 때처럼 [`pkg/agent/runtime.go`](https://github.com/aylei/kubectl-debug/blob/24842b00e65449fb35bb33900f5c32d05bbac7a9/pkg/agent/runtime.go) 파일의 `RunDebugContainer` 함수에 다음 코드 5줄을 넣어 `/etc/resolv.conf`를 그대로 가져왔습니다.
```go
for _, mount := range trgtInf.MountSpecs {
	if mount.Destination == "/etc/resolv.conf" {
		spcOpts = append(spcOpts, oci.WithMounts([]specs.Mount{mount}))
	}
}
```

## Finally?
```bash
ip-10-x-x-x $ mount
overlay on / type overlay (rw,relatime,context=system_u:object_r:local_t:s0,lowerdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/352/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/351/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/350/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/349/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/348/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/347/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/346/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/345/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/344/fs:/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/343/fs,upperdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/455/fs,workdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/455/work)
proc on /proc type proc (rw,nosuid,nodev,noexec,relatime)
tmpfs on /dev type tmpfs (rw,nosuid,context=system_u:object_r:local_t:s0,size=65536k,mode=755)
devpts on /dev/pts type devpts (rw,nosuid,noexec,relatime,context=system_u:object_r:local_t:s0,gid=5,mode=620,ptmxmode=666)
shm on /dev/shm type tmpfs (rw,nosuid,nodev,noexec,relatime,context=system_u:object_r:local_t:s0,size=65536k)
mqueue on /dev/mqueue type mqueue (rw,nosuid,nodev,noexec,relatime,seclabel)
sysfs on /sys type sysfs (ro,nosuid,nodev,noexec,relatime,seclabel)
tmpfs on /run type tmpfs (rw,nosuid,context=system_u:object_r:local_t:s0,size=65536k,mode=755)
/dev/nvme1n1p1 on /etc/resolv.conf type ext4 (rw,nosuid,nodev,noatime,fscontext=system_u:object_r:local_t:s0,defcontext=system_u:object_r:local_t:s0,rootcontext=system_u:object_r:local_t:s0,seclabel)
devpts on /dev/console type devpts (rw,nosuid,noexec,relatime,context=system_u:object_r:local_t:s0,gid=5,mode=620,ptmxmode=666)

ip-10-x-x-x $ cat /etc/resolv.conf
search istio-system.svc.cluster.local svc.cluster.local cluster.local ap-northeast-1.compute.internal
nameserver 172.20.0.10
options ndots:5

ip-10-x-x-x $ curl http://promxy
<a href="/graph">Found</a>.

ip-10-x-x-x $ apk add htop
fetch https://dl-cdn.alpinelinux.org/alpine/v3.13/main/x86_64/APKINDEX.tar.gz
fetch https://dl-cdn.alpinelinux.org/alpine/v3.13/community/x86_64/APKINDEX.tar.gz
fetch http://nl.alpinelinux.org/alpine/edge/main/x86_64/APKINDEX.tar.gz
fetch http://nl.alpinelinux.org/alpine/edge/testing/x86_64/APKINDEX.tar.gz
fetch http://nl.alpinelinux.org/alpine/edge/community/x86_64/APKINDEX.tar.gz
tou(1/1) Installing htop (3.0.5-r1)
Executing busybox-1.33.0-r5.trigger
OK: 291 MiB in 160 packages
```
이제 DNS resolve도 잘 되고, package도 성공적으로 설치할 수 있습니다!

### Debug Container vs Target Container?
여러 고생 끝에 띄운 debug container가 대상 container와 어떤 차이가 있는지 알아보기 위해, [`lsns`](https://man7.org/linux/man-pages/man8/lsns.8.html) 명령어를 실행시켜봤습니다. 대상 container는 Java process를 실행하여 HTTP API 서버를 띄웁니다. 아래 결과에서 볼 수 있듯이, 대상 container와 mount 및 uts namespace를 제외하고는 모두 같습니다!
```
ip-10-x-x-x # lsns
        NS TYPE   NPROCS   PID USER COMMAND
4026531835 cgroup      3     1 1000 java ...
4026531837 user        4     1 1000 java ...
4026532476 mnt         1     1 1000 java ...
4026532477 pid         4     1 1000 java ...
4026532693 mnt         2  1098 root zsh
4026532694 uts         2  1098 root zsh
4026532988 net         3     1 1000 java ...
4026533053 uts         1     1 1000 java ...
4026533054 ipc         3     1 1000 java ...
```

localhost에 대한 `curl`도 잘 동작하고, `ps`나 `netstat` 결과도 대상 container와 같은 것을 확인할 수 있습니다.
```
ip-10-x-x-x # curl http://localhost:8080/healthCheck
OK

ip-10-x-x-x # ps aux
PID   USER     TIME  COMMAND
    1 1000      9:12 java ...
    7 1000      0:00 [sh]
 1253 1000      0:00 /bin/bash
 1305 root      0:00 zsh
 1376 1000      0:00 /bin/bash
 1396 root      0:00 ps aux

ip-10-x-x-x # netstat -nlp
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 0.0.0.0:9000            0.0.0.0:*               LISTEN      1/java
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN      1/java
```

Process가 바라보는 rootfs는 `/proc/<pid>/root/`를 통해 연결되어 있으므로, 대상 container의 rootfs는 `/proc/1/root/`를 통해 접근할 수 있습니다.
```
ip-10-x-x-x # ls -al /proc/1/root/opt/hpcnt/
total xxxxxx
drwx------    1 1000     1000          4096 Aug 30 11:40 .
drwxr-xr-x    1 root     root          4096 Jun 18 05:58 ..
-rw-------    1 1000     1000           122 Aug 30 11:40 .bash_history
-rw-r--r--    1 1000     1000            18 Jul 15  2020 .bash_logout
-rw-r--r--    1 1000     1000           193 Jul 15  2020 .bash_profile
-rw-r--r--    1 1000     1000           231 Jul 15  2020 .bashrc
-rwxrw-r--    1 root     root             x Aug 30 09:24 service.jar
```

Hyperconnect에서는 Istio[[17]](https://istio.io/)를 사용하고 있습니다. Istio를 사용하면 설정한 Pod에 istio-proxy라는 container가 추가되고, inbound / outbound traffic을 제어하기 위한 iptables 규칙이 생성됩니다. 이 iptables 규칙 역시 debug container에서 정상적으로 확인할 수 있습니다! (일부 내용을 가렸습니다)
```
ip-10-x-x-x # iptables -t nat -L
Chain PREROUTING (policy ACCEPT)
target     prot opt source               destination
ISTIO_INBOUND  tcp  --  anywhere             anywhere

Chain ISTIO_INBOUND (1 references)
target     prot opt source               destination
RETURN     tcp  --  anywhere             anywhere             tcp dpt:15020
ISTIO_IN_REDIRECT  tcp  --  anywhere             anywhere
```


# Wrap Up
Ephemeral containers 없이 비슷한 기능을 사용하기 위해 kubectl-debug라는 open source를 사용하고 있었습니다. Bottlerocket 도입 후 Bottlerocket에서도 kubectl-debug를 정상적으로 사용하기 위해서 다음 코드를 작성했습니다.
- Bottlerocket에서 사용하는 올바른 경로의 containerd socket과 directory를 mount했습니다.
- Node의 registry secret을 불러와서 사용하도록 했습니다.
- ReadOnly root를 해결하기 위해 적절한 SELinux label을 process와 root file system에 추가했습니다.
- DNS resolve를 정상적으로 할 수 있도록 디버그 대상 container에 mount 된 `/etc/resolv.conf`를 똑같이 mount 했습니다.

결과적으로, 기존 Amazon Linux 기반 node에서 사용하고 있었던 kubectl-debug를 Bottlerocket 기반 node에서도 동등하게 사용할 수 있었습니다. 이 작업을 통해 shell이 없거나, 디버깅에 필요한 package가 설치되어 있지 않은 경우에도 쉽게 Pod을 디버깅할 수 있게 되었습니다.

Bottlerocket 도입이나 live container debugging을 고민하고 계신 분들께 많은 도움이 되었으면 좋겠습니다. 그리고 ephemeral container 기능이 빨리 beta로 promotion 되어 이 코드를 사용할 일이 없었으면 좋겠습니다.

긴 글 읽어주셔서 감사합니다 :)

<br>
<br>
언제나 글 마지막은 채용공고입니다. 이렇게 재미있는(?) 일을 같이할 DevOps와 보안 전문가, Backend 개발자분들의 많은 지원 부탁드립니다. [채용공고 바로가기](https://career.hyperconnect.com/jobs/)

# References
[1] [https://github.com/aylei/kubectl-debug](https://github.com/aylei/kubectl-debug)

[2] [https://aws.amazon.com/bottlerocket/](https://aws.amazon.com/bottlerocket/)

[3] [https://alpinelinux.org/](https://alpinelinux.org/)

[4] [https://kubernetes.io/blog/2018/07/18/11-ways-not-to-get-hacked/#8-run-containers-as-a-non-root-user](https://kubernetes.io/blog/2018/07/18/11-ways-not-to-get-hacked/#8-run-containers-as-a-non-root-user)

[5] [https://github.com/GoogleContainerTools/distroless](https://github.com/GoogleContainerTools/distroless)

[6] [https://man7.org/linux/man-pages/man7/namespaces.7.html](https://man7.org/linux/man-pages/man7/namespaces.7.html)

[7] [https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/#example-2-ambassador-containers](https://kubernetes.io/blog/2015/06/the-distributed-system-toolkit-patterns/#example-2-ambassador-containers)

[8] [https://kubernetes.io/docs/concepts/workloads/pods/#pod-update-and-replacement](https://kubernetes.io/docs/concepts/workloads/pods/#pod-update-and-replacement)

[9] [https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/](https://kubernetes.io/docs/concepts/workloads/pods/ephemeral-containers/)

[10] [https://github.com/kubernetes/enhancements/issues/277](https://github.com/kubernetes/enhancements/issues/277)

[11] [https://kubernetes.io/docs/tasks/debug-application-cluster/debug-running-pod/#ephemeral-container](https://kubernetes.io/docs/tasks/debug-application-cluster/debug-running-pod/#ephemeral-container)

[12] [https://github.com/kubernetes/enhancements/issues/277#issuecomment-824886449](https://github.com/kubernetes/enhancements/issues/277#issuecomment-824886449)

[13] [https://github.com/open-policy-agent/gatekeeper](https://github.com/open-policy-agent/gatekeeper)

[14] [https://containerd.io/](https://containerd.io/)

[15] [(https://github.com/aylei/kubectl-debug/pull/99](https://github.com/aylei/kubectl-debug/pull/99)

[16] [https://docs.docker.com/config/containers/container-networking/#dns-services](https://docs.docker.com/config/containers/container-networking/#dns-services)

[17] [https://istio.io/](https://istio.io/)

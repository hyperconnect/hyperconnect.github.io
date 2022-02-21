---
layout: post
date: 2022-02-21
title: ImagePullSecrets 없이 안전하게 Private Registry 사용하기!
author: sammie
tags: kubernetes kubelet bottlerocket
excerpt: ImagePullSecrets 없이 편리하고 안전하게 private registry를 사용 할 수 있도록 Kubelet Credential Provider 기능을 실험해보았습니다.
last_modified_at: 2022-02-21
---

안녕하세요, DevOps팀 Cloud Platform Unit의 Sammie입니다. 이번 글에서는 Kubernetes 환경에서 ImagePullSecrets[[1]](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/) 없이 안전하게 private registry를 사용할 수 있는 방법에 대해 소개해보려고 합니다. 많이 알려진 방법은 Kubernetes node의 `/root/.docker/config.json`이나 containerd의 설정 파일에 credentials를 추가하는 것입니다. 이렇게 하면, 아주 쉽게 ImagePullSecrets 없이 private registry에서 image를 pull 할 수 있습니다. 하지만, 이 방법은 관리의 용이성이나 보안 안전성 측면에서 문제가 있습니다. 그래서 Kubernetes 1.20부터 alpha feature로 추가된 `Kubelet Credential Provider` - [KEP 2133](https://github.com/kubernetes/enhancements/issues/2133)를 소개하려고 합니다.

이전 몇 개의 글에서도 소개해드렸지만, Hyperconnect에서는 Bottlerocket[[2]](https://aws.amazon.com/bottlerocket/)과 AmazonLinux 2 기반의 node를 사용하며, 각각에 대한 설정 방법까지 공유하려고 합니다. Bottlerocket에 대한 설명은 분량 관계상 생략했으며, 이전 기술 블로그 글 - [Bottlerocket in Production Kubernetes Cluster](https://hyperconnect.github.io/2021/03/08/bottlerocket-on-kubernetes.html)을 참고하시기 바랍니다.

# The Quick Way - /root/.docker/config.json
ImagePullSecrets 없이 private repository의 image를 사용하기 위한, 가장 흔하게 알려져 있으며 동시에 가장 편한 방법은 `/root/.docker/config.json`에 credentials를 넣는 방법입니다. Hyperconnect에서도 역시 이 방법을 사용하고 있고, Bottlerocket에 이 기능을 넣기 위해 `containerd` 설정 파일을 변경하도록 OS를 수정하여 사용하고 있습니다. (자세한 내용은 [이 글](https://hyperconnect.github.io/2021/03/08/bottlerocket-on-kubernetes.html)을 참고하시면 됩니다.)

다만, 이 방법은 관리나 보안 모두 문제가 있습니다.
1. Hard-coded 된 credentials를 변경하기 힘듭니다. Node group을 rollout 하거나, Ansible 등으로 일괄적으로 설정을 변경한 다음 container runtime을 재시작해야 합니다.
2. 보안에 취약합니다. 누군가 AMI나 snapshot에 접근할 수 있다면, 새 EC2를 launch 한 다음 `cat /root/.docker/config.json` 명령을 입력해서 credentials를 가져올 수 있습니다. Bottlerocket의 경우에는 AMI 자체에는 credentials 정보가 없지만, userdata를 읽을 수 있는 `ec2:DescribeInstanceAttribute` 권한이 있다면 바로 credentials를 얻을 수 있습니다.

## Hints from ECR?
ECR [[3]](https://aws.amazon.com/ecr/)은 AWS에서 제공하는 container image registry입니다. 당연히 private repository를 구축할 수 있으며, IAM을 사용하여 cross-account 연동까지 지원합니다. ECR에 존재하는 image는 AWS EKS [[4]](https://aws.amazon.com/eks/) cluster에서 imagePullSecrets을 넣거나 node에 특별한 설정을 할 필요 없이 image를 pull 할 수 있습니다. Image pull 과정은 대략 다음과 같습니다.
1. EKS 생성 절차에서 node (EC2)가 사용할 IAM role을 생성합니다.
2. 이 IAM role에 `AmazonEC2ContainerRegistryReadOnly` policy를 attach 합니다. 이 policy를 사용하면 ECR에 접근하기 위한 token을 발급받을 수 있고, ECR을 읽을 수 있습니다.
3. kubelet은 ECR에서 image를 pull 하려고 할 때 IAM role을 사용해서 ... ???... 해서 credentials를 잘 가져옵니다.

3이 어떻게 가능할까요? 놀랍게도 Kubernetes upstream에 ECR의 credentials를 가져오는 코드 [[5]](https://github.com/kubernetes/kubernetes/blob/release-1.20/pkg/credentialprovider/aws/aws_credentials.go)가 포함되어 있습니다. Azure나 GCP가 제공하는, ECR과 유사한 서비스에서 credentials를 가져오는 코드 [[6]](https://github.com/kubernetes/kubernetes/tree/release-1.20/pkg/credentialprovider)도 포함되어 있습니다.

만약 `"Hyperconnect provider"`를 Kubernetes upstream에 추가할 수 있다면 1) kubelet을 통해, 2) AMI나 EC2 instance 설정 어디에도 hard-coded 된 credentials를 남기지 않고 3) 직접 만든 custom 한 logic을 사용해서 4) 원격 서버에서 credentials를 가져올 수 있을 것입니다.


# KEP 2133 - Kubelet Credential Provider
이제 글의 가장 처음에서 소개했던, Kubernetes 1.20부터 alpha feature로 추가된 `Kubelet Credential Provider` - [KEP 2133](https://github.com/kubernetes/enhancements/issues/2133)를 설명할 때입니다.

어렵고 formal 하게 쓰인 KEP 문서 대신 Kubernetes 공식 홈페이지의 매뉴얼 [[7]](https://kubernetes.io/docs/tasks/kubelet-credential-provider/kubelet-credential-provider/)로 소개해드리겠습니다. 이 기능을 켜면 kubelet은 plugin을 호출하여 동적으로 container image에 대한 credential을 가져오게 됩니다. kubelet과 plugin은 Kubernetes API 형식의 payload를 stdin과 stdout로 주고받으면서 통신하게 됩니다. 따라서, 다음 조건 중 1가지 이상에 해당한다면 이 기능을 사용하여 이득을 볼 수 있습니다.
- Credential을 가져오기 위해 cloud provider service의 API를 호출할 필요가 있는 경우
- Credential이 짧은 유효 기간을 가지며, 새 credential을 얻는 것이 주기적으로 필요한 경우
- Credential을 disk나 imagePullSecrets에 넣는 것이 적합하지 않은 경우

첫 번째 조건과 두 번째 조건은 ECR의 사용의 정확한 예시이며, 세 번째 조건은 풀고 싶은 문제와 정확하게 일치합니다! 그래서 guide를 따라 이 기능을 설정해봤습니다.

## High-Level Overview
문서를 따라서 할 일을 정리한 다음 개발을 시작했습니다. 전반적인 프로세스는 다음과 같습니다.
1. Plugin을 개발해서 binary 파일을 생성했습니다. ECR credential provider [[8]](https://github.com/kubernetes/cloud-provider-aws/tree/master/cmd/ecr-credential-provider)의 코드를 참고하여 쉽게 개발했습니다.
2. Plugin의 요청을 받아 유효한 요청인지 검증한 뒤, Harbor credential을 반환할 서버를 개발한 다음 배포했습니다. Cluster에서 정상적으로 발생한 요청인지 검증하기 위한 방법은 여러 가지가 있는데, 여기서는 aws-iam-authenticator[[9]](https://github.com/kubernetes-sigs/aws-iam-authenticator) 가 사용하는 방법을 사용했습니다.
3. 1에서 얻은 binary 파일을 모든 Kubernetes node에 넣었습니다. Bottlerocket 기반의 node에서는 bootstrap container라는 기능을 사용했고, AmazonLinux 기반의 node에서는 userdata를 적절히 추가했습니다.
4. 마지막으로 kubelet 설정 파일과 kubelet의 command line argument를 수정했습니다. Credential provider 설정 파일도 썼고, feature gate 설정도 수정했습니다.

이제 하나씩 자세히 소개해드리겠습니다.

### 1. Plugin Development
Plugin 개발은 golang을 할 수 있다면 매우 쉽습니다. Credential plugin은 필요할 때마다 kubelet에 의해서 1회성으로 실행되므로, 기본적으로 cli 개발과 유사합니다. `k8s.io/kubelet/pkg/apis/credentialprovider/` 패키지에서는 stdin에서 읽는 요청, stdout으로 전송하는 요청의 struct와 serialize / deserialize까지 제공해 줍니다. 그리고 위에서 소개했던 ECR credential provider의 코드와 테스트를 보면 쉽게 이해해서 개발할 수 있습니다. 아래는 kubelet에 의해 `GetCredentials` 가 호출되었을 때 `http://some-server-endpoint`에 `some-token`을 보내고, Harbor의 username과 password를 받아 stdout으로 보내는 간단한 코드입니다.
```go
type credentialRequest struct {
	Token string `json:"token"`
}

type credentialResponse struct {
	Message  string `json:"message"`
	Username string `json:"username"`
	Password string `json:"password"`
}

type harborPlugin struct {
	username string
	password string
}

func (e *harborPlugin) updateCredential() error {
	reqData := credentialRequest{Token: "some-token"}
	respData, err := getCredentialFromServer("http://some-server-endpoint", respData)
	if err != nil {
		return err
	}
	if respData.Message != "ok" {
		return errors.New(respData.Message)
	}
	e.username = respData.Username
	e.password = respData.Password
	return nil
}

func (e *harborPlugin) GetCredentials(ctx context.Context, image string, args []string) (*v1alpha1.CredentialProviderResponse, error) {
	err = e.updateCredential()
	if err != nil {
		return nil, err
	}
	return &v1alpha1.CredentialProviderResponse{
		CacheKeyType:  v1alpha1.RegistryPluginCacheKeyType,
		CacheDuration: &metav1.Duration{Duration: cacheDuration},
		Auth: map[string]v1alpha1.AuthConfig{
			harborRegistry: {
				Username: e.username,
				Password: e.password,
			},
		},
	}, nil
}
```
### 2. Server Development
이제 서버 개발을 해보겠습니다. 특별할 것 없는 go로 만든 http 서버입니다. 요청을 검증한 뒤, 올바른 요청에 대해서는 Harbor의 credentials를 전송합니다.
```go
var harborBotUsername = os.Getenv("HARBOR_BOT_USERNAME")
var harborBotPassword = os.Getenv("HARBOR_BOT_PASSWORD")

func validateRequest(r *http.Request) (bool, error) {
	return true, nil
}

func handleCredential(w http.ResponseWriter, r *http.Request) {
	resp := credentialResponse{}
	valid, err:= validateRequest(r)
	if valid && err == nil {
		resp.Message = "ok"
		resp.Username = harborBotUsername
		resp.Password = harborBotPassword
	} else {
		fmt.Printf("invalid request: validates: %t, error: %+v", valid, err)
		resp.Message = "<failed>"
		resp.Username = "<failed>"
		resp.Password = "<failed>"
	}

	respBytes, err := json.Marshal(resp)
	if err != nil {
		fmt.Printf("%v\n", err)
	}
	w.Write(respBytes)
}

func main() {
	r := mux.NewRouter()
	r.HandleFunc("/token/{registry:[a-z0-9.-]+}/", handleCredential)
	log.Fatal(http.ListenAndServe(":8080", r))
}
```
이 코드에는 문제가 있습니다. `validateRequest` 가 항상 `true`를 반환하므로, 이 server의 endpoint에 접근할 수 있다면 `curl http://some-server-endpoint/token/some-registry`를 호출하여 Harbor의 credentials를 얻을 수 있게 됩니다.

따라서, client에서는 적절한 token을 발급하고 server에서는 `validateRequest` 함수를 적절히 작성하여 kubelet에 의해 발생한 올바른 요청인지 검증해야 합니다. 여러 가지 구현이 가능하지만, 앞서 소개했듯 `aws-iam-authenticator`의 방법을 선택했습니다.
- client: `sts:GetCallerIdentity` API 호출을 presign 하여 token을 생성합니다. [이 method](https://github.com/kubernetes-sigs/aws-iam-authenticator/blob/v0.5.3/pkg/token/token.go#L316)와 유사하게 구현했습니다.
- server: token이 `sts:GetCallerIdentity`의 presigned url인지 검증하고, 실제로 호출하여 정상적인 response를 받는지 확인합니다. Response의 ARN 데이터가 Kubernetes의 node가 가지는 role과 동일한지 검사합니다. [이 method](https://github.com/kubernetes-sigs/aws-iam-authenticator/blob/v0.5.3/pkg/token/token.go#L425)와 거의 동일합니다.


여기까지 go 개발은 마무리하고, 이제부터 설정 파일을 수정해보겠습니다.

### 3. Plugin Download
1에서 개발한 plugin을 모든 Kubernetes node에 넣어야 합니다. 안타깝게도 kubelet이 켜지기 전에 plugin binary를 추가해야 하므로 DaemonSet 같은 방법을 사용할 수는 없습니다. 이제부터는 Bottlerocket 기반 node와 AmazonLinux 기반 node의 접근 방법이 달라 각각 따로 소개하겠습니다.

#### Bottlerocket
Bottlerocket은 "bootstrap container"[[10]](https://github.com/bottlerocket-os/bottlerocket#bootstrap-containers-settings)라는 기능이 있습니다. 말 그대로 Bottlerocket OS가 부팅될 때 실행할 수 있는 container로, `CAP_SYS_ADMIN` 권한을 가지고 실행되며, root filesystem에 접근할 수 있습니다.

1. 먼저, build 된 binary를 Bottlerocket root filesystem에 복사하는 `entrypoint.sh`를 만들었습니다.
   ```sh
   #!/bin/sh
   mkdir -p /.bottlerocket/rootfs/mnt/kubelet-registry-credential-plugins/
   cp /harbor-credential-provider /.bottlerocket/rootfs/mnt/kubelet-registry-credential-plugins/
   echo "Succeeded!"
   ```
2. 그다음, Dockerfile을 만들어 container image를 생성했습니다.
   ```Dockerfile
   FROM golang:1.16 as builder
   RUN some-build-process

   FROM some-base-image 
   USER root
   WORKDIR /
   COPY entrypoint.sh .
   COPY --from=builder /workspace/harbor-credential-provider .

   ENTRYPOINT ["/entrypoint.sh"]
   ```
3. 이렇게 생성된 container image를 ECR에 업로드하고, 아래 toml을 사용하여 매 부팅 시 실행되도록 설정했습니다.
   ```toml
   [settings.bootstrap-containers.harbor-credential-provider]
   source = "account-id.dkr.ecr.ap-northeast-1.amazonaws.com/bottlerocket-harbor-provider:latest"
   mode = "always"
   essential = true
   ```

Bootstrap container image가 ECR registry 안에 있는 경우 Bottlerocket이 자동으로 credential을 발급하여 image를 받게 되므로 위 설정은 완벽하게 작동합니다. 결과적으로 Bottlerocket이 켜지면, `/mnt/kubelet-registry-credential-plugins/` directory 안에 plugin이 저장됩니다!


#### AmazonLinux
AmazonLinux에서는 userdata를 수정하여 원하는 동작을 쉽게 수행할 수 있습니다. Bottlerocket에서 사용한 container image를 그대로 사용하기 위해, 동일한 path를 mount 하도록 다음 userdata를 추가했습니다.
```sh
mkdir -p /mnt/kubelet-registry-credential-plugins/
systemctl start docker
aws ecr get-login-password --region ${cluster_region} | docker login --username AWS --password-stdin ${account_id}.dkr.ecr.${cluster_region}.amazonaws.com
docker run -v /mnt/kubelet-registry-credential-plugins/:/.bottlerocket/rootfs/mnt/kubelet-registry-credential-plugins/ ${account_id}.dkr.ecr.${cluster_region}.amazonaws.com/bottlerocket-harbor-provider:latest
```
`/etc/eks/bootstrap.sh` 파일이 실행되기 전까지는 docker service가 정지되어 있으므로 직접 켜 줘야 하며, EC2에 attach 되어 있는 instance profile의 IAM profile로 ECR credential을 생성해 주입해야 합니다.

### 4. Kubelet Settings
이제 마지막 단계입니다. kubelet의 설정을 수정해야 하는데, 다음 설정을 추가해야 합니다. 
1. `CredentialProviderConfig` 파일을 쓰고, 이 파일의 경로를 kubelet의 `--image-credential-provider-config` argument로 넘겨야 합니다.
2. 위에서 download 한 plugin의 directory 경로를 kubelet의 `--image-credential-provider-bin-dir` argument로 넘겨야 합니다.
3. kubelet image credential provider는 alpha feature이므로 기본적으로 활성화되어있지 않아 kubelet의 설정을 조작하여 `KubeletCredentialProviders`를 켜야 합니다.

여기서, `CredentialProviderConfig` 파일은 다음과 같습니다. Providers의 이름은 plugin 실행 파일의 이름과 정확하게 일치해야 하며, `matchImages` list 중 하나와 일치하는 image를 pull 받을 때 해당 plugin을 사용하게 됩니다.
```yaml
---
apiVersion: kubelet.config.k8s.io/v1alpha1
kind: CredentialProviderConfig
providers:
  - apiVersion: credentialprovider.kubelet.k8s.io/v1alpha1
    name: harbor-credential-provider
    matchImages:
      - "harbor.hyperconnect.com"
    defaultCacheDuration: "1m"
    args: []
    env: []
```

#### Bottlerocket
안타깝게도 Bottlerocket은 `/etc/` directory 전체가 tmpfs이고, 동적으로 모든 설정이 생성되며, userdata가 없으므로 파일을 생성하기가 어렵습니다. 또한, kubelet argument를 변경하기 위해서는 systemctl이 읽는 kubelet의 configuration 파일을 변경해야 합니다. 이 설정을 변경하기 위해 Bottlerocket source code를 조금 수정했습니다.

1. 먼저 위 credential config 내용을 `packages/kubernetes-1.20/kubelet-credential-config` 파일로 추가합니다.
2. 그다음, kubelet argument를 추가하기 위해 `packages/kubernetes-1.20/kubelet-exec-start-conf` 파일을 수정합니다.
   ```sh
   {% raw %}{{#if settings.kubernetes.image-credential-provider-enabled}}
       --image-credential-provider-config="/etc/kubernetes/kubelet/credential-config" \
       --image-credential-provider-bin-dir="/mnt/kubelet-registry-credential-plugins/" \
   {{/if}}
   {% endraw %}```
3. `packages/kubernetes-1.20/kubernetes-1.20.spec` 파일을 적절히 수정하여 `kubelet-credential-config` 파일이 `/etc/` 에 설치되도록 합니다.
4. `sources/models/shared-defaults/kubernetes-services.toml`, `sources/packages/kubernetes-1.20/kubelet-config`나 `sources/models/src/lib.rs` 파일을 수정하여 feature gate를 활성화하고, 필요한 기능을 추가합니다. Credential provider 기능을 켜고 끄는 flag를 넣거나, debug를 위해 plugin이 연결하는 server의 주소를 설정할 수 있도록 설정을 추가할 수 있습니다.

더 자세한 Bottlerocket의 설정 추가 방법은 [이전 기술 블로그 글](https://hyperconnect.github.io/2021/03/08/bottlerocket-on-kubernetes.html)을 참고하시기 바라며, 이 글에서는 생략했습니다.

#### AmazonLinux
AmazonLinux에서는 userdata를 통해 직접 파일을 수정할 수 있으므로 Bottlerocket에 비해 쉽게 설정할 수 있습니다.

1. 먼저 credential-config를 다음과 같이 kubelet directory 안에 씁니다.
   ```sh
   echo "$CREDENTIAL_CONFIG" > /etc/kubernetes/kubelet/credential-config
   ```
2. 그다음, `bootstrap.sh`를 호출할 때 `kubelet-extra-args`를 통해서 `--image-credential-provider-config`와 `--image-credential-provider-bin-dir`를 설정해주고 feature gate를 켜면 끝납니다.
   ```sh
   /etc/eks/bootstrap.sh ... --kubelet-extra-args "--image-credential-provider-config=/etc/kubernetes/kubelet/credential-config --image-credential-provider-bin-dir=/mnt/kubelet-registry-credential-plugins/ --feature-gates=KubeletCredentialProviders=true" ...
   ```

Bottlerocket과는 달리 빠르게 설정이 끝났습니다!


# The Final Result
4단계에 걸친 개발과 복잡한 설정의 결과는 예상대로 작동했습니다. Bottlerocket에서는 `/etc/containerd/config.toml`에 credential을 hard-code하지 않아도 kubelet에서 성공적으로 image를 pull 했습니다.
```sh
bash-5.0# cat /etc/containerd/config.toml | grep "harbor" # empty result
bash-5.0# journalctl -u containerd | grep "harbor" | grep PullImage
Oct 27 08:03:41 ip-10-220-85-71.ap-northeast-1.compute.internal containerd[1646]: time="2021-10-27T08:03:41.783255616Z" level=info msg="PullImage \"harbor.hyperconnect.com/node-exporter:v0.0.0\""
Oct 27 08:03:51 ip-10-220-85-71.ap-northeast-1.compute.internal containerd[1646]: time="2021-10-27T08:03:51.292003346Z" level=info msg="PullImage \"harbor.hyperconnect.com/node-exporter:v0.0.0\" returns image reference \"sha256:...\""
```
AmazonLinux도 마찬가지로, `/root/.docker/config.json`에 credential을 hard-code하지 않아도 모든 Harbor image를 성공적으로 pull 했습니다.

# Wrap Up
AMI나 user-data에 hard-coded 된 private registry credential을 남기지 않도록 KEP 2133 - Kubelet Credential Provider 기능을 사용해 보았습니다.
- KEP 2133 규격에 맞춰 kubelet이 호출할 plugin을 만들었습니다.
- Plugin으로부터 요청을 받아 Harbor credential을 발급하는 http server를 만들었습니다.
- 생성한 plugin의 요청을 검증하기 위해 aws-iam-authenticator가 사용하는 인증 방식을 사용해서 server를 보호했습니다.
- kubelet 설정과 command line argument를 추가하여 기능을 활성화하고, 테스트해봤습니다.

결과적으로, ImagePullSecrets 없이 편리하면서도 안전하게 credential을 관리할 수 있게 되었습니다. ECR이 아닌 다른 private registry를 사용하고 계신 분들께 많은 도움이 되었으면 좋겠습니다.

긴 글 읽어주셔서 감사합니다 :)

<br>
<br>
언제나 글 마지막은 채용공고입니다. 이렇게 재미있는(?) 일을 같이할 Cloud Platform Engineer의 많은 지원 부탁드립니다. [채용공고 바로가기](https://career.hyperconnect.com/jobs/)

# References
[1] [https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/)

[2] [https://aws.amazon.com/bottlerocket/](https://aws.amazon.com/bottlerocket/)

[3] [https://aws.amazon.com/ecr/](https://aws.amazon.com/ecr/)

[4] [https://aws.amazon.com/eks/](https://aws.amazon.com/eks/)

[5] [https://github.com/kubernetes/kubernetes/blob/release-1.20/pkg/credentialprovider/aws/aws_credentials.go](https://github.com/kubernetes/kubernetes/blob/release-1.20/pkg/credentialprovider/aws/aws_credentials.go)

[6] [https://github.com/kubernetes/kubernetes/tree/release-1.20/pkg/credentialprovider](https://github.com/kubernetes/kubernetes/tree/release-1.20/pkg/credentialprovider)

[7] [https://kubernetes.io/docs/tasks/kubelet-credential-provider/kubelet-credential-provider/](https://kubernetes.io/docs/tasks/kubelet-credential-provider/kubelet-credential-provider/)

[8] [https://github.com/kubernetes/cloud-provider-aws/tree/master/cmd/ecr-credential-provider](https://github.com/kubernetes/cloud-provider-aws/tree/master/cmd/ecr-credential-provider)

[9] [https://github.com/kubernetes-sigs/aws-iam-authenticator](https://github.com/kubernetes-sigs/aws-iam-authenticator)

[10] [https://github.com/bottlerocket-os/bottlerocket#bootstrap-containers-settings](https://github.com/bottlerocket-os/bottlerocket#bootstrap-containers-settings)

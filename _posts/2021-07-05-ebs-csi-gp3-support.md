---
layout: post
date: 2021-07-05
title: AWS EBS gp3 출시하자마자 EKS에서 사용하기
author: sammie
tags: kubernetes cluster eks ebs csi gp3
excerpt: AWS EBS에 gp3 type이 출시되자마자 AWS EKS에서 사용한 과정을 간략하게 공유합니다.
last_modified_at: 2021-07-05
---

안녕하세요, DevOps 팀의 Sammie입니다. 이번 글에서는 지난 2020년 12월 1일에 출시된 gp3 type의 EBS volume[[1]](https://aws.amazon.com/blogs/aws/new-amazon-ebs-gp3-volume-lets-you-provision-performance-separate-from-capacity-and-offers-20-lower-price/)을 EKS에서 사용한 경험을 짧게 소개합니다.

# What is EBS?
Elastic Block Store (EBS)[[2]](https://aws.amazon.com/ebs/)는 EC2 instance에서 쉽게 사용할 수 있는 영구적인 volume입니다. AWS console 또는 API를 사용하여 EBS volume을 생성하고, EC2 instance에 붙이게 되면 Linux가 해당 volume을 device로 인식하게 됩니다. 그다음, `mkfs` 명령어를 사용하여 file system을 생성하고, `mount` 명령어로 지정한 directory에 mount 하여 사용할 수 있습니다.

EBS는 사용자의 workload에 따라 다양한 EBS 볼륨 유형[[3]](https://docs.aws.amazon.com/ko_kr/AWSEC2/latest/UserGuide/ebs-volume-types.html)을 지원합니다. 일반적인 workload에 적합한 SSD 기반 `gp2`, latency 및 IOPS (input-output operations per second)가 매우 중요한 database 등에 적합한 `io1` 및 `io2`, 그리고 throughput이 중요한 batch 작업 등에 적합한 HDD 기반의 `st1`, `sc1` 등이 있습니다. AWS에서는 지난 2014년 처음으로 SSD 기반의 EBS type인 `gp2`를 출시[[4]](https://aws.amazon.com/blogs/aws/new-ssd-backed-elastic-block-storage/)했고, 지난 2021년 12월에는 storage 용량과 무관하게 iops를 조절할 수 있는 `gp3`를 출시했습니다.

# Why gp3?
기존 `gp2`에서 높은 iops를 사용하기 위해서는 반드시 volume 크기를 늘려야 합니다. `gp2`의 iops는 GB당 3 iops로 일정하게 확장되기 때문입니다. 따라서 용량이 클 필요는 없지만, iops가 많이 필요한 workload에 적합하지 않았습니다. `io1`이나 `io2`를 사용하면 GB당 provisioning 할 iops를 정할 수 있지만, `gp2`보다 가격이 매우 비싸기 때문에 RDS 등 일부 production workload를 제외하면 사용하기 힘들다는 단점이 있습니다.

반면 `gp3`는 volume 크기와 무관하게 volume의 전체 iops를 정할 수 있습니다. 또한 volume 크기와 iops와도 무관하게 volume 전체의 throughput도 지정할 수 있습니다. 그러면서도 가격은 iops나 throughput을 무료 제공 값을 초과하여 설정하지만 않는다면 어떤 용량에서도 `gp2` 보다 저렴합니다. 그리고 무료 제공되는 iops나 throughput은 1TB 이하에서 `gp2` 보다 항상 좋습니다. 즉, `gp2`에서 `gp3`로 migration하지 않을 이유가 거의 없습니다. (다만 `gp3`는 burst balance를 사용하여 순간적으로 기본 제공되는 iops 이상의 성능을 낼 수 있도록 burst 되지 않습니다.)

자세한 비교는 OpsNow blog 글 [[5]](https://blog.opsnow.com/26) 등 많은 자료가 있으니 참고하시기 바랍니다.

# PV, PVC and StorageClass
Kubernetes 환경에서 모든 workload는 Pod이라는 최소 단위로 실행됩니다. Pod은 container 기술을 사용하여 구현되므로, Pod이 삭제되게 되면 container 내부의 모든 파일이 삭제됩니다. 데이터를 영구적으로 저장할 수 있도록 Kubernetes에서는 Persistent Volume (PV)와 Persistent Volume Claim (PVC) [[6]](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)라는 기능을 제공합니다.

PV는 Kubernetes node처럼 cluster 단위의 resource이며, 보통 관리자가 생성하거나 PVC로부터 동적으로 생성됩니다. PV는 물리적인 volume을 나타내며, NFS나 EBS 같이 다양한 방법으로 구현할 수 있습니다. 이때, PV object는 구현 방법과 설정을 저장합니다. 예를 들어, NFS를 사용하는 PV object에는 NFS 서버의 ip가 기록되어있습니다.
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv 
spec:
  capacity:
    storage: 5Gi
  accessModes:
    - ReadWriteOnce
  nfs:
    path: /tmp
    server: 127.0.0.1 
```

PVC는 Pod처럼 namespace 단위의 resource이며, 보통 사용자가 생성합니다. 사용자가 PVC를 생성할 때 사용할 용량, access mode 또는 다른 옵션 등을 설정하면 요청과 일치하는 PV나 요청에 맞는 PV가 동적으로 생성되어 PVC와 1대 1 binding 됩니다. 이후, Pod에서 `.spec.volumes[].persistentVolumeClaim`을 사용하여 mount 할 수 있습니다.
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
---
apiVersion: v1
kind: Pod
metadata:
  name: pod
  namespace: default
spec:
  containers:
    - name: test 
      image: dummy 
      volumeMounts:
        - mountPath: "/tmp"
          name: pvc 
  volumes:
    - name: pvc
      persistentVolumeClaim:
        claimName: pvc 
```

일반적으로 AWS와 같은 cloud 환경에서는 PVC만 사용자가 직접 선언하여 생성하고, PV는 동적 생성 기능으로 자동 생성된 것을 사용합니다. PVC를 사용해 PV를 동적으로 생성하려면 `StorageClass`를 정의해야 합니다. EKS cluster를 생성하면 기본 `StorageClass`가 같이 생성됩니다.
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp2
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp2
  fsType: ext4 
```
Provisioner는 `StorageClass`의 설정과 PVC의 설정을 읽어 AWS EBS 등 물리적인 volume과 PV object 생성을 담당합니다. 위의 `StorageClass`는 Kubernetes source code 내부에 존재하는 AWS EBS provisioner를 사용하고 있고, 추가적으로 `type: gp2`와 `fsType: ext4` 옵션을 전달하도록 설정하고 있습니다. 이제 아래 PVC와 같이 `.spec.storageClassName`을 사용하여 `StorageClass`를 지정하면 자동으로 5Gi의 용량을 가지는 gp2 type의 EBS가 생성되며, PV object 또한 생성됩니다. 
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-ebs
  namespace: default
spec:
  storageClassName: gp2
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

이 내용을 그림 한 장으로 요약한 것이 [Kubernetes In Action](https://www.manning.com/books/kubernetes-in-action)에 나오는 아래 그림입니다.
![pv pvc storageclass]({{"/assets/2021-07-05-ebs-csi-gp3-support/00-pv.png"}}){: width="800px" }

# What is CSI Driver?
위 단락의 `StorageClass` 설명에는 매우 불편한 점을 찾을 수 있습니다. Kubernetes source code 내부에 존재하는 AWS EBS provisioner는 당연히 Kubernetes release lifecycle을 따라서 배포되므로, provisioner 신규 기능을 사용하기 위해서는 Kubernetes version을 업그레이드해야 하는 제약 사항이 있습니다.

따라서, Kubernetes 개발자는 Kubernetes 내부에 내장된 provisioner (in-tree)를 모두 삭제하고, 별도의 controller Pod을 통해 동적 provisioning을 사용할 수 있도록 만들었습니다. 이것이 바로 CSI (Container Storage Interface) driver [[7]](https://kubernetes-csi.github.io/docs/introduction.html)입니다.

AWS EBS 역시 Amazon EBS CSI driver[[8]](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)를 사용하여 동적으로 provisioning 할 수 있습니다. AWS 공식 문서에 따라 Helm chart나 manifest를 통해 CSI driver를 설치하면 몇 개의 workload와 `CSIDriver`라는 종류의 object가 설치됩니다.
```yaml
apiVersion: storage.k8s.io/v1
kind: CSIDriver
metadata:
  name: ebs.csi.aws.com
spec:
  attachRequired: true
  podInfoOnMount: false
```

그러면 이제 `ebs.csi.aws.com` provisioner를 사용하는 `StorageClass`를 아래와 같이 추가할 수 있습니다. 이후에는 in-tree `StorageClass`를 사용했던 것처럼 PVC object를 생성하면 됩니다.
```yaml
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: gp2-csi
provisioner: ebs.csi.aws.com
parameters:
  type: gp2
  fsType: ext4
```

아래 그림은 일반적인 CSI driver의 구조입니다. AWS EBS CSI driver 역시 아래와 같은 구조를 가지는데, 오른쪽 StatefulSet 또는 Deployment로 배포된 controller Pod이 AWS API를 사용하여 실제 EBS volume을 생성하는 역할을 합니다. 왼쪽 DaemonSet으로 배포된 node Pod은 AWS API를 사용하여 Kubernetes node (EC2 instance)에 EBS volume을 attach 해줍니다.
![CSI structure]({{"/assets/2021-07-05-ebs-csi-gp3-support/01-csi-structure.png"}}){: width="800px" }

더 자세한 구조와 동작에 대한 설명은 Container Storage Interface의 [Design Document](https://github.com/kubernetes/community/blob/master/contributors/design-proposals/storage/container-storage-interface.md)를 참고하시기 바랍니다.

# Add gp3 Support
2020년 12월 2일 `gp3` 공개 소식을 본 Hyperconnect의 DevOps engineer는 기존에 설치된 EBS CSI driver를 사용해서 `gp3` volume을 생성해보려고 했지만, 당연히 PV가 생성되지 않았습니다. EBS CSI driver는 입력값에 대한 validation을 하고 있었고, AWS SDK를 사용하여 EBS를 생성하고 있었는데 바로 전날 발표된 `gp3` type을 인식하지 못하고 있었습니다.

혹시나 validation을 우회할 방법이 없을까 golang 코드를 들여다봤지만 방법이 없다는 사실을 알게 되었습니다. 그와 동시에 EBS CSI driver의 코드가 생각보다 복잡하지 않다는 사실도 같이 알게 되었습니다. 이미 IOPS를 설정할 수 있는 `io1` type의 volume 생성을 지원하고 있어, 코드를 조금만 복사 + 붙여 넣기 하면 `gp3` volume을 지원하도록 만들 수 있을 것 같은 느낌이 들었습니다.

`pkg/cloud/cloud.go` 코드에 `VolumeTypeGP3`를 추가하고, `VolumeTypeIO1`처럼 iops 관련 parameter를 받도록 했습니다. 또한, `gp3`의 기능인 throughput도 받을 수 있도록 했습니다.
```diff
	switch diskOptions.VolumeType {
	case VolumeTypeGP2, VolumeTypeSC1, VolumeTypeST1, VolumeTypeStandard:
		createType = diskOptions.VolumeType
	case VolumeTypeIO1, VolumeTypeIO2:
		createType = diskOptions.VolumeType
		iops = capacityGiB * int64(diskOptions.IOPSPerGB)
+	case VolumeTypeGP3:
+		createType = diskOptions.VolumeType
+		iops = int64(diskOptions.IOPSTotal)
+		throughput = int64(diskOptions.Throughput)
```
그리고 AWS SDK의 버전을 최신으로 올려서 gp3 type을 인식할 수 있도록 만들었습니다.

몇 차례의 빌드 끝에 12월 3일 새벽, gp3 provision이 가능한 patch를 얻어 테스트용 Kubernetes에 설치한 다음, StorageClass 2개와 PVC 2개를 생성해보았습니다.
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  csi.storage.k8s.io/fstype: ext4
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gp3
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 4Gi
---
kind: StorageClass
apiVersion: storage.k8s.io/v1
metadata:
  name: gp3-full
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iopsTotal: "5000"
  throughput: "300"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gp3-full
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3-full
  resources:
    requests:
      storage: 10Gi
```
몇 초 후, AWS EBS CSI controller Pod의 로그와 Kubernetes Event에 성공 메시지가 나타났습니다. AWS console에 접속하여 EBS volume을 확인한 결과 아래처럼 원하는 volume이 생겼습니다!
![gp3 support]({{"/assets/2021-07-05-ebs-csi-gp3-support/02-ebs-gp3.png"}}){: width="800px" }

## Pull Request to Upstream!
gp3를 지원하도록 변경한 코드를 Hyperconnect 내부에서만 사용하기에는 아까웠습니다. 마침 upstream에 관련된 issue만 있고 pull request가 없었습니다. 그날 아침, 코드를 조금 수정 해서 PR[[9]](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/pull/633)을 생성했습니다.
![gp3 support pr]({{"/assets/2021-07-05-ebs-csi-gp3-support/03-pr.png"}}){: width="800px" }

그리고 몇 가지 feedback을 받아 수정했습니다.
- 기본 type을 `gp2`에서 `gp3`으로 변경
- `gp3` 관련 문서 추가 및 수정
- `gp3` 관련 E2E 테스트 추가
- `gp3` 관련 내부 구현에서 몇 가지 조건 검사 추가
- `io1` type처럼 GB 단위 iops 지정이 아니라 volume 전체의 iops를 `iops` 키로 지정하도록 변경

마침내 12월 8일에 merge 되었고, 2일 뒤 v0.8.0이 release [[10]](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/pull/642) 되었습니다.
![gp3 support pr merged]({{"/assets/2021-07-05-ebs-csi-gp3-support/04-merged.png"}}){: width="800px" }

이번 PR을 작성하면서 코드 외에 경험했던 것을 공유해드리자면,
- EBS CSI driver repository는 golang 1.11 이전 style의 dependency 관리를 하고 있었습니다. 따라서, library version을 업데이트하니 vendor/ directory에 모든 dependency가 update 되었고, 200개 이상의 파일이 수정된 PR이 탄생했습니다. 이런 style이 처음이라 신기했습니다.
- 인프라 관련 test 코드는 작성하기 어렵습니다. 특히 end-to-end test라면 더욱 그렇습니다. 하지만 EBS CSI driver는 E2E test를 하고 있습니다. 다른 workload와의 간섭을 피하고 일관된 테스트 결과를 위해 test가 실행될 때마다 kops[[11]](https://github.com/kubernetes/kops)를 사용하여 Kubernetes cluster를 생성하고 있었습니다. 차원이 다른 테스트 방법에 놀랐습니다.
- 모든 테스트의 소요 시간은 평균 20분 정도였는데, 기다리기 지루했습니다. 직접 테스트를 돌려보려고 시도했지만, kops를 사용하여 동적으로 Kubernetes cluster를 생성할 때 AWS credentials과 resource를 설정하는 부분이 너무 복잡해서 포기했습니다.
- 복사 + 붙여 넣기를 잘했더니 돌아갔습니다. 첫 번째로 golang을 사용하여 의미 있는 개발(?)을 한 것 같아서 뿌듯했습니다.

# Wrap Up
EBS CSI driver를 사용하면 기존 `gp2` type의 EBS보다 성능과 가격이 좋은 `gp3` type의 EBS를 사용할 수 있습니다. 이것이 가능하도록 직접 구현하여 EBS CSI driver에 기여했습니다.

v0.8.0 release 이후 Hyperconnect의 모든 Kubernetes cluster의 EBS CSI driver를 upgrade 했고, `gp3`를 사용하는 `StorageClass`를 추가했습니다. 이제, 이 release 전에 생성된 PV를 제외하면 전부 `gp3`를 사용하고 있습니다.

처음으로 의미 있는 open source pull request를 생성한 뜻깊은 경험이었습니다. EBS CSI driver 사용에 도움이 되셨으면 좋겠습니다.


긴 글 읽어주셔서 감사합니다 :)

<br>
<br>
언제나 글 마지막은 채용공고입니다. 이렇게 재미있는(?) 일을 같이할 개발자분들의 많은 지원 부탁드립니다. [채용공고 바로가기](https://career.hyperconnect.com/jobs/)

# References
[1] [https://aws.amazon.com/blogs/aws/new-amazon-ebs-gp3-volume-lets-you-provision-performance-separate-from-capacity-and-offers-20-lower-price/](https://aws.amazon.com/blogs/aws/new-amazon-ebs-gp3-volume-lets-you-provision-performance-separate-from-capacity-and-offers-20-lower-price/)

[2] [https://aws.amazon.com/ebs/](https://aws.amazon.com/ebs/)

[3] [https://docs.aws.amazon.com/ko_kr/AWSEC2/latest/UserGuide/ebs-volume-types.html](https://docs.aws.amazon.com/ko_kr/AWSEC2/latest/UserGuide/ebs-volume-types.html)

[4] [https://aws.amazon.com/blogs/aws/new-ssd-backed-elastic-block-storage/](https://aws.amazon.com/blogs/aws/new-ssd-backed-elastic-block-storage/)

[5] [https://blog.opsnow.com/26](https://blog.opsnow.com/26)

[6] [https://kubernetes.io/docs/concepts/storage/persistent-volumes/](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

[7] [https://kubernetes-csi.github.io/docs/introduction.html](https://kubernetes-csi.github.io/docs/introduction.html)

[8] [https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html](https://docs.aws.amazon.com/eks/latest/userguide/ebs-csi.html)

[9] [https://github.com/kubernetes-sigs/aws-ebs-csi-driver/pull/633](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/pull/633)

[10] [https://github.com/kubernetes-sigs/aws-ebs-csi-driver/pull/642](https://github.com/kubernetes-sigs/aws-ebs-csi-driver/pull/642)

[11] [https://github.com/kubernetes/kops](https://github.com/kubernetes/kops)

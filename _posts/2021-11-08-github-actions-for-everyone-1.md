---
layout: post
date: 2021-11-08
title: 모두의 Github Actions (feat. Github Enterprise) 1편 - 모두가 쓸 수 있는 패턴 만들기
author: hong
tags: github-actions github-enterprise continuous-integration
excerpt: Github Enterprise에서 Github Actions를 이용하여 개발자들이 고민 없이 CI하는 방법에 대해 소개합니다.
last_modified_at: 2021-11-08
---

하이퍼커넥트에서는 최근 Jenkins에서 진행되던 CI/CD 태스크를 Github Actions으로 대부분 옮기는 작업을 진행했습니다. 이 글에서는 왜 Jenkins에서 잘 돌던 CI 작업을 Github Actions로 이전했는지, 이전하며 고려해야 할 점들은 어떤게 있었는지, 그리고 Github Enterprise를 사용할 때 특히 고려해야 할 점은 어떤 점들이 있는지에 관해서 다룹니다.



# Github Actions가 뭔데요?

Github Actions는 Github Repository와 연동되어 소프트웨어 빌드, 테스트, 그리고 배포까지 자동화 할 수 있는 강력한 CI/CD 도구입니다. Github 의 다양한 이벤트를 간단한 YAML 문법을 통해 트리거로서 사용할 수 있으며, Workflow 또한 개발자가 간단하게 YAML 문법을 통해 구성할 수 있고, 자주 사용되는 패턴은 Action이라는 별도의 YAML 문법을 사용하여 모듈화를 할 수 있는 것이 특징입니다. 아래는 Github Actions로 구성된 Workflow의 예시입니다.[1]

```yaml
name: GitHub Actions Demo
on: [push]
jobs:
  Explore-GitHub-Actions:
    runs-on: ubuntu-latest
    steps:
      - run: echo "🎉 The job was automatically triggered by a {% raw %}${{ github.event_name }}{% endraw %} event."
      - run: echo "🐧 This job is now running on a {% raw %}${{ runner.os }}{% endraw %} server hosted by GitHub!"
      - run: echo "🔎 The name of your branch is {% raw %}${{ github.ref }}{% endraw %} and your repository is {% raw %}${{ github.repository }}{% endraw %}."
      - name: Check out repository code
        uses: actions/checkout@v2
      - run: echo "💡 The {% raw %}${{ github.repository }}{% endraw %} repository has been cloned to the runner."
      - run: echo "🖥️ The workflow is now ready to test your code on the runner."
      - name: List files in the repository
        run: |
          ls {% raw %}${{ github.workspace }}{% endraw %}
      - run: echo "🍏 This job's status is {% raw %}${{ job.status }}{% endraw %}."

```

위의 workflow는 다음과 같이 구성되어 있습니다.

1. `on: [push]`: push event가 발생했을 때 workflow가 트리거 됩니다.
2. `run: echo`: Shell의 echo 명령어를 통해서 shell에 메세지를 출력합니다. 이 때, YAML Syntax를 이용하여 (e.g. `github.event_name` 등) Workflow를 트리거한 이벤트의 정보나 Workflow가 돌아가는 Actions Runner의 OS 정보, Repository의 정보 등을 얻어낼 수 있습니다.
3. `uses: actions/checkout@v2`: Repository를 체크아웃하는 과정입니다. "Actions" 라고 하는 일종의 모듈을 호출하여 공통적으로 사용하는 절차를 재사용할 수 있게 해 줍니다.

단순 메세지만을 출력하는 위의 예제를 넘어, 다양한 상황에서 다양한 작업을 할 수 있는 것이 Github Actions의 특징입니다. 예를 들어 Pull Request가 작성되었을 때 테스트를 돌리고 Test Coverage를 계산하거나, main branch에 Pull Request가 merge 되었을 때 자동으로 배포하는 등의 작업을 쉽게 할 수 있습니다.



# 왜 Github Actions를 사용하기로 결심했나요?

Jenkins 역시 강력한 도구임에 틀림 없습니다. CI/CD를 도와주는 수많은 플러그인이 존재하고, 여러 팀에서 잘 사용한 전력이 있는 튼튼한 툴입니다. 그러나, DevOps 입장에서는 개발자와 협업하기에는 부담이 있는 툴이었습니다. 그러한 부담은 주로 Worker Node 관리에서 발생했습니다. 예를 들어, Worker Node에 Go 언어가 설치되어 있어야 한다거나, docker와 같은 프로그램이 설치되어야 한다는 요청을 받았다고 가정합시다. Worker Node에 개발자의 접근을 허용하지 않는다면 DevOps가 일일이 프로그램을 설치해주느라 삽질(toil)의 비중이 늘어난다는 문제점이 있으며, Worker Node에 개발자의 접근을 허용하면 Worker Node가 보안적, 인프라적으로 관리가 잘 되지 않는다는 문제점이 있습니다.

또한, Github를 사용하는 팀 입장에서는 개발 편의성이 크게 증대된다는 특징이 있습니다. Github Actions는 Github과 강하게 결합되어 있어 Github과의 연동이 Jenkins에 비해 매끄럽고, 개발자들이 직접 YAML을 만들어 Commit하는 것 만으로 간단하게 CI/CD Workflow를 만들 수 있습니다. 그리고 Actions는 재사용이 가능한 형태로 만들어져 있어 Github Marketplace에 있는 Actions를 가져와서 복잡한 작업을 몇 줄의 YAML 작업만으로 간단하게 연동할 수 있다는 점이 강점이었습니다. 이러한 장점들 때문에 내부적으로 사용하고자 하는 수요가 늘어나고 있던 참이기도 했습니다.



# 어떻게 Github Actions를 사용했나요? (Feat. Enterprise)

Github Actions를 도입하며 제일 중요하다고 생각한 점은, 개발자들이 **실제로 인프라에 대한 걱정 없이 YAML Workflow를 commit 하는 것 만으로** 간편하게 CI/CD를 할 수 있어야 된다는 점이었습니다. 이 목표를 이루기 위해 저희 팀에서 고민한 점들을 공유해보도록 하겠습니다.

### 어디서 Workflow를 돌릴까요?

Actions Runner는 Github Actions를 실제로 돌리는 프로그램을 말합니다. 1 Runner당 하나의 Workflow를 수행할 수 있으며, Github이 호스팅하는 Github-hosted Runner와 직접 호스팅하는 Self-hoted Runner로 두 가지 종류가 있습니다.

Github Hosted Runner는 분당 Linux 기준 $0.008 과금되지만[2], Github가 Runner를 신경써서 운영해주므로 Actions Runner에 관해 DevOps 팀 조차 아무런 고민을 할 필요 없습니다. 빠르게 CI/CD를 적용해야 하는 작은 팀이라면 직접 Actions Runner를 구성하는 편 보다 나은 선택지가 될 수 있습니다.

그러나 하이퍼커넥트 팀은 이런 편리함을 버리고 Self-Hosted Runner의 형태로 Actions Runner를 직접 운영하기로 결정했습니다. 이렇게 결정하게 된 원인은 세 가지가 있습니다. 첫 번째로 Actions를 돌릴 때 Harbor에 있는 Private Docker Image에 접근해야 하는데, Github Runner에서 접근할 수 있도록 Security Group을 열어줄 수 없기 때문입니다. Github Hosted Runner가 떠 있는 IP 대역을 전부 열어주는 건 불가능할 뿐 더러, 보안적으로도 말이 안 되는 상황이었습니다. 두 번째로, Github Hosted Runner를 쓰는 것 자체가 외부에 코드를 노출시키는 행위이기 때문입니다. 마지막으로 빠른 CI/CD의 핵심인 빌드캐시가 Enterprise 판에서는 지원이 안 됩니다.[3] 일반 Github를 사용했다면 `actions/cache` 액션을 사용하는 것 만으로 간편하게 빌드 캐시를 구성할 수 있었지만, 하이퍼커넥트에서는 Github Enterprise 판을 사용하고 있기 때문에 치명적인 문제점이었습니다.

### 어떻게 Actions Runner를 띄우고 관리할까요?

Actions Runner는 AWS Launch Template과 Autoscaling Group을 통해 필요에 따라 언제든지 쉽게 Scale-out 할 수 있게 구성하였습니다. AWS EC2 Instance에 Actions Runner를 띄우는 과정은 쉽습니다. 다운로드 받고, 설치 스크립트에 따라 설치하면 됩니다. 이 때 Github에 Runner를 붙이기 위해서 토큰이 필요한데, 이 토큰은 Private Network를 통해 사내 CI를 담당하는 Django 서버를 거쳐 Github API를 호출하는 방식으로 얻어냈습니다. 그리고 Scale-In 되어 오랫동안 Offline이 된 러너 데이터를 지우는 Periodic Task도 하나 구현하여 Online인 Runner만 추려내는 기능도 구현하였습니다.

비용 최적화를 위해, Actions Runner는 용도와 Instance의 크기에 따라 Pool이라는 개념으로 구분하였습니다. CI/CD 대부분의 작업은 비교적 간단하고 금방 끝나는 작업입니다. 이러한 작업들을 위한 Pool인 m5a.large Pool을 만들고 인스턴스를 여러 대 배치해 놓았습니다. 반면, CI/CD가 오래 걸리고 메모리 사용량이 많은 경우도 있어 사이즈가 큰 Pool도 만들어 소수의 인스턴스를 배치하거나, 메모리는 별로 차지하지 않으나 디스크를 많이 차지하는 Pool을 만들어 소수의 인스턴스를 배치하는 등의 작업도 진행했습니다. Actions Runner에는 Pool 별로 다른 Label을 붙였습니다.

![Runner Label Example]({{"/assets/2021-11-08-github-actions-for-everyone-1/runner-label.png"}})

이 작업은 개발자가 비용, 인프라 스펙에 대한 걱정을 일체 할 필요가 없게 합니다. 일반적인 작업이라면 공용 Pool을 사용하도록, 특수한 작업이라면 특수 Pool을 사용하도록 Workflow의 `runs-on` 항목만 수정하면 됩니다.

관련 인프라는 Terraform을 이용하여 작성했습니다. Parameter, Runner Label을 붙이는 User Data 만 살짝 다르고 나머지는 다 똑같기 때문에 Terraform 의 `for`문을 활용하여 `local` 변수를 만들고, `local` 변수 기반으로 `for_each`문을 사용하여 쉽게 만들었습니다.

```terraform
locals {
  gp_nodes = {
    for i in var.instances:
    "${i.instance_type}-${i.pool_name}" => {
      instance_type = i.instance_type
      min_capacity = i.min_capacity
      max_capacity = i.max_capacity
      volume_size = i.volume_size
      image_id = data.aws_ami.amzn2.id
      suspended_processes = ["AZRebalance"]
      user_data = base64encode(data.template_file.init["${i.pool_name}-${i.instance_type}"].rendered)
    }
  }
}
```

이제 Parameter만 다른 Pool이 한 벌 더 필요하다면 instances 변수에 Runner 스펙만 적어주면 됩니다.

### Workflow는 어떻게 돌릴까요?

고민하고 있는 점은 크게 세 가지가 있었습니다. 첫 번째로, 전사적으로 CI/CD를 하는 데 공통적으로 필요한 프로그램들이 있는데 공통적으로 필요한 프로그램들이 추가될 때 마다 새로 프로그램을 모든 Pool의 모든 Runner에 일일이 깔아주는 것은 귀찮습니다. 두 번째로, CI/CD를 할 때 특정 팀이 추가로 특정 프로그램을 설치해야 하는 경우입니다. 마찬가지로 이 경우 모든 Runner에 일일이 깔아주는 것이 귀찮습니다. 마지막으로 Actions가 특정 Linux Distro(특히 Ubuntu)에 의존적인 경우입니다. 아무리 Runner Pool을 만드는 것이 쉬워도 Distro마다 새로운 Runner Pool을 만드는 것은 귀찮습니다.

다행히도, Github Actions는 간단한 YAML 작성을 통해 Docker 컨테이너 위에서 CI/CD 작업을 할 수 있도록 해줍니다. 아래는 job이라는  Workflow의 작업을 Harbor에서 Pull 해 온 `devops/actions/base` 라는 컨테이너 위에서 작업하겠다는 의미입니다.

```yaml
jobs:
  job:
    container:
      image: harbor.address/devops/actions/base:latest
      credentials:
        username: bot@hpcnt.com
        password: {% raw %}${{ secrets.BOT_PASSWORD }}{% endraw %}
    runs-on: ["gprunner", "pool=m5a.large"]
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v2
```

모든 고민이 해결되는 순간이었습니다. 첫째로, 전사적으로 필요한 프로그램은 공용 컨테이너 이미지를 구워서 해결하면 되는 문제입니다. 둘째로, 각 조직에서 필요한 프로그램은 공용 컨테이너를 base로 하는 조직별 컨테이너 이미지를 구워서 해결하면 되는 문제입니다. 셋째로, Linux Distro에 영향을 받는다면 해당 Distro의 컨테이너 이미지를 base로 하여 별도로 이미지를 구우면 되는 문제입니다. 이제 개발자들이 CI/CD 과정에서 필요한 프로그램 설치는 Dockerfile 작성을 통해 직접 할 수 있습니다. DevOps는 단순히 Dockerfile Pull Request만 리뷰하면 됩니다.

그러나 이렇게 되면 한 가지 고민이 생깁니다. Docker 관련 작업을 컨테이너 안에서 어떻게 할까요?

### Docker 작업을 어떻게 컨테이너 위에서 하나요?

Docker Container 안에서 Docker 작업을 수행하기 위한 방법으로 크게 DinD(Docker-in-Docker)와 DooD(Docker-out-of-Docker) 방법이 있습니다. DinD는 docker를 privileged mode로 띄우고 별도의 docker를 띄워 호스트의 namespace에 접근할 수 있게끔 하는 방법입니다. Github Actions에서 흑마술을 사용하면 가능은 하지만 컨테이너가 호스트를 오염시킬 수 있으므로 당연히 보안적으로 안 좋습니다. DooD는 docker image에 `/var/run/docker.sock` 소켓을 동일한 위치에 마운트하고 docker client만 깔아서 host의 docker를 그대로 쓰는 방법입니다.

Github Actions에서는 DooD 방법을 사용합니다. Github 팀이 처음부터 고민했다는 듯, docker 위에서 workflow를 돌리겠다고 선언하면 기본적으로 아래와 같은 flag를 넣어 컨테이너를 실행합니다.

```shell
/usr/bin/docker create --name container_name
                      --label xxx --workdir /__w/repo/repo --network yyy
                      -e "HOME=/github/home" -e GITHUB_ACTIONS=true -e CI=true
                      -v "/var/run/docker.sock":"/var/run/docker.sock"
                      -v ... --entrypoint "tail" image "-f" "/dev/null"
```

`-v "/var/run/docker.sock":"/var/run/docker.sock"` 가 있으니 docker 작업은 문제 없겠네요. 그 외에도 여러 디렉토리를 마운트 하는 게 보입니다.

### Q: 와 그러면 CI/CD에서 외부 컨테이너가 필요하면 그냥 띄우면 되겠네요!

A: 아닙니다 고민이 필요합니다!

### Service Container

redis나 mysql과 같은 외부 컨테이너가 필요하면 막 띄울 수는 있기는 하지만 이렇게 하면 두 가지 문제가 있습니다. 첫 번째로 CI 작업 도중에 workflow가 실패할 경우 띄웠던 컨테이너를 직접 내리지 않으면 컨테이너가 그대로 남아있게 됩니다. 두 번째로, 띄운 컨테이너와 통신하기 어렵습니다. 위 명령어 줄에서 `--network yyy` 플래그를 보셨으면 눈치채셨겠지만, Docker 위에서 Github Actions을 돌린다고 하면 Actions Runner는 Workflow가 돌아가는 컨테이너 뿐만 아니라 docker bridge network를 하나 만듭니다.[4] 띄운 컨테이너와 같은 네트워크에 있고 호스트 네임을 정확하게 알아야 통신을 할 수 있겠죠.

같은 네트워크에 컨테이너를 띄우는 방법은 간단합니다. Actions YAML Syntax에 Service Container라는 것을 정의할 수 있습니다.[4]

```yaml
name: Redis container example
on: push

jobs:
  # Label of the container job
  container-job:
    # Containers must run in Linux based operating systems
    runs-on:
      - gprunner
      - m5a.large
    # Docker Hub image that `container-job` executes in
    container:
      image: harbor.address/devops/actions/base:latest
      credentials:
        username: bot@hpcnt.com
        password: {% raw %}${{ secrets.BOT_PASSWORD }}{% endraw %}
    # Service containers to run with `container-job`
    services:
      # Label used to access the service container
      redis-host:
        # Docker Hub image
        image: redis
```

이렇게 하면 `redis-host` 라는 hostname을 가진 dockerhub의 redis 컨테이너가 workflow가 실행되는 컨테이너와 같은 네트워크에 뜨게 됩니다. 해당 Redis의 주소는 `redis-host` 로 설정하면 끝납니다. 이렇게 하면 컨테이너의 lifecycle 관리는 actions runner가 알아서 해 주니 걱정은 없습니다.



# 결론

이번 글에서는 하이퍼커넥트에서 Github Actions를 어떻게 운영하는지, 어떻게 개발자들이 고민 없이 Github Actions를 사용할 수 있는 패턴을 구성할지에 대해 다뤘습니다. 하이퍼커넥트에서는 Self-hosted runner를 Pool이라는 개념을 통해 관리하고 있으며, Docker 컨테이너를 사용한 패턴으로 모든 조직에서 동일한 CI/CD 경험을 할 수 있도록 구성했습니다.

다음 글에서는 공용 Runner에서 타 조직에 노출되지 않도록 Secret 관리하는 방법, 특히 어떻게 개발자가 이 과정을 고민하지 않게 만들었는지에 관해 다뤄보려고 합니다.

# References

[1] [https://docs.github.com/en/actions/quickstart]({{https://docs.github.com/en/actions/quickstart}})

[2] [https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions)

[3] [https://github.com/actions/cache/pull/421](https://github.com/actions/cache/pull/421)

[4] [https://docs.github.com/en/actions/guides/about-service-containers](https://docs.github.com/en/actions/guides/about-service-containers)


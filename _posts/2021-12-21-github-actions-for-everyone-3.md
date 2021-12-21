---
layout: post
date: 2021-12-21
title: 모두의 Github Actions (feat. Github Enterprise) 3편 - Build Cache
author: hong
tags: github-actions github-enterprise continuous-integration
excerpt: Github Actions의 Build Cache를 어떻게 구성했는지에 대하여 다룹니다.
last_modified_at: 2021-12-21
---

지난 글에서는 Github Actions를 이용하며 번거롭지 않고 안전하게 Secret에 접근하는 방법에 대해 다루었습니다. 핵심은 Vault Login을 Actions Runner에서 잘 할 수 있도록 구성하고, 나머지는 Vault에 맡기는 것이었습니다.

이번 글에서는 Github Enterprise 위에서 Github Actions를 사용하며 지원되지 않는 빌드캐시를 어떻게 스스로 구축했는지에 대하여 다루어보려고 합니다.

# Build Cache

빌드 캐시는 모든 CI에서 빠질 수 없는 기능입니다. 빌드 캐시 유무에 따라 빌드 시간이 수 분에서 수 십 분까지 차이가 나기도 하고, 이는 개발자들의 생산성에 큰 영향을 미칩니다. Github.com의 경우 Github Actions에서 기본으로 제공하는 캐시(actions/cache, [1])가 있어 yaml 대여섯줄로 간단하게 빌드 캐시의 효과를 누릴 수 있습니다. 그래서 Github Enterprise에서도 똑같이 사용할 수 있는지 확인을 해 봤고, 그 결과 아래의 코드를 발견하게 됩니다.

```js
if (utils.isGhes()) {
  utils.logWarning(
    "Cache action is not supported on GHES. See https://github.com/actions/cache/issues/505 for more details"
  );
  utils.setCacheHitOutput(false);
  return;
}
```

해당 이슈를 따라가보면, "Github Enterprise에서는 actions/cache를 지원하지 않습니다. GHE에서는 대부분 self-hosted runner를 사용하고, 별도의 외부 캐시를 두는 것 보다는 같은 머신에서 빌드 캐시를 공유하는 것이 효율적이다"라는 이유에서 입니다. 그러나 이 말은 컨테이너를 사용하면 어림도 없는 말이 됩니다. 빌드 캐시가 컨테이너 안에 남고, CI 작업이 끝나면 전부 삭제되는 판이라서, 머신에서 빌드 캐시를 공유하는 것도 할 수 없는 일이었습니다. 이대로 빌드 캐시는 영영 포기해야만 하는 것일까요?

![하겠습니다. 그것이 엔지니어니까.]({{"/assets/2021-12-21-github-actions-for-everyone-3/koizumi.gif"}})

하지만 우리는 엔지니어입니다. 모든 상황을 이겨내고 해 내야 합니다. 그것이 엔지니어니까 (끄덕). 저희 팀은 빌드 캐시를 직접 만들어 Github Action으로 사내 배포하기로 결정했습니다. 접근한 방법은 간단합니다.

1. 머신간 공유할 수 있는 파일 시스템을 마운트합니다.
2. 마운트한 파일 시스템을 CI 컨테이너에서 쓸 수 있도록 합니다.
3. CI가 종료될 때 캐시 되어야 할 아티팩트를 압축하여 파일 시스템에 잘 남깁니다.
4. 나중에 CI가 재실행되면 파일 시스템에서 캐시를 복원해옵니다.

### 1. 머신간 공유할 수 있는 파일 시스템을 마운트 합니다.

저희 팀은 Self-hosted runner를 모두 AWS 위에서 운영하고 있습니다. 따라서 머신간 공유할 수 있는 파일 시스템으로 제일 먼저 생각한 것도 EFS입니다. EFS는 AWS의 Managed NFS Service입니다. 저희 팀은 EFS를 빌드 캐시용 파일 시스템으로 사용하기로 결정하였습니다.

EFS를 캐시용 파일 시스템으로 사용하기 전에 고민했던 점은 바로 가격입니다. EFS는 ap-northeast-1 region 기준, 매월 GB당 0.36 달러가 청구됩니다[2]. 만약 EFS를 이용하여 캐시를 구현하고 1TB 정도 사용할 경우 연간 캐시용 볼륨 비용으로 4,320 달러를 내야 하게 됩니다. 이는 생각보다 큰 돈이고 EFS를 도입해도 될지 반신반의하게 만들었습니다. 빌드캐시 볼륨의 경우 사용하지 않는 빌드캐시가 계속 쌓여 용량이 꾸준히 증가하여 1TB정도 사용할 것이고, 이를 청소해주지 않으면 돈을 더 내야 하는 상황이 되기 때문입니다. 한 편, 사용하는 캐시 엔트리인지 아닌지 구분하여 삭제해주는 작업은 어렵습니다. 

그럼에도 불구하고 EFS를 사용하게 된 이유는 Infrequent Access 기능 때문이었습니다. EFS는 자주 접근하지 않는 파일에 대해서 저장하는 방식을 변경해서 비용을 절감해주는 Infrequent Access 기능을 지원합니다. Infrequent Access 기능은 최소 7일에서 최대 90일까지 기간을 설정할 수 있으며, 설정한 기간동안 파일 액세스가 일어나지 않는다면 파일의 클래스를 변경합니다. 이 경우 ap-northeast-1 region 기준 1GB당 0.0272 달러[2]가 청구되며, Standard Class의 7%에 해당되는 금액입니다. 빌드캐시는 dependency가 업데이트되어 한 번 접근되지 않기 시작하면 그 뒤로도 접근되지 않게 될 확률이 매우 높습니다. 그래서 저희는 `AFTER_7_DAYS` 로 파일의 lifecycle policy를 설정하여 7일 뒤 IA 클래스로 캐시 엔트리를 옮기도록 했습니다. 그 결과 비용을 절약하며 저희는 용량 절감을 위한 행동을 아무것도 안 해도 되는 상태로 EFS를 캐시용 파일 시스템으로 사용할 수 있었습니다. 아래의 그림은 4개월동안 캐시를 운영하며 Standard class와 IA class로 저장된 파일의 용량을 보여줍니다.

![Infrequent Access]({{"/assets/2021-12-21-github-actions-for-everyone-3/IA.png"}})

### 2. 마운트한 파일 시스템을 CI 컨테이너에서 쓸 수 있도록 합니다.

이제 Actions Runner를 구성하는 terraform에 EFS를 NFS 볼륨으로 마운트하는 작업을 합니다. Mount Target을 만들고, Userdata를 이용하여 정해진 디렉토리(`/cache`)에 마운트 되도록 작업했습니다. Github Actions는 docker를 이용하여 Actions를 실행하는 경우 docker flag를 주입할 수 있도록 문법적으로 지원해 주고 있습니다. 그래서 이 부분은 `-v` 플래그를 yaml에 집어넣는 것으로 쉽게 진행되었습니다.

```yaml
name: cache
on:
  ...
jobs:
  cache_action:
    container:
      ...
      options: "-v /cache:/__cache"
```

### 3. CI가 종료될 때 캐시되어야 할 아티팩트를 압축하여 파일 시스템에 잘 남깁니다.

캐시 엔트리가 들어갈 공간도 준비가 되었고, 이제 캐시 하기만 하면 됩니다. 저희 팀은 캐시하는 Action을 Typescript를 이용하여 직접 구현하여 캐시될 파일을 압축하고 캐시 볼륨으로 옮기는 과정을 추상화 했습니다. 사용자에게 요구하는 것은 캐시될 파일의 이름의 접두어(prefix)와 Lockfile의 hash입니다. Lockfile의 hash를 요구한 이유는 Dependency가 달라질 때 다른 캐시 아이템을 사용하도록 하기 위함입니다. 파일의 hash는 Github Actions yaml 문법에서 `hashFiles` 라는 함수가 있어 쉽게 할 수 있습니다.

이 모든 과정을 `actions/cache` 와 비슷하게 구성하려고 했습니다. 저희 팀이 만든 캐시 액션을 이용하여 개발자가 빌드 캐시 엔트리를 캐시 볼륨에 저장하는 방법은 아래와 같습니다. (Node 기준, 다른 언어의 경우 [3]과 비슷하게 하면 됩니다.)

```yaml
name: cache
on:
  ...
jobs:
  cache_action:
    container:
      ...: ...
      options: "-v /cache:/__cache"
      ...: ...
    runs-on: ...
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v2
      - name: Setup Node
        uses: actions/setup-node@v1
        with:
          node-version: '12'
      - name: Cache Action
        uses: hyper-actions/hyper-cache@v2
        with:
          path: ~/.npm
          key: {% raw %}${{ runner.os }}{% endraw %}-build-node-example-app-master-{% raw %}${{ hashFiles('**/package-lock.json') }}{% endraw %}
          restore-keys: |-
            {% raw %}${{ runner.os }}{% endraw %}-build-node-example-app-master-
            {% raw %}${{ runner.os }}{% endraw %}-build-node-example-app-
      - name: Install Bunch of Things
        run: |-
          npm install
```

위 yaml은 저희가 구현한 Cache Action의 Post Action을 통해 지정된 경로 (위의 예시의 경우  `~/.npm`)를 key와 같은 포맷의 이름으로 압축하여 (위의 예시의 경우  `Linux-build-node-example-app-master-0123456789abcdef.tar.gz`) `/cache` 디렉토리 아래에 저장합니다. Post Action은 약 60줄 정도의 Typescript 코드로 구현할 수 있었습니다.

### 4. 나중에 CI가 재실행되면 파일 시스템에서 캐시를 복원해옵니다.

이제 복원하는 일만 남았습니다. 간단하게 구현하면 위의 저장 단계에서 저장한 대로 파일을 불러오면 끝나기는 합니다. 하지만 저희 팀은 `actions/cache` 와 비슷하게 **dependency가 달라져 Lockfile의 hash가 달라져도** 캐시의 도움을 받을 수 있으면 좋겠다고 생각했습니다. 그래서 `restore-keys` 라는 개념을 같이 사용하게 되었습니다. 원리는 다음과 같습니다.

1. 다음과 같은 상황을 가정합시다.
   1. Lockfile A: a, b, c 라는 dependency가 설치되도록 기술됨
   2. Lockfile B: a, b, c, d라는 dependency가 설치되도록 기술됨
2. Hash(Lockfile A)에 해당하는 캐시 엔트리는 존재하나, Hash(Lockfile B) 에 해당하는 캐시 엔트리가 없음
3. Prefix를 공유하는 Lockfile A의 캐시 엔트리를 불러옴
4. Dependency d만 설치하면 됨!

그래서 restore-key 관련 로직을 추가하여 파일 시스템에서 캐시를 복원해오도록 했습니다. 로직은 간단합니다. prefix를 공유하는 파일 중 가장 최신의 파일을 불러오도록 했습니다. 이 작업도 약 60줄 정도의 Typescript 코드로 구현할 수 있었습니다.



# 이야기를 마치며

지금까지 사내 CI 도구를 Jenkins에서 Github Actions로 옮기는 과정에 대해 다루어 보았습니다. Jenkins에서 Github Actions로 CI 도구를 옮긴 뒤의 후회는 없으며, 오히려 더 좋아진 부분이 많다고 생각합니다. 그 이유는 아래와 같습니다.

1. 쉬운 yaml syntax로 개발자들의 CI에 대한 부담이 확연히 줄었습니다.
2. Secret 관리나 Build Cache를 만드는 등의 일부 DevOps 작업이 있었지만, Jenkins에 비해 관리가 용이합니다.
   - 특히, Secret 관리를 개발자가 직접 안전하게 할 수 있다는 점이 좋습니다.
   - 또한, Docker Container를 이용하여 동일한 CI 환경을 제공할 수 있어 DevOps가 지원하기 편합니다.
3. Github Integration이 잘 되어 있고 쉽습니다. Git Repository에 필요한 작업을 개발자가 octokit과 git command를 이용하여 쉽게 할 수 있습니다.

사내 Git 관리 도구로 Github를 사용하고 있다면, Github Actions를 한 번 쯤 사용해 보는 건 어떨까 하는 추천을 하며 이 글을 마칩니다.

# References

[1] [https://github.com/actions/cache](https://github.com/actions/cache)

[2] [https://aws.amazon.com/ko/efs/pricing/](https://aws.amazon.com/ko/efs/pricing/)

[3] [https://github.com/actions/cache#implementation-examples](https://github.com/actions/cache#implementation-examples)


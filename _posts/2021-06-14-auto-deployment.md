---
layout: post
date: 2021-06-14
title: Pull Requests를 Merge 하면 자동으로 배포하기
author: hudson
tags: continuous-delivery github-actions
excerpt: Pull Requests를 Merge하면 자동으로 배포가 되도록 시스템을 구성하기까지의 고민을 공유합니다.
---

하이퍼커넥트에는 마이크로서비스를 몇 번의 클릭만으로 배포할 수 있는, Spinnaker 기반의 배포 파이프라인이 구축되어 있습니다. (관련 글: [Kubernetes에 Microservice 배포하기 1편 - 클릭 몇 번으로 배포 시스템 만들기](https://hyperconnect.github.io/2020/06/13/microsrv-deploy-1.html), [2편 - Pipeline 복제하기](https://hyperconnect.github.io/2020/07/04/microsrv-deploy-2.html)) 
다만 개발팀마다 원하는 배포 전략이 다르기 때문에, 배포를 트리거하는 부분은 개발팀에서 정할 수 있게 되어 있습니다. 
저희 팀에서는 개발자가 수동으로 Spinnaker로 접속해서 배포를 진행하고 있었습니다. 

1. **코드 Merge**: master 브랜치에서 새로운 브랜치를 만들어 작업합니다. 
작업이 완료되면 Pull Requests를 생성합니다. 
CI Test가 모두 통과하고, 동료의 Approve를 받으면 master 브랜치로 Merge 합니다.
2. **GitHub Release & Git Tag 생성**: 배포 이력을 관리하기 위해 배포하기 전 Git Tag를 설정합니다. 
Semantic Versioning으로 GitHub 저장소에서 Release를 생성하여 Git Tag를 만듭니다.
3. **배포 시작**: Spinnaker에 접속하여 개발 서버 배포 파이프라인 실행 버튼을 누르고, 빌드 파라미터로는 위에서 추가한 태그를 입력한 후 확인 버튼을 누릅니다. 
프로덕션 서버 배포 파이프라인에도 이를 반복합니다.
4. **배포 파이프라인 작동**: 배포 파이프라인에 따라 Docker Image를 생성하고, Kubernates Deployment가 업데이트되며, 곧 새로운 코드가 배포됩니다.

# 기존 배포 프로세스의 문제점

배포 프로세스를 운영하면서 사람의 실수로부터 오는 몇 가지 이슈가 있었습니다. 

1. **잘못된 Git Tag 생성**: Release 버전을 입력할 때 수동으로 올린 버전을 입력해야 합니다. 
이때 5.2.0 버전의 다음 버전을 5.33.0 버전으로 입력하는 실수를 합니다. 
오타를 내서 지키기로 약속한 Git Tag 네이밍 규칙을 깨트리기도 합니다.
2. **실수로 이전 버전 배포**: Spinnaker 파이프라인에서 배포할 때 입력하는 버전 파라미터에 잘못된 Git Tag 버전을 입력합니다. 
개발자가 의도한 배포 버전은 5.33.0 버전인데, 실수로 숫자 하나를 빠트려 한참 이전 버전인 5.3.0 버전을 배포하는 실수를 합니다.
3. **서버 간 버전의 불일치**: 개발 서버와 프로덕션 서버 모두 최신 버전을 바라보고 있어야 하나, 배포하는 개발자가 실수로 한 곳의 서버에만 배포를 진행합니다.
다음에 배포하는 개발자는 서버 간의 버전이 다른 것을 보고, 해당 스택에 배포하기를 주저하게 됩니다. 
QA 팀 등 유관부서에서 테스트를 진행할 때, 특정 서버에서만 기능이 다르게 동작하여 혼란을 줍니다.
4. **Git 저장소와 서버 배포 버전의 불일치**: Merge만 해 놓고 배포를 잊어버려서 배포하지 않는 경우가 생깁니다. 
다음에 배포를 진행하는 개발자는 한 번에 두 개의 변경 사항을 배포하게 됩니다.
**많은 변경 사항을 포함한 배포는 장애 발생 시 원인 파악이 어렵습니다.**

이러한 문제점들은 현재의 배포 프로세스가 사람의 수작업에 의존하기 때문에 발생하는 문제점입니다.
이제 문제점을 파악했으니 하나씩 차근차근 개선해 나가겠습니다.

# 배포 프로세스의 개선 Phase 1: GitHub Release 자동 생성하기

어떤 소스 코드의 버전이 배포되었는지를 기록하기 위해, 프로덕션에 배포하기 전 Semantic Versioning에 맞춰 Release를 생성하고 있습니다.
이전에는 수동으로 이 작업을 진행하고 있었습니다.
master 브랜치에 Merge 되었을 때 자동으로 GitHub Release를 생성하여 Git Tag를 만드는 GitHub Actions를 만들어 적용하였습니다.
GitHub에서 제공하는 [`actions/create-release@v1`](https://github.com/actions/create-release)을 활용하여 손쉽게 적용할 수 있었습니다.

수동으로 진행하던 프로세스 중 일부를 자동화하니 배포가 한결 쉬워졌습니다.
하지만 배포 자체는 여전히 수동으로 진행하고 있었습니다.
배포를 완전 자동화 할 수 있는 방안을 생각해보기 시작했습니다.

# 배포 프로세스의 개선 Phase 2: Pull Requests를 Merge 하면 배포되게 만들기

이 포스트의 핵심입니다.

Spinnaker에는 Webhook으로 파이프라인을 트리거할 수 있습니다.
이 기능을 이용하면 쉽게 배포를 진행할 수 있습니다. 
하지만 수동으로 배포하는 것을 자동화하는 것은 왠지 모르게 두렵습니다. 
이럴 때는 두려운 이유를 글로 풀어서 써 보면 두려움을 해소하고 해결책을 찾을 수 있습니다.

## Concern 1: 자동 배포의 동작을 개발자가 제어할 수 있을까?

저희 팀에서는 Lightweight Branching Model을 채택하여 사용하고 있습니다. 
develop 브랜치를 사용하지 않고 master 브랜치만 사용합니다. 
변경 사항은 master 브랜치를 base로 하여 새로운 브랜치를 만들어 작업합니다. 
master 브랜치에 merge가 되면 개발 서버와 프로덕션 서버에 배포합니다.

개발 서버는 특정 피처를 테스트하기 위해 간혹 오랫동안 점유하여 사용합니다.
이 경우 개발 서버에는 새로운 버전이 배포되지 않아야 합니다. 
기존의 수동 프로세스에서는 개발 서버와 프로덕션 서버에 손으로 배포하기 때문에, 이러한 예외 상황에 유연하게 대처할 수 있었습니다.

자동 배포를 진행하게 되면 자동으로 모든 스택의 배포 파이프라인을 모두 트리거하기 때문에, 유연성이 떨어지게 되었습니다. 
따라서 이를 제어할 수 있는 여러 가지 방법들을 검토해 보았습니다.

1. 가장 먼저 Settings → Actions → Actions permissions에서 일부 Action을 끄는 방법을 검토해 보았습니다. 
하지만 이 방법은 저장소 전역으로 설정이 들어가기도 하고, 매번 켜고 끄는 것을 까먹을 리스크가 있을 것으로 보였습니다.

    ![]({{"/assets/2021-06-14-auto-deployment/auto-deployment-03.png"}})

2. [GitHub Actions: Environments, environment protection rules and environment secrets (beta)](https://github.blog/changelog/2020-12-15-github-actions-environments-environment-protection-rules-and-environment-secrets-beta/) 기능을 이용하여 Manual approval을 적용하는 것을 검토해 보았습니다. 
하지만 저희는 GitHub Enterprise를 이용하고 있고, GitHub Enterprise에서는 해당 기능이 아직 지원되지 않아 해당 방법을 사용할 수 없었습니다.
3. Label을 이용하여, Pull Requests가 Merge 될 때 배포 동작을 제어하는 것을 검토해 보았습니다.
    - 기본적으로는 Merge 될 때 모든 환경에 자동 배포되는 것을 기본으로 합니다.
    - 자동 배포를 막고 싶을 때, `no-deploy-to-qa`, `no-deploy-to-prod` 라벨을 붙입니다.

        ![]({{"/assets/2021-06-14-auto-deployment/auto-deployment-04.png"}})

    - [GitHub API 중 List pull requests associated with a commit](https://docs.github.com/en/enterprise-server@3.0/rest/reference/repos#list-pull-requests-associated-with-a-commit)을 이용하면, 가장 최근에 Merge 된 Pull Requests의 Label 들을 가져올 수 있습니다.

    Pull Requests의 Label을 이용하여 스택별로 자동 배포 여부를 관리하면, 직관적으로 배포 여부를 결정할 수 있을 뿐 아니라, 동료도 코드 리뷰를 진행하면서 배포 여부를 함께 검토할 수 있습니다.
    자동 배포에 대한 히스토리도 자연스럽게 남게 됩니다.
    따라서 이 방법으로 자동 배포의 동작을 제어하게 되었습니다.

## Concern 2: 검증되지 않은 변경 사항이 배포되면 어떡하지?

자동 배포가 적용된다는 것은, 모든 master 브랜치에 푸쉬되는 커밋은 자동으로 배포된다는 의미입니다. 
이 상황에서는 검증되지 않은 커밋이 master 브랜치에 Merge 되면 개발 환경뿐 아니라 실제 유저가 사용하는 프로덕션 환경에도 영향을 미치게 됩니다.

이러한 잠재적인 이슈를 막기 위하여, Settings → Branches → master에서, master 브랜치를 Protected branch로 설정한 후, 모든 테스트가 통과하고 동료의 Approve가 1개 이상 있어야 merge 할 수 있도록 설정하였습니다. 

![]({{"/assets/2021-06-14-auto-deployment/auto-deployment-05.png"}})

위와 같이 설정하면 검증되지 않은 변경 사항이 배포되는 것을 막을 수 있습니다.

## Concern 3: 동시에 여러 Merge가 되면 어떡하지?

동시에 Merge가 여러 번 진행되면, 파이프라인이 동시에 실행되어서 뭔가 꼬일 수 있는 위험이 있습니다. 
다행히 Spinnaker에는 같은 파이프라인이 동시에 실행하는 것을 막을 수 있는 기능이 있습니다. 

![]({{"/assets/2021-06-14-auto-deployment/auto-deployment-06.png"}})

이 옵션을 사용했을 때 실제로 동시에 파이프라인이 실행되는 것을 막아주는지 실험해보았고, 예상한 대로 한 번에 하나의 파이프라인만 실행되는 것을 확인할 수 있었습니다.

![]({{"/assets/2021-06-14-auto-deployment/auto-deployment-07.png"}})


## Concern 4: 보안상 이슈가 있지는 않을까?

Spinnaker CD 파이프라인을 Webhook으로 트리거하게 되면, 외부에서 파이프라인을 트리거할 수 있는 보안 이슈가 있을 수 있습니다. 
이를 위하여, Spinnaker의 웹훅 기능에는 웹훅의 Payload에 특정 값이 입력되어야 파이프라인을 실행시키는 보안 기능이 있습니다. 
이를 이용하면 해당 키와 값을 알아야만 배포할 수 있게 됩니다. 
물론 해당 키와 값은 절대 외부에 유출되면 안 됩니다.

![]({{"/assets/2021-06-14-auto-deployment/auto-deployment-08.png"}})

모든 두려움의 원인을 찾아 해결했습니다.
위의 검토대로 자동 배포를 실전으로 적용해 보았습니다.

## DevOps의 도움 받기

사실 이러한 자동 배포 기능은 저희 팀에서만 사용하기에는 아깝습니다. 
DevOps 팀에 지원을 요청하였고, 곧 전사적으로 사용할 수 있도록 필요한 기능들을 작업해 주셨습니다.

- Spinnaker 파이프라인을 찍어내는 서비스에 적절한 Payload Constraints를 자동으로 추가해 주는 기능을 추가해 주셨습니다.
- Spinnaker로 배포를 시작하는 웹훅을 호출해주는 GitHub Actions를 작업해 주셨습니다. 개발팀은 복잡한 것을 알 필요 없이 이 Actions를 가져다 사용하면 됩니다.

## 자동 배포 Step 추가

이제 위에서 결정한 내용을 파이프라인으로 옮기면 됩니다. 
고민한 것들에 비하여 실제 코드의 양은 그리 길지 않습니다.

```yaml
{% raw %}- id: check_pr_labels
  name: Check PR Labels
  shell: bash
  run: |
    # Pull Requests에 달린 Label 목록을 가져온다.
    pull_request_labels=$(curl \
      --fail \
      -H "Accept: application/vnd.github.groot-preview+json" \
      -H "Authorization: Bearer ${{ secrets.GITHUB_TOKEN }}" \
      "${{ github.api_url }}/repos/${{ github.repository }}/commits/${{ github.sha }}/pulls" \
    | jq -r ".[0].labels[].name")

    # no-deploy-to-qa Label이 붙어 있는지 확인한다.
    if echo "$pull_request_labels" | grep -q '^no-deploy-to-qa$' ; then
      echo "::set-output name=DEPLOY_TO_QA::false"
    fi

    # no-deploy-to-prod Label이 붙어 있는지 확인한다.
    if echo "$pull_request_labels" | grep -q '^no-deploy-to-prod$' ; then
      echo "::set-output name=DEPLOY_TO_PROD::false"
    fi

- id: deploy_to_qa
  name: Deploy To QA
  if: ${{ steps.check_pr_labels.outputs.DEPLOY_TO_QA != 'false' }}
  uses: hyper-actions/spinnaker-trigger@v1
  with:
    (Actions를 실행시키는 데 필요한 여러 가지 파라미터)

- id: deploy_to_prod
  name: Deploy To Prod
  if: ${{ steps.check_pr_labels.outputs.DEPLOY_TO_PROD != 'false' }}
  uses: hyper-actions/spinnaker-trigger@v1
  with:
    (Actions를 실행시키는 데 필요한 여러 가지 파라미터){% endraw %}
```

위의 Actions를 간략하게 설명해 보았습니다.

1. Step `Check PR Labels`
  * 가장 최근에 Merge 된 Pull Requests에 달린 모든 Label을 가져옵니다.
  * `no-deploy-to-qa` Label이 있으면 `DEPLOY_TO_QA` 변수를 `false`로 설정합니다.
  * 마찬가지로 `no-deploy-to-prod` Label이 있으면 `DEPLOY_TO_PROD` 변수를 `false`로 설정합니다.
2. Step `Deploy To QA`
  * `DEPLOY_TO_QA` 변수가 `false`가 아닐 때만 실행됩니다. 즉 해당 Label이 없을 때만 자동으로 배포합니다.
3. Step `Deploy To Prod`
  * `DEPLOY_TO_PROD` 변수가 `false`가 아닐 때만 실행됩니다. 즉 해당 Label이 없을 때만 자동으로 배포합니다.

수동 배포 프로세스의 문제점을 모두 해결할 수 있도록 자동 배포 프로세스를 구축하였습니다.
이제 아래의 Merge Pull Requests 버튼을 누르면 프로덕션을 포함한 모든 스택에 배포가 됩니다!

![]({{"/assets/2021-06-14-auto-deployment/auto-deployment-09.png"}})

# 결론

- Pull Requests의 Merge 버튼으로 자동 배포할 수 있는 파이프라인을 만들었습니다. 
배포를 진행하다가 실수할 여지를 제거했습니다.
개발자가 수동으로 배포할 때보다 훨씬 더 안정되었습니다.
- 무엇보다도 배포가 더는 무섭고 귀찮지 않게 되었습니다. 
큰 변경 사항을 한 번에 배포하는 대신, 작은 변경 사항을 여러 번 배포하는 팀 문화를 만드는 데 큰 도움이 되었습니다.

또한, 자동 배포를 진행하기로 하기까지 간접적으로 도움이 되었던 것들입니다.

- 테스트 커버리지가 높아서, 테스트가 통과하면 웬만해서는 큰 이슈가 없다는 것을 확신할 수 있습니다. 
동료의 꼼꼼한 코드리뷰를 거치고 나면 바로 프로덕션에 배포해도 괜찮을 만큼의 확신을 가질 수 있습니다.
- 데이터베이스 마이그레이션 툴로 Django Migrations를 사용하고 있습니다. 
소스 코드가 배포되면서 이에 맞게 데이터베이스의 스키마도 자동으로 변경됩니다. 
배포 시 수동으로 데이터베이스 스키마를 변경하는 애플리케이션이라면 자동 배포를 적용하는 것이 알맞지 않을 수 있습니다.
- 여러 가지 중요 메트릭과 오류에 대해 Alert이 잘 걸려 있습니다. 
시스템에 문제가 생기면 빠르게 Alert이 울리기 때문에 무언가 잘못되었다는 것을 빠르게 인지하고 대응할 수 있습니다.
- 뭔가 잘못된 배포가 있었을 때 빠르게 롤백할 수 있도록, 롤백 가이드 문서를 만들고 주기적으로 업데이트하며, 주기적으로 팀원들에게 알리고 있습니다. 
이로써 팀원 모두가 배포가 잘못되었을 때 즉각적으로 롤백할 수 있게 대응할 수 있습니다.
- 소스 코드에서 Docker 이미지를 만들고 Kubernates 클러스터로 배포해 주는 Spinnaker 파이프라인이 기존에 구축되어 있었기 때문에, 이 부분에 대해서는 신경 쓸 필요가 없었습니다.

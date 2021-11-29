---
layout: post
date: 2021-11-29
title: 모두의 Github Actions (feat. Github Enterprise) 2편 - 공용 CI 머신에서 Secret 관리하기
author: hong
tags: github-actions github-enterprise continuous-integration
excerpt: Github Enterprise에서 Github Actions를 사용할 때 보안 문제 없이 Secret에 접근하는 방법에 대해 소개합니다.
last_modified_at: 2021-11-29
---

지난 글에서는 Jenkins에서 돌아가던 CI/CD 작업을 Github Actions로 옮긴 이유와, 개발자가 고민 없이 Actions를 쓰게 하기 위해 Actions Runner를 사용하는 패턴을 만드는 과정에 대해 소개했습니다.
지난 글의 핵심은 컨테이너를 이용하여 언제나 격리된 환경을 제공하면 관리가 용이한 CI 환경을 만들 수 있다는 것이었습니다.

이번 글에서는 개발자들이 CI를 하며 보안 문제는 없으면서 알아서 잘 딱 깔끔하고 센스있게 되면 좋겠다고 생각하는 Secret Management 를 Actions로 추상화하여 개발자가 디테일을 몰라도 알아서 다 잘 되게끔 하는 과정에 대해 소개합니다. 



# Secrets... Secrets... Secrets...!

CI 작업 중에 다른 서비스와 연동되는 일들을 하는 경우가 있습니다. 예를 들어 React로 열심히 만든 웹 페이지를 빌드해서 S3로 올리고 싶은 상황이나 Pull Request를 머지하면 알아서 Spinnaker를 trigger 해서 배포하는[1] 상황이 있겠네요. 이러한 상황에 공통적으로 필요한 것이 바로 Token이나 Credential입니다. 통칭 Secret이라고 불리는 이것들은 단어 그대로 *비밀스럽게* 관리가 되어야 합니다. 비밀스럽게 관리가 된다는 것은 다음을 뜻합니다.

1. 내가 올린 비밀을 암호화하여 관리하고 있어야 합니다.
2. 코드에 박혀있으면 안 됩니다. 유출됩니다.
3. 마스킹이 잘 되어야 합니다. 예를 들어, 실수로 workflow에 `echo $SECRET` 을 했을 때에도 가려져서 문제가 없어야 합니다.
4. 유출 된다고 쳐도 큰 문제가 없게끔 주기적으로 교체(rotate) 되어야 합니다.

다행히도, Github Actions에서는 Github Secrets라는 것을 지원합니다. Github Secret은 libsodium sealed box를 통해 암호화되어 관리됩니다.[2]  이 Secret은 Repository 단위로 생성할 수도 있고, Organization의 모든 Repository에 Secret이 뿌려지도록 Organization-level 로도 생성할 수도 있습니다.

![Secrets]({{"/assets/2021-11-29-github-actions-for-everyone-2/secrets.png"}})

이렇게 만들어진 Github Secret은 쉽게 환경변수나 파일의 형태 등으로 주입할 수 있습니다. 아래는 Github Secret을 `{% raw %}${{ secrets.XXX }}{% endraw %}` 형태로 참조하여 간단하게 환경변수로 주입하는 예시입니다.

```yaml
name: workflow
env:
  SOME_SECRET: {% raw %}${{ secrets.SOME_SECRET }}{% endraw %}
```

Secret은 아래와 같이 workflow log에서는 mask되어 보입니다.

![Masked Secrets]({{"/assets/2021-11-29-github-actions-for-everyone-2/masked.png"}})

유출되었다면 secret을 Github에 업로드 하는 것 만으로도 rotate가 됩니다. 좋습니다! 이제 모든 Secret을 별도의 하드코딩 없이 Github Secret 형태로 관리하면 되겠네요!



# 멈춰!

개발자는 당황스럽습니다.

1. 본인 조직에 있는 Repository만 해도 수십개에 달합니다. **귀찮습니다!**
2. 기존에 Vault로 관리되고 있던 Secret을 다 옮길 생각을 하니 까마득합니다.
3. 분명 AWS에서는 Credential의 수명을 짧게 가져가라고 했던 거 같은데... 개발자가 인간 Credential Rotator가 되어야 할까요? 아니면 장수하는 Credential을 그대로 두어야 하나요?

DevOps는 난감해집니다.

1. 개발자가 아무리 귀찮다고 해도 모든 Secret을 Organization Secret으로 뿌릴 수는 없는 판입니다.
2. Vault에 조직별로 관리되고 있는 Secret이 있다고 했습니다. 그러면 Vault에라도 접근하게 해 주면 좋을텐데, *공용* Runner Pool에서 어떻게 조직을 구분할 수 있을까요?
3. CI용으로 AWS IAM User를 발급하면 사람은 Credential Rotate를 해야한다는 사실을 무조건 까먹습니다!



# Vault를 이용하여 해결해보기

Vault는 Hashicorp에서 만든 Secret Management Tool입니다. 다양한 유형의 Secret과 Authentication Method를 편하고 안전하게 사용할 수 있는 가이드라인을 제시합니다. 이 글에서 Vault의 특징에 관한 설명은 길게 하지 않겠습니다. Vault가 뭔지 궁금하신 분들은 [3] 을 참조하시면 됩니다. Vault에서 Secret에 접근하는 과정은 다음과 같은 흐름으로 볼 수 있습니다.

1. Vault에 다양한 방법으로 로그인. (LDAP, AWS IAM 등...)
2. Vault Token 부여
3. Token을 이용하여 Secret에 접근.

Vault에서는 Vault Policy를 통해 로그인 한 방법(Auth Backend)에 따라 다른 Policy를 부착하여 특정 Secret에 접근하거나 접근하지 못 하게 할 수 있습니다. 이제 이 사실을 바탕으로, 조직별로 필요한 Secret에만 접근할 수 있도록 하는 설정을 해 봅시다.

### Step 1. 각 Repository가 어떤 조직의 Repository인지 마킹하기

Github Repository에는 Topic이라는 라벨과 같은 기능이 존재합니다. 토픽 기준으로 Repository를 필터할 수 있는 Github API가 있어서, 전사적으로  Repository의 Topic에 주인 표시를 요청했습니다.

![Repo by Topic]({{"/assets/2021-11-29-github-actions-for-everyone-2/topic.png"}})

### Step 2. 조직별로 다른 방법으로 Vault에 로그인하기

조직별로 다른 Auth Backend를 생성하여, 그 Auth Backend를 통해 로그인 할 수 있도록 구성했습니다. 이렇게 하면 조직별로 역할이 다르게 부여된 Token을 얻을 수 있게 됩니다. 이 단계에서는 Approle Auth Backend Role을 사용했습니다. Approle Auth 방식은 RoleID와 RoleID에 일시적으로 부여된 SecretID를 통해 Vault에 로그인하는 일종의 ID/PW 방식과 비슷한 방식입니다. Approle Auth Backend Role은 아래와 같이 사용했습니다.

1. 먼저 Repository의 topic을 확인하여 Repository 주인을 찾습니다.
2. Repository 주인과 매칭되는 Approle Auth Backend Role을 찾습니다.
3. 사내 CI 담당 Django 서버가 (2)에서 찾은 Auth Backend Role의 SecretID를 주기적으로 새로 발급해 주고, Github Secrets API를 통해 Github Secrets로 RoleID와 SecretID로 등록해줍니다.
4. Github Secret의 RoleID와 SecretID를 통해 Vault에 로그인하면 조직별로 Policy가 다른 Token을 확보할 수 있습니다!

### Step 3. Secret에 접근하기

Vault Token이 있으니 이제 다 됐습니다. 공용 액션 이미지에 vault-cli가 설치되어 있고, 이를 통해 원하는 secret을 확보하는 것은 어렵지 않습니다!



# Vault를 이용해서 AWS도 Github Actions에서 쓰기

특이한 점은, AWS Credential를 얻을 수 있는 Vault Secret Engine이 존재해서 vault token을 통해 IAM Role Assume을 할 수 있다는 것입니다. 왠지 Vault를 이용하여 Github Actions에서 AWS도 안전하게 접근할 수 있을 것 같습니다. 그 방법은 아래와 같습니다.

### Step 1. Vault에서 IAM Assume 할 수 있는 AWS Secret Backend 만들기

Vault에서 AWS Secret Backend를 조직별로 찍어냅니다. 테라폼으로 쉽게 찍어낼 수 있습니다.

```terraform
resource "vault_aws_secret_backend" "aws" {}

resource "vault_aws_secret_backend_role" "role" {
    for_each        = local.policy_by_role
    backend         = vault_aws_secret_backend.aws.path
    name            = "role-${each.key}"
    credential_type = "assumed_role"

    role_arns       = ["arn:aws:iam::xxxxxxxxxxxx:role/role-vault-team-${each.key}"]
}
```

이렇게 하면  Vault에서 read operation을 통해 `role-vault-team-devops` 와 같은 IAM Role에 Assume할 수 있는 Secret Backend가 아래 그림과 같이 생깁니다.

![Secret Backend]({{"/assets/2021-11-29-github-actions-for-everyone-2/aws-secret-backend.png"}})



### Step 2. AWS 계정별로, 하이퍼커넥트 조직별로 IAM Role 찍어내기

위에서 Secret Backend를 만들 때 같이 만든 IAM Role (예: `role-vault-team-devops` ) 는 중앙 계정에서 다른 계정으로 IAM Role Assume 하기 위한 1차 Role로 사용합니다. 1차 Role은 중앙 계정에 조직 수 만큼 있으며, `AssumeRole` 만 할 수 있도록 권한을 부여했습니다. 그리고 사용 중인 모든 AWS 계정에서 모든 조직에 대한 2차 Role을 만들어냅니다. 예를 들어, DevOps 팀의 Azar라는 AWS 계정에서의 2차 Role은 `role-azar-devops` 와 같이 만듭니다. 그리고 2차 Role을 Assume할 수 있는 Trusted Entity로 1차 Role을 설정합니다. 예를 들어 `role-azar-devops` 의 trusted entity 는  `role-vault-team-devops` 가 되는 것입니다.

![2-Level Assume Role]({{"/assets/2021-11-29-github-actions-for-everyone-2/2-level-assume.png"}})

수백개에 달하는 이 Role은 마찬가지로 Terraform으로 찍어냈습니다. Terraform 0.12부터 들어간 `for` 구문과  `for_each` 구문을 통해 어렵지 않게 찍어낼 수 있었습니다. 먼저, 조직 => AWS IAM Policy로 이어지는 Map을 받으면 `for_each` 를 통해 조직별 2차 Role을 찍어주는 Terraform Module을 만듭니다.

```
data "aws_iam_policy_document" "mgmt_user_assume_role_policy" {
  for_each = var.iam_policy_by_role
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type = "AWS"
      // 1차 role은 2차 role을 assume 할 수 있다.
      identifiers = ["arn:aws:iam::xxxxxxxxxxxx:role/role-vault-team-${each.key}"]
    }
  }
}

resource "aws_iam_role" "user-role" {
  for_each = var.iam_policy_by_role
  name = "role-${var.aws_profile_identifier}-${each.key}"
  assume_role_policy = lookup(data.aws_iam_policy_document.user_assume_role_policy, each.key, {}).json
  dynamic "inline_policy" {
    // empty inline policy가 안 됩니다 ㅠㅠ
    for_each = length(each.value) > 0 ? [1]: []
    content {
      name = each.key
      policy = jsonencode({
        Version = "2012-10-17"
        Statement = [for s in each.value : jsondecode(s)]
      })
    }
  }
}
```



해당 Module에 `providers` 블록을 통해 AWS provider만 아래와 같이 주입시키면 수백개의 AWS IAM Role이 바로 만들어집니다.

```
provider "aws" {
  profile = "azar"
  alias = "azar"
  // e.g. ap-northeast-2...
  region = "xxx"
}

module "azar" {
  source = "./role-by-account"
  providers = {
      aws = aws.azar
  }
  aws_profile_identifier = "azar"
  iam_policy_by_infrarole = tomap({
    for k, r in local.teams:
      k => concat(
        lookup(r, "azar", []),
        lookup(r, "_all", [])
      )
  })
}
```



### Step 3. 준비 완료! AWS 서비스 쓰기!

이제 개발자는 `aws sts assume-role` 커맨드를 통해 정해진 role을 assume하고, AWS 서비스도 마음껏 사용할 수 있습니다! 와 그럼 이제 준비가 다 됐네요!



# 하지만 아직 개발자는 귀찮다.

아직 풀리지 않은 문제들이 있습니다. 그것은 바로 개발자들에게는 **이 모든 과정이 별로 알고싶지 않고 귀찮다는 것입니다!**

1. Vault 로그인 할 때 실수라도 하면 shell 커맨드를 다 디버깅하고 있어야 합니다 🤦
2. 내가 굳이 Vault read 안 해도 우리 팀이 쓰는 secret은 환경변수에 등록되었으면 좋겠어요. 😡
3. 사내 AWS 계정이 수 십 개인데, 여기에 다 STS Assume Role을 하라구요? 😵

개발자 입장에서는 "Vault에 로그인하고 팀 공용 Secret을 불러와 줘.", "AWS에 로그인 해 줘." 정도로만 이 모든 것을 수행하고 싶지, AppRole이 어떻고 AWS 1차 2차 Role이 어떻고는 별로 궁금하지 않습니다! 이 문제는 어떻게 해결할 수 있을까요?



# Github Action에 담긴 추상화의 미학

Github Actions의 Workflow에는 *알아서 잘 딱 깔끔하고 센스있게*  복잡한 CI 작업을 처리해 줄 수 있도록 Action이라는 것을 도입했습니다. Action은 workflow로부터 parameter를 받고, parameter 기반으로 복잡한 작업을 처리하고, 그 결과를 workflow에게 돌려주는 일종의 함수와 같은 역할을 합니다. Workflow를 작성하는 입장에서는 Action 내부가 어떻게 구현 되어 있는지 알 필요 없이 Action을 **호출**하는 작업만 해 주면 됩니다. 아래는 Github에서 기본적으로 제공하고 있는 `actions/checkout` 과 `actions/setup-node` Action의 예시입니다.

```
name: pr
on:
  issue_comment:
    types: [ created ]
jobs:
  some_job:
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v2
      - name: Setup Node
        uses: actions/setup-node@v1
        with:
          node-version: '12'
```

첫 번째 step은 `actions/checkout` 의 `v2` 태그를 참조하여 Action을 실행하라는 의미입니다. [링크](https://github.com/actions/checkout) 와 같이 token, ssh-key, ssh-strict 등 여러 parameter를 받고 복잡한 과정을 거쳐 checkout 하는 action입니다. 코드만 해도 typescript 수 백 줄 이상에 달하지만, 개발자는 그런 것 알 필요 없이 위의 `uses: actions/checkout@v2` 한 줄로 repository를 checkout 할 수 있다는 사실만 알면 됩니다.

그 아래에 있는 setup-node action의 경우 단 4줄로 Node 12를 CI 환경에 설치해주는 역할을 합니다. 내부적으로는 시스템 아키텍쳐 확인, 노드 버전 다운로드, Node 캐싱 등이 들어있습니다. 그러나 당장 개발자가 CI 환경에서 Node 12를 쓰는 데에는 별로 알고 싶지 않고, 알지 않아도 되는 정보입니다!



# Secret Operation을 Action으로 추상화하기

DevOps가 Action을 이용하여 Vault Operation을 추상화 해 주면, 개발자 입장에서는 내부 Vault Auth Backend가 어떻고 하는 정보를 알 필요 없이 Vault를 사용할 수 있습니다. Action은 Docker Image, Shell Script(Composite Run Steps), Javascript 이렇게 세 가지 형태로 작성할 수 있습니다. 하이퍼커넥트에서 Vault Operation 관련한 작업은 Typescript로 작성하고 [ncc](https://github.com/vercel/ncc)를 이용해 Javascript로 transpile하여 사용하였습니다.

하이퍼커넥트에서 만든 Vault Operation Actions를 실행하면 아래와 같은 일들이 돌아갑니다. (Action에 대한 구체적인 코드 첨부는 하지 않습니다. Action 만드는 법이 궁금하다면 [4]를 참조해주세요.)

1. Secret을 이용하여 AppRole 로그인
2. 조직 공용 Secret을 읽고 환경변수로 export
3. CI가 종료될 때 사용한 Vault Token을 삭제

이 모든 작업의 코드 줄 숫자는 150줄이 약간 넘어가는 수준입니다. 개발자는 150줄의 코드에 대해서도, Vault 내부 사정에 대해서도 알 필요 없이 단 5줄로 vault에 로그인하여 공용 secret을 얻어오는 것 까지 수행할 수 있습니다.

비슷하게, AWS IAM Role Assume을 하는 과정도 Action도 만들었습니다. 아래와 같이 단 4줄로 수십 개의 AWS Credential을 모두 얻어올 수 있습니다.

```yaml
jobs:
  some_job:
    steps:
      - name: Vault Login
        uses: hyper-actions/login-vault@master
        with:
          role-id: {% raw %}${{ secrets.DEVOPS_VAULT_ROLE_ID }}{% endraw %}
          secret-id: {% raw %}${{ secrets.DEVOPS_VAULT_SECRET_ID }}{% endraw %}
      - name: IAM Role Assume Action #assume role
        uses: hyper-actions/iam-assume-role@master
        with:
          infra-role: devops
```



# 결론

이번 글에서는 1편에서 소개드렸던 공용 Github Actions Runner 패턴을 운영할 때 보안 문제 없이 Secret을 관리하는 방법에 대해 다뤘습니다. 또한 이러한 Secret들을 받아올 때 개발자들이 내부 사정에 대해 고민 없이 받아올 수 있는 방법에 대해 다뤘습니다. 하이퍼커넥트에서는 Secret을 가져오는 문제를 주기적으로 Rotate되는 Github Secrets와 Vault를 이용해 해결했습니다. 그리고 이 과정을 Github Action을 통해 추상화하여 개발자들이 4~5줄로 원하는 Secret Operation을 할 수 있도록 만들었습니다.

다음 글에서는 Github Actions를 잘 쓰기 위해서 Build Cache를 어떻게 구축했고 어떻게 관리하는지에 관해 다뤄보려고 합니다.



# References

[1] [https://hyperconnect.github.io/2021/06/14/auto-deployment.html](https://hyperconnect.github.io/2021/06/14/auto-deployment.html)

[2] [https://docs.github.com/en/actions/reference/encrypted-secrets](https://docs.github.com/en/actions/reference/encrypted-secrets)

[3] [https://learn.hashicorp.com/tutorials/vault/getting-started-intro?in=vault/getting-started](https://learn.hashicorp.com/tutorials/vault/getting-started-intro?in=vault/getting-started)

[4] [https://docs.github.com/en/actions/creating-actions/about-actions](https://docs.github.com/en/actions/creating-actions/about-actions)

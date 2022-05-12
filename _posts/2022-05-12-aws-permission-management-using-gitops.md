---
layout: post
date: 2022-05-12
title: 개발자의 AWS 권한을 GitOps로 우아하게 관리하는 방법
author: sammie
tags: aws sso vpn gitops permission
excerpt: 많은 개발자가 가지는 많은 권한을 쉽게 관리하고, 개발자가 필요한 권한을 직접 얻을 수 있게 권한 시스템을 설계하고 GitOps 기반 도구를 개발한 과정을 소개합니다.
last_modified_at: 2022-05-12
---

안녕하세요, DevOps 팀의 Sammie입니다. 몇 명의 개발자만 있는 초기 start-up의 권한 관리는 매우 쉽습니다. 단순히 모든 개발자에게 admin 권한을 부여하면 됩니다. 하지만, 회사가 성장하면서 개발자가 늘어나게 되고, 각자에게 맞는 권한이 필요하게 됩니다. 이번 글에서는 개발자의 권한을 편하게 부여하기 위해 GitOps를 도입한 경험을 공유합니다. 특히, 여러 개의 AWS account와 VPC를 사용하는 조직에서 발생하는 권한 관리 문제와, 이를 AWS SSO[[1]](https://aws.amazon.com/single-sign-on/) 및 AWS Client VPN[[2]](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/what-is.html)을 활용해 해결한 방법에 대해서 자세히 소개해보려고 합니다.

기술 소개에 앞서 Hyperconnect에서 현재 사용 중인 도구와 시스템에 대해서 간략하게 공유하고, 이를 만들게 된 계기와 기술을 공유하려고 합니다. 분량 관계상 기술에 대한 자세한 설명이나 GitOps 도구 자체의 구현에 대해서는 생략했으므로 양해 부탁드립니다.

# TL; DR
본격적인 설명에 앞서, 다음 2가지 사례를 통해 현재 gitops 기반 권한 관리가 어떻게 이루어지고 있는지 살펴보겠습니다.

### On-Boarding
어느 봄날, 신규 입사자 Alice가 `azar-api` 팀에 입사했습니다. 그렇다면, 제일 먼저 `azar-api` 팀의 팀장인 Bob은 다음과 같이 PR을 하나 올립니다.
![onboarding]({{"/assets/2022-05-12-aws-permission-management-using-gitops/01-perm-gitops.png"}})

이 PR은 `azar-api` 팀에 속해있는 모든 사람의 목록을 저장한 `azar-api/users.yaml` 파일에 한 줄을 추가합니다.
```yaml
root:
  - Bob    # team leader
  - <팀원1>
  - <팀원2>
  - Alice  # welcome, alice!
```

이 PR은 CODEOWNERS 규칙에 의해 자동으로 DevOps팀에게 리뷰 요청이 전송되고, DevOps engineer의 approve 후 merge 됩니다. Merge 된 이후 자동화 프로세스의 실행이 끝나면, Alice는 `azar-api` 팀이 가지는 모든 AWS account 접근 권한과 VPN 접근 권한을 가지게 됩니다!

### Team Leader Permission
`azar-api` 팀의 leader인 Bob은 작업을 하다 RDS를 삭제해야 할 일이 생겼습니다. 하지만, production의 database를 삭제하는 것은 무섭고 위험한 일이므로, 다른 팀 구성원에게는 권한을 주지 않고 팀장인 본인만 권한을 얻고 싶습니다. 이때, Bob은 다음과 같은 PR을 올릴 수 있습니다.

제일 먼저, RDS를 삭제할 수 있는 권한을 포함하는 policy 파일을 생성합니다. `permission-sets/RDSMasterAcccess.yaml`이라고 하겠습니다.
```yaml
sessionDuration: PT1H
awsManagedPolicies:
  - ViewOnlyAccess 
inlinePolicy: |-
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": "rds:*",
        "Resource": "*"
      }
    ]
  }
```
그다음, AWS 계정의 권한을 정의하는 파일에 위에서 생성한 policy 이름을 추가합니다. 이러한 형식의 파일은 Hyperconnect에서 관리하는 모든 AWS 계정마다 한 개씩 존재하므로 각 계정마다 서로 다른 권한을 부여할 수 있습니다.
```yaml
id: '<account-id>'
roles:
  - name: azar-api
    awsName: AzarProdAzarAPI
  - name: rds-master          # added
    awsName: RDSMasterAccess  # added
```
마지막으로 위에서 정의한 `azar-prod` 계정의 `rds-master` 권한을 Bob에게 부여할 차례입니다. `azar-api/roles.yaml` 파일에 내용을 추가했습니다.
```yaml
- groups: root
  aws-accounts:
    - effect: allow
      accounts: azar-prod
      permissions: azar-api
- users: Bob                   # added
  aws-accounts:                # added
    - effect: allow            # added
      accounts: azar-prod      # added
      permissions: rds-master  # added
```
이제 이 3가지 파일을 변경한 PR을 올립니다. DevOps팀 리뷰 후 master에 merge 되면 Bob은 일반 팀원의 권한인 `AzarProdAzarAPI`와 Bob 전용 권한인 `RDSMasterAccess`를 모두 행사할 수 있습니다!

VPN도 이와 유사한 방법을 통해 팀 또는 개인마다 접근할 수 있는 CIDR를 제한할 수 있고, Hyperconnect의 모든 개발자가 직접 파일을 수정해서 권한을 받을 수 있도록 설계되어 있습니다. 이제 DevOps 팀에서 이 시스템을 설계하게 된 이유와 기술적인 내용에 대해서 조금 더 자세히 설명해보겠습니다.


# Background
Hyperconnect에서는 몇십 개의 AWS 계정과 VPC를 사용하고 있습니다. 이 시스템을 만들기 전에 발생했던, 또는 발생할 뻔했던 귀찮은 상황 몇 개를 먼저 소개해드리겠습니다.

### 신규 입사자
어느 날, Azar API팀에 신규 입사자 Alice가 왔습니다. Azar API팀의 팀장 Bob은 다른 팀원과 동등한 권한을 달라고 요청했습니다.

1. azar-prod와 azar-dev AWS account에 각각 접속해서 Alice IAM user를 만들었습니다. AWS cli를 사용할 수 있도록 access key도 만들었습니다. Private subnet에 존재하는 EC2 instance에도 접근할 수 있도록, 두 계정의 VPC의 VPN instance에 접속해서 Alice의 계정을 만들었습니다.
2. Alice는 AILab과의 협업이 필요해 AILab AWS account와 EC2 instance에 접근이 가능해야 한다는 추가 요청이 왔습니다. ailab AWS account에도 Alice IAM user를 생성했습니다. (그리고 access key도요!)
3. 낯선 환경에서 업무를 하느라 피곤했던 Alice는 그만 본인의 access key와 password를 git에 commit 해버리는 실수를 하고 말았습니다. 전부 access key를 rotate 하고, AWS account 3개의 IAM user의 passowrd를 reset 시켜야 합니다. 물론, VPN instance에도 각각 접속하여 초기화시켜야 합니다.

### New Product!
새 product를 만들기로 했습니다. Azar2라는 신규 프로젝트 용 AWS 계정이 필요하고, 해당 계정에 Alice와 Bob이 권한을 가져야 한다고 요청받았습니다.

1. azar2-dev account를 생성했습니다. 그리고 account에 접속해서 Alice와 Bob의 IAM User를 만들었습니다. access key도 만들어 전달했는데, 실수로 Slack DM을 잘못 보내서 한 사람에게 key 2개를 보냈습니다. 빨리 revoke 시키고 다시 보냈습니다.
2. ML 기술을 사용하는 서비스라 AILab의 팀원 Carol과 David도 접근이 필요하다는 요청이 들어왔습니다. 마찬가지로 IAM user를 만들었습니다. S3 bucket만 접근하면 된다고 하니 S3FullAccess 권한을 부여했습니다.
3. Sammie는 피곤한 나머지 피곤한 휴가를 썼습니다. 휴가를 떠나기 전, 다른 DevOps팀원인 Eve가 도와줄 수 있도록 Eve의 IAM user를 만들었습니다. Sammie가 휴가에 간 사이 불쌍한 Eve는 Terraform으로 VPC를 만들었습니다. OpenVPN instance를 하나 띄우고, Alice와 Bob, Carol, David와 Eve 계정을 추가했습니다.
4. Sammie가 휴가에서 돌아왔습니다. Carol과 David가 EC2 instance를 직접 띄울 수 있어야 한다는 요청이 왔습니다. IAM user의 권한에 EC2FullAccess를 추가했습니다.
5. EC2 instance에 disk 증설 요청이 왔습니다. Sammie는 Eve에게 VPN profile을 받아서 VPN client에 등록했습니다. 10개가 넘는 VPN profile에서 클릭 실수로 Azar Production VPC에 연결이 되어버렸습니다. 다시 azar2-dev profile을 클릭해서 연결하는데, 내 계정 정보가 뭐였는지 기억나지 않습니다. 아니 계정이 존재하기는 했던가?

### 퇴사자 발생
오랫동안 회사에서 많은 일을 하신 Judy가 퇴사한다고 팀장님이 Judy의 계정 삭제를 요청했습니다.

1. 수많은 AWS 계정에서 Judy용 IAM user를 지웠습니다.
2. 수많은 AWS VPC에 띄워놓은 OpenVPN instance에 접속해서 Judy 계정을 지웠습니다.
3. 퇴근 후 맥주를 마시다 on-call이 울렸습니다. Judy가 본인 IAM user의 credentials를 production 서비스에 사용했고, 리뷰에서 놓쳐 그대로 production 장애가 발생했던 것입니다.

## Pain Points
제일 처음에 소개해드렸던 시스템이라면 AWS 계정의 권한과 VPN의 권한이 한 개의 git repository에서 관리되기 때문에 위 상황의 대부분은 간단한 몇 줄의 PR로 처리할 수 있습니다. 하지만, 시스템이 도입되기 전 위 상황에서 Sammie를 포함한 DevOps가 고통받았던 지점은 다음과 같습니다.

1. 팀장 등 극히 일부를 제외하고, 보통 팀은 대부분 동일한 권한을 가집니다. IAM group을 사용해서 IAM user에게 동일한 권한을 부여하기는 쉽지만, IAM user는 사람마다 하나씩 부여해야 합니다.
2. 때로는 회사의 공식적인 조직과 업무를 위한 인프라 권한이 다른 경우가 발생합니다.
3. 개발자의 권한 변경 요청은 사소하지만, 생각보다 자주 발생하며 시간을 소모합니다.
4. VPN 계정과 profile이 여러 개일 경우 매우 피곤해집니다. DevOps 특성상 많은 VPC를 오가며 작업해야 할 때가 많은데, 연결하는데 많은 시간을 소모하게 됩니다.
5. AWS 계정과 VPN 계정이 다른 경우 credential leak이 발생할 경우 피곤해집니다.
6. IAM user를 발급할 경우, rotate가 되지 않거나, 실수로 git에 올라가는 등 보안에 취약합니다. 또한 Judy의 예시처럼 실수로 service에 사용되고 있다 퇴사하여 삭제된 경우 production service에 장애가 발생합니다.

이 문제를 해결하기 위해 가장 먼저, AWS 계정 접근과 VPN 접근을 하나로 통일할 필요가 있었습니다. Hyperconnect에서는 AWS SSO와 AWS Client VPN을 사용했는데, 좀 더 자세히 알아보겠습니다.
 

# AWS SSO
AWS SSO는 한 번의 로그인으로 다른 AWS 계정이나 외부 application을 사용할 수 있도록 사용자의 신원과 application 권한을 중앙 관리하는 도구입니다. 특히, AWS organization 내부의 AWS 계정은 별도 설정 없이 빠르게 연동할 수 있습니다. 연동 후에는 아래 사진처럼 로그인 한 번으로 본인이 접근 가능한 AWS account의 목록을 모두 볼 수 있고, 권한을 클릭하여 AWS console에 로그인할 수 있습니다.
![sso login]({{"/assets/2022-05-12-aws-permission-management-using-gitops/02-aws-sso.png"}})

AWS SSO를 사용하는 방법에 대해 조금 소개해 보겠습니다. AWS 계정에 권한을 부여하려면 먼저 PermissionSet을 생성해야 합니다. 한 개의 PermissionSet은 AWS에서 관리하는 managed policy 여러 개와 한 개의 custom inline policy를 가질 수 있습니다. 이 글의 제일 처음 예시에서 들었던 `RDSMasterAcccess` 가 하나의 PermissionSet입니다. 이렇게 생성한 PermissionSet은 여러 AWS 계정에 배포할 수 있어 각 계정마다 동일한 PermissionSet을 중복해서 만들 필요 없이 한 번에 관리할 수 있습니다.

그다음으로 AccountAssignment를 생성해야 합니다. 이는 (1) AWS 계정, (2) 그룹 또는 사용자, 그리고 (3) PermissionSet의 조합입니다. 이때, 그룹 또는 사용자는 AWS SSO 내부에서 직접 관리하거나, 이미 존재하는 Active Directory에서 가져와 사용할 수도 있습니다. 제일 처음 예시에서는 yaml 파일을 통해 (1) `azar-prod` 계정에서 (2) Bob에게 (3) `RDSMasterAccess`를 부여했는데, 이는 실제로 AccountAssignment를 생성하게 됩니다. 이렇게 AccountAssignment 생성이 완료되면 AWS SSO를 통해 AWS 계정에 접근할 수 있습니다.

기술적인 내용을 조금 더 설명하자면, AWS SSO는 AccountAssignment 생성 마지막 단계에서 다음 작업을 자동으로 수행합니다.
1. AWS SSO에서 생성한 PermissionSet이 각 AWS 계정으로 배포됩니다. `arn:aws:iam::<account-id>:role/aws-reserved/sso.amazonaws.com/<region>/AWSReservedSSO_<permission_set_name>_<hash>` 같은 형태의 role이 생성되며 사용자는 이 role을 사용하여 AWS 계정에 권한을 가지게 됩니다.
2. 각 계정에 SAML identity provider가 생성됩니다. `arn:aws:iam::<account-id>:saml-provider/AWSSSO_<hash>_DO_NOT_DELETE`와 같은 형태의 SAML identity provider가 생성되며, 사용자는 이 identity provider를 통해 1에서 생성한 role을 assume 할 수 있게 됩니다.

이 외에도 AWS SSO의 기능은 많습니다. 예를 들어, Macbook의 Touch ID까지 지원하는 MFA를 설정할 수 도 있습니다. 더 많은 기능은 AWS의 공식 문서를 참고하시기 바랍니다. 이제 AWS SSO에 대한 소개는 마치고, AWS Client VPN에 대한 소개를 해보겠습니다.


# AWS Client VPN
AWS Client VPN Endpoint (이하 AWS VPN)은 OpenVPN과 호환되는 AWS 관리형 VPN입니다. AWS VPN을 연결하면 VPC / Subnet 내부의 IP를 사용하여 VPC 내부의 자원에 접근할 수 있습니다. 다른 VPC와 VPC peering 되어있거나 transit gateway로 연결되었다면, 해당 VPC에도 접근이 가능합니다.

AWS VPN을 생성할 때는 연결할 대상의 VPC / Subnet과 client 인증 방법을 지정해야 합니다. 인증 방법은 Active Directory, SAML-based identity provider이나 mutual TLS를 지원합니다.

AWS VPN을 생성하고 나면, 접근이 필요한 모든 network의 CIDR 대역을 authorization rule에 추가해야 합니다. 만약 Active Directory 또는 SAML IdP 인증을 선택했다면, 각 CIDR별로 접근할 수 있는 사용자 그룹을 지정할 수 있으며 prefix가 제일 많이 일치하는 authorization rule이 먼저 적용됩니다. 예를 들어, 다음 2개의 rule이 설정되어 있는 상황을 가정합니다.
- `0.0.0.0/0`에 대해서는 devops 그룹만 접근을 허용함
- `10.0.0.0/8`에 대해서는 aws-azar-vpn 그룹만 접근을 허용함

이때, 만약 devops인 Sammie가 aws-azar-vpn 그룹에 없다면, 123.0.0.1에는 접속이 가능하지만, 10.0.0.1에는 접속이 불가능합니다. 따라서, 모든 network에 전부 접근해야 하는 사람은 모든 authorization rules에서 지정한 그룹에 전부 포함시켜야 합니다.


# Solution
이제 위에서 소개한 AWS SSO와 AWS Client VPN을 사용해서 어떻게 권한 시스템을 설계했는지 소개해드리겠습니다.

## Active Directory
먼저, 모든 인증 데이터를 저장하기 위한 Active Directory를 구축했습니다. Azure나 AWS의 managed Active Directory 대신, 직접 AWS VPC 위에 EC2 instance를 띄워 HA로 구성했습니다. 구체적인 Active Directory 설정 방법이나 HA 설정 등은 이 글의 주제가 아니므로 넘어가겠습니다. :)

다만, SSO 관점에서 사용한 몇 가지 도구와 설정을 공유해드립니다. 먼저, Google Cloud Directory Sync[[3]](https://support.google.com/a/answer/106368) (GCDS)를 사용하여 AD의 사용자나 그룹이 Google Workspace의 사용자 및 Google Groups과 동기화되도록 설정했습니다. 또한 G Suite Password Sync[[4]](https://support.google.com/a/answer/2611859) (GSPS)를 사용하여 AD의 비밀번호 변경이 그대로 Google Account에 적용되도록 설정했습니다. Okta의 Active Directory Integration[[5]](https://help.okta.com/en/prod/Content/Topics/Directory/ad-agent-main.htm) 기능을 사용해서 Okta와도 연결했습니다.

이 도구들을 사용해서 Google Groups나 Okta 밖에 지원하지 않는 시스템도 쉽게 연동 가능합니다. 또한, ldap protocol 밖에 지원하지 않는 시스템의 경우 Active Directory instance로 연결되는 AWS Network Load Balancer를 생성하면 쉽게 연동 가능합니다.

![active directory]({{"/assets/2022-05-12-aws-permission-management-using-gitops/03-active-directory.png"}}){: height="250px" .center-image }

## InfraRole
그다음, InfraRole이라는 개념을 만들었습니다. 회사의 조직, 업무 및 인프라 권한은 대체로 일치하지만, 회사의 조직은 인프라 권한을 부여하기 위해 만든 것이 아닌 만큼 서로 다른 경우가 존재합니다. 특히 프로젝트가 새로 시작되거나 급격히 성장하는 과정에서는 일치하지 않는 경우가 더 많이 발생합니다.

따라서, DevOps팀에서는 조직과 인프라 권한을 일치시키기 위해 InfraRole이라는 개념을 만들었습니다. DevOps팀은 회사 조직도를 사용하는 대신, 인프라 권한에 맞춰 InfraRole을 생성하여 DevOps 업무를 처리하고, 인프라 권한을 부여합니다. 기본적으로 1개의 프로젝트 당 `(프로젝트)-api`, `(프로젝트)-ios`, `(프로젝트)-android` 3개를 생성하며, 개발자가 더 늘어서 별도의 권한 분리가 필요한 경우 추가하고 있습니다. 이렇게 하면, 신규 프로젝트 또는 요청에 의한 팀 간 이동이 있을 때 회사의 공식적인 인사 처리를 기다릴 필요 없이 관련 팀장과 빠르게 논의하여 권한을 변경할 수 있습니다.

InfraRole 1개마다 바로 전에 소개했던 Active Directory의 Group 1개를 생성했습니다. 생성한 Active Directory의 Group는 GCDS를 통해 Google Groups로 동기화되어 그룹 메일도 자동으로 생성되는데, 이를 일정 초대나 Drive 공유 권한 설정 등 다양한 곳에 사용할 수 있습니다.

권한 제어나 Google 제품에서의 활용뿐만 아니라, InfraRole을 EC2 instance tag에 붙여 비용을 추적하는데도 사용하고, 모니터링 시스템과 연동하여 on-call 또는 Slack alert을 발생시킬 대상을 정하는데도 사용하는 등 인프라와 관련된 거의 모든 곳에서 사용하고 있습니다.

## AWS SSO
Hyperconnect에서는 AWS organization master 계정에 AWS SSO를 구축했고, 직접 구축한 Active Directory를 identity provider로 사용하도록 설정했습니다. Self-managed AD를 AWS SSO에 연결하기 위해서는 AD connector를 생성해야 합니다. AD connector 생성 및 설정은 AWS 문서[[6]](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_ad_connector.html)를 보고 진행했습니다.

AWS SSO 생성과 identity provider 연결이 완료되었다면, PermissionSet을 생성할 차례입니다. Hyperconnect에서는 DevOps 외에도 일부 개발자들에게 AdministratorAccess에 준하는 권한을 부여하고 있으며, production account와 이 외의 account로 분리하여 조금씩 권한을 다르게 제한합니다. 구체적으로, 다음과 유사한 권한을 제한합니다.

#### DevOps 이외에 개발자에게 부여하지 않는 권한
IAM User 및 Network 관련 일부 권한을 제한하며, 이 권한은 개발 전용 AWS 계정에서도 개발자에게 부여하지 않습니다. 이는 심각한 보안 위협 또는 서비스 장애를 막기 위해서입니다.
- IAM user 생성, 수정, 삭제 권한 및 access key 발급 권한 (IAM policy를 추가하는 권한도 포함)
- VPC route table 생성, 수정, 삭제 권한 및 subnet에서 route table replace 권한
- VPC transit gateway와 관련된 모든 non-readonly 권한

#### Production 계정에서 개발자에게 부여하지 않는 권한
AWS IAM에 익숙하지 않은 개발자는 종종 서비스에 대해 전체 권한을 부여하는 (ex: `Action: "s3:*"`) 정책이 담긴 IAM role을 생성하여 사용합니다. 물론 이는 development 계정에서도 절대 권장되지 않으나, 빠른 개발을 위해 개발자가 IAM role을 직접 생성할 수 있는 권한을 막고 있지는 않습니다. 다만, production 계정에서 이와 같은 권한 부여는 치명적이므로, production 계정에서만 제한합니다.
- RDS 및 S3 bucket 삭제 권한
- IAM role 생성, 수정, 삭제 권한 (IAM policy를 추가하는 권한도 포함)
- IAM policy 생성, 수정, 삭제 권한

이제 PermissionSet을 생성했으니, AD에 존재하는 그룹과 사용자를 지정하여 AccountAssignment를 생성할 수 있습니다. 다만, Hyperconnect에서는 Active Directory의 InfraRole 그룹을 사용하여 AccountAssignment를 구성하지 않았습니다. 같은 InfraRole을 가지는 사람끼리는 대부분 권한이 비슷하나, 팀장에게는 추가적인 권한 부여가 필요하고, 인턴에게는 권한 일부를 제한해야 하는 등 반드시 권한이 일치하지는 않는 경우가 있기 때문입니다. 글의 제일 처음에서 소개해드렸던, Bob의 RDS 삭제 예시를 생각해보시면 됩니다.

이 문제를 해결하기 위해, 각 계정과 PermissionSet의 조합마다 Active Directory의 그룹을 생성하고, 이를 사용하여 AccountAssignment를 구성하였습니다. Bob의 예제에서는 `azar-prod-rds-admin` 그룹을 생성하고, Bob을 이 그룹에 할당시킨 다음, 이 그룹의 구성원에 대해 `azar-prod` 계정의 `RDSMasterAccess` 권한을 부여했습니다.


## AWS Client VPN (이하 AWS VPN)
Hyperconnect는 관리 목적으로만 사용되는 전용 AWS 계정이 있으며, 모든 VPC와 transit gateway로 연결된 관리용 VPC가 존재합니다. 따라서, AWS VPN 또한 해당 관리용 VPC에 설정하였습니다. EC2 등 관리용 VPC의 다른 리소스와 쉽게 구분할 수 있도록 VPC 내부에 vpn용 subnet을 생성하고, 모든 요청은 이 subnet에 연결시켰습니다. 따라서, AWS VPN를 사용하여 EC2나 RDS 등 특정 리소스에 연결할 수 있도록 하려면 해당 리소스의 security group에 vpn subnet CIDR를 입력해주기만 하면 됩니다.

![network topology]({{"/assets/2022-05-12-aws-permission-management-using-gitops/04-network-topology.png"}}){: height="300px" .center-image }

먼저 AWS VPN을 생성했습니다. 처음에는 AWS SSO와 마찬가지로 Active Directory를 사용하여 인증하도록 구성하였으나, Okta가 도입되면서 Okta를 사용하도록 변경했습니다. AWS VPN 구성이 끝났다면, authorization rule을 생성하고 관리할 차례입니다. Hyperconnect에서는 다음과 같이 설정하여 사용하고 있습니다.
- 모든 Private IP CIDR: DevOps 그룹에만 허가
- 각 VPC의 CIDR: VPC에 따른 그룹을 별도 생성하여 해당 그룹에만 허가

VPC 접근도 AWS 계정 접근과 같이 InfraRole이 동일한 사람들은 대부분 같은 권한을 부여받지만, 다른 팀이나 제품과의 협업을 위해 몇몇 사람에게만 추가 권한이 필요합니다. 따라서, VPN의 authorization rule에는 InfraRole 그룹을 직접 넣지 않고, VPC에 따른 그룹을 별도 생성하여 지정하였습니다.


# perm-gitops!
이제 마지막 단계입니다! AWS SSO의 각종 설정과 AWS Client VPN의 AuthorizationRule이 코드로 관리되지 않는 상태였으므로, 이 둘을 해결할 프로젝트를 만들기로 했습니다. 구체적으로 다음 4가지 핵심 기능을 모두 수행할 수 있어야 했습니다.
1. 회사의 모든 InfraRole과 모든 개발자의 원본 데이터 보관
2. InfraRole 및 소속 개발자와 Active Directory 그룹 동기화
3. AWS SSO AccountAssignment 및 PermissionSet을 코드로 관리
4. AWS Client VPN의 AuthorizationRule을 코드로 관리

3번과 4번은 Terraform으로 쉽게 작업할 수 있을 것이라고 생각했습니다. 지금은 Terraform AWS provider를 사용하여 쉽게 작업할 수 있지만, AWS SSO 도입 당시에는 AWS SSO API 자체가 없었으며, 해당 API가 공개된 다음 몇 달 동안 Terraform AWS provider에서 지원하지 않아 관련 설정을 동기화하는 코드를 Python으로 개발해야 했습니다. 먼저, 동기화 코드와 yaml 데이터가 담긴 최상위 directory를 각각 생성한 뒤, 설정 파일 디자인부터 시작했습니다.

가장 처음 예시에서 확인할 수 있었듯이 `infra-role`, `permission-set`, `aws-account`, `aws-vpn`과 같이 데이터의 종류에 따라 directory를 분리해서 저장했습니다. 각 InfraRole별로는 다음 파일을 생성했습니다.
- `users.yaml`: 해당 InfraRole에 소속된 모든 사람을 기록합니다. 이 파일이 회사 전체 권한 관리의 시작점이 됩니다.
- `roles.yaml`: AWS SSO와 AWS Client VPN의 접근 권한을 기록합니다.
- `<product>.yaml`: gitops 도구와 추가적으로 연동할 다른 제품의 권한을 기록합니다.

`roles.yaml`을 디자인할 때는 AWS IAM policy 문법에서 몇 가지 아이디어를 가져왔습니다. `effect`라는 설정이 존재하고, `effect: deny`인 규칙이 `effect: allow`보다 먼저 적용되도록 하거나, `accounts`나 `permissions`가 단일 아이템이나 목록이 될 수 있도록 하는 것 등이 있습니다.

### Sync
이제 동기화 코드를 작성할 차례입니다. 동기화 코드의 기본은 Kubernetes Operator나 Terraform이 하는 것처럼 다음 4단계 step으로 구현했습니다.
1. AWS API를 사용하여 (그리고 약간의 설정 파일을 읽어) 현재 상태를 계산
2. 설정 파일을 읽어 (그리고 약간의 AWS API를 사용하여) 원하는 상태를 계산
3. 1을 2로 만들기 위해서 필요한 action을 계산
4. dry-run이 아닐 경우 3에서 계산한 action을 실제로 실행

모든 코드는 Python3.9로 작성되었으며, type annotation과 dataclass를 최대한 사용하여 오류가 발생할 여지를 줄였습니다. 또한 master branch에 merge 전 반드시 상태 동기화에 필요한 action을 계산하고 DevOps의 리뷰를 받도록 강제하였습니다. Github Actions를 사용하여 PR에 `/plan`과 같은 comment를 입력하면, 상태 변화에 필요한 action 계산 결과를 PR comment로 남기도록 했습니다.


# Current & Feature?
제일 앞에서 소개했듯이, gitops repository에는 각 팀의 팀장들이 신규 입사자 / 퇴사자가 있을 때 직접 PR을 날려 리뷰를 요청하고 있습니다. 팀장뿐만 아니라 권한이 추가로 필요한 팀원도 PermissionSet을 추가하고, 다른 팀의 계정에 접근을 추가하는 요청 등 자유롭게 PR을 보내고 있습니다. 이제 DevOps팀은 메일, Slack 입사 환영 채널, Slack DM, 구두 전달 등등을 통해 권한 변경 요청에 대응하지 않아도 됩니다.

GitOps 관리 도구는 계속 확장해나가고 있습니다. SSO로 InfraRole 연동이 불가능하거나, InfraRole에 따라 다른 권한을 부여해야 하는 경우 이 도구에 추가 개발을 진행하고 있습니다. 현재 Hyperconnect에서는 AWS SSO와 VPN 외에도 다음 도구의 권한을 동기화하는 데 사용하고 있습니다.
- Internal developer portal
- Kibana, Grafana, Sentry
- Github Organizations & Teams
- Harbor, [Querypie](https://www.querypie.com/en)
- Cloudflare

terraform-aws-provider에서 AWS SSO를 지원[[7]](https://github.com/hashicorp/terraform-provider-aws/issues/15108)하기 시작했고, 아직 preview지만 ActiveDirectory 관련 provider[[8]](https://github.com/hashicorp/terraform-provider-ad)도 릴리즈 되어 계속 개발되고 있습니다. Terraform provider가 존재하는 제품은 관리의 편의성을 위해 Terraform으로 migration 하는 것도 고려하고 있습니다 :)


# Wrap Up
개발자의 AWS 계정 접근과 VPC 접근을 더 쉽고 안전하게 만들면서 DevOps팀의 편의를 증진시키기 위해 다음 작업을 수행했습니다.
- InfraRole이라는 개념을 만들어 인프라 권한을 회사 조직도에서 분리시켰습니다.
- AWS SSO를 사용하여 AWS Console 및 API 권한을 제어하고, 유효 기간이 있는 AWS API credential을 발급합니다.
- AWS Client VPN Endpoint를 사용하여 수십 개의 VPC를 한 개의 VPN 연결로 접근 가능하도록 만들었습니다.
- gitops 프로젝트를 만들어 InfraRole, Active Directory group membership, AWS SSO와 AWS Client VPN Endpoint의 데이터와 설정을 git으로 관리하도록 했습니다.

마침내, 개발자가 직접 본인의 권한을 수정할 수 있도록 단일 repository를 사내 인프라 권한 부여의 시작점으로 만들었습니다. 더 이상 DevOps가 신규 입사자나 퇴사자, AWS 계정이나 VPN 접근 credentials를 신경 쓸 필요가 없게 되어 많은 시간을 절약하게 되었고, 개발자의 AWS credentials은 일정 시간 이후에 자동으로 만료되어 더 안전해졌습니다.

AWS multi-account나 multi-vpc 환경에서 권한 관리를 고민하고 계신 분들께 많은 도움이 되었으면 좋겠습니다.

긴 글 읽어주셔서 감사합니다 :)

<br>
<br>
언제나 글 마지막은 채용공고입니다. 이렇게 재미있는(?) 일을 같이할 DevOps의 많은 지원 부탁드립니다. [채용공고 바로가기](https://career.hyperconnect.com/jobs/)

# References
[1] [https://aws.amazon.com/single-sign-on/](https://aws.amazon.com/single-sign-on/)

[2] [https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/what-is.html](https://docs.aws.amazon.com/vpn/latest/clientvpn-admin/what-is.html)

[3] [https://support.google.com/a/answer/106368](https://support.google.com/a/answer/106368)

[4] [https://support.google.com/a/answer/2611859](https://support.google.com/a/answer/2611859)

[5] [https://help.okta.com/en/prod/Content/Topics/Directory/ad-agent-main.htm](https://help.okta.com/en/prod/Content/Topics/Directory/ad-agent-main.htm)

[6] [https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_ad_connector.html](https://docs.aws.amazon.com/directoryservice/latest/admin-guide/directory_ad_connector.html)

[7] [https://github.com/hashicorp/terraform-provider-aws/issues/15108](https://github.com/hashicorp/terraform-provider-aws/issues/15108)

[8] [https://github.com/hashicorp/terraform-provider-ad](https://github.com/hashicorp/terraform-provider-ad)

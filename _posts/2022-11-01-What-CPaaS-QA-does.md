---
layout: post
date: 2022-11-01
title: CPaaS QA가 하는 일
author: anne
tags: qa testing
excerpt: SDK를 테스트할 때는 일반적인 웹/앱 서비스를 테스트할 때와 어떤 다른 점이 있는지를 중심으로 CPaaS QA가 하는 일을 소개합니다. 
last_modified_at: 2022-11-01
---

안녕하세요. 저는 QA3 Team의 CPaaS Unit에서 Audio/Video Call SDK를 담당하고 있는 Anne입니다. CPaaS는 아자르, 하쿠나에 쓰이는 미디어 기술을 활용해서 외부에서 쉽고 빠르게 적용할 수 있도록 관련 Communication 기술을 별도 SDK 형태로 제공해주는 서비스입니다. WebRTC기반 Call Protocol을 1:1 또는 Group Call 형태로 구현할 수 있는 API를 제공하고 있고, 이에 필요한 Console 및 Documentation도 지원해주고 있습니다.
 
QA는 도메인이나, 프로덕트 특성에 따라 정말 다양한 방식으로 일을 하게 됩니다. B2B 서비스를 제공하는 저희는 어떤 Process로 일을 하고 있는지, SDK를 테스트할 때는 일반적인 웹/앱 서비스를 테스트할 때와 어떤 다른 점이 있는지를 중심으로 CPaaS QA가 하는 일을 공유해보려고 합니다.

# QA Process 소개

![process]({{"/assets/2022-11-01-what-CPaaS-QA-does/process.png" | absolute_url}})

Epic Studio의 CPaaS 조직에서는 Milestone 단위로 정기배포를 하고 있습니다. Milestone은 총 8주 동안 진행되며, 각각 2주 단위로 운영되는 3개의 Sprint와 1개의 Workshop으로 이루어집니다. Sprint 초반에는 개발자분들의 작업 건에 맞추어 요구사항 분석 및 Test 설계를 하고, Sprint 말미의 QA 기간에 테스트를 수행합니다. Sprint QA 기간 동안 해당 Sprint에 추가되는 기능과 수정사항을 테스트하고, Regression Test를 진행하고 있습니다. 

Workshop 기간에는 Sprint QA에서 확인하지 못했던 Cross Browser Test나 테스트 케이스(TC) 개선 작업을 진행하고 Prod 배포 전 Beta 환경에서의 테스트를 진행합니다. 이런 기본적인 테스트 설계-수행 활동 외에도, 새로 추가될 기능들의 Spec 논의에도 참여하면서 전체적인 흐름과 어떤 부분을 중점으로 테스트해야 하는지를 파악하고 있습니다.

## 끊임없이 프로세스 개선 중!

QA팀에서는 어떻게 하면 더 효율적으로 일할 수 있을지 항상 고민하고 있습니다. 2주마다 회고 시간을 가지고 어떤 점이 좋았고, 또 어떤 점을 개선시켜야 할지 함께 논의하면서 더 나은 방향으로 일할 수 있게 노력합니다. 얼마 전에는 Risk Based Testing 기법을 적용해서 프로세스 개선을 진행했습니다. 

QA 기간에 비해 TC 수행에 걸리는 시간이 너무 길었고, TC 수행 시간을 줄여서 더 창의적이고 유연하게 이슈를 발견할 수 있는 시간을 확보해보자는 니즈가 있었습니다. 

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2022-11-01-what-CPaaS-QA-does/matrix.png" | absolute_url}}' alt='absolute'>
  <figcaption>Risk Assessment Matrix</figcaption>
</figure>


Matrix를 저희 상황에 맞게 조정하고, 각 TC의 Probability와 Severity를 판단해보면서 우선순위를 지정했습니다. 배포 전 세 번의 Sprint 동안 우선순위가 낮고 안정적인 케이스들을 매번 확인하는 것이 비효율적이라고 느껴져서, Sprint 동안은 우선순위 높음/중간인 케이스만 수행하는 방향으로 프로세스를 개선했습니다. 그 결과 Sprint 기간에 수행해야 하는 TC의 개수가 356개에서 250개로 약 30% 감소했습니다. 우선순위 낮음에 해당하는 케이스는 Workshop 기간에 진행하기로 하여 Prod 배포 전 모든 TC를 수행하면서 품질도 이전과 동등한 수준으로 보장할 수 있었습니다. 

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2022-11-01-what-CPaaS-QA-does/tc.png" | absolute_url}}' alt='absolute'>
  <figcaption>리스크 기반 테스트로 우선순위를 도출한 TC</figcaption>
</figure>

# B2B Product라서 다른 점?

## 기획서가 없어요.

요구사항 분석하고, 테스트 설계하고 TC 수행하고… 큰 프로세스는 크게 다르지 않지만, B2C 서비스와 제일 다른 점은 기획서가 없다는 점입니다. 그럼 뭘 보고 설계하냐고요? 저희의 테스트 베이시스는 개발자분들이 작성한 Tech Spec 문서입니다.

Tech Spec은 요구사항, 인터페이스 정의와 플랫폼별 차이, 예외 사항 등 Feature를 개발하기 위해 작성되는 문서입니다. 이 문서를 바탕으로 Spec을 분석하고 테스트 설계를 하고 있습니다. Tech Spec은 노션에 작성되고 있는데, 노션의 댓글 기능을 이용해 바로바로 질문을 하기도 하고, Spec이 복잡한 경우에는 Spec을 정확히 이해하고 설계할 수 있도록 개발자, PM분들과 Meeting을 진행하기도 합니다.

QA분들 중에는 Tech Spec 문서가 낯선 분들도 많으실 것 같은데요, 실제 Tech Spec 문서를 보여드릴 수는 없어서 비슷하게 재구성한 인터페이스를 예시로 제가 이슈를 찾았던 사례를 소개해보겠습니다.

바로 Tech Spec에 적혀있는 인터페이스 정의를 보고 callback에 누락된 요소를 찾았던 경험이었습니다. 

```javascript
interface SessionInfo {
    sessionId: string,
    useVideo: boolean,
  }

interface UserSessionEventDetail {
    ...
    SessionInfo?: SessionInfo,
    ...
  }

export interface ScreenShareStartedEventDetail extends UserSessionEventDetail {
    ...
    }
```

위의 코드를 보면 `ScreenShareStartedEventDetail`은 `UserSessionEventDetail`을 상속받고 있어서 `ScreenShareStartedEventDetail`이 호출됐을 때 `UserSessionEventDetail`의 `SessionInfo`도 확인이 가능해야 하는데, Spec과는 달리 `SessionInfo`를 확인할 수 없었습니다. 개발 단계에서 해당 요소를 누락한 이슈였습니다. 해당 이슈를 발견하고 동일한 클래스를 상속받은 다른 인터페이스에서는 누락된 요소가 없는지 재차 확인하면서 Spec대로 구현이 되었는지 확인을 진행했고, 이슈를 수정해서 Prod에 배포할 수 있었습니다.

## TestApp이 따로 있어요.

또 하나의 다른 점은 테스트를 위한 TestApp이 따로 있다는 점입니다. Call SDK는 UI를 제공하지 않아서 SDK의  UI를 테스트할 일은 없지만, 각 기능들을 수월하게 테스트하기 위해서는 SDK API를 호출하는 UI 기반의 테스트용 App이 필요합니다. SDK API를 QA가 직접 호출하기 힘들고, User Scenario를 기반으로 테스트하는 데는 UI가 있는 편이 훨씬 효율적이기 때문입니다.

SDK에 새 기능이 추가될 때, TestApp에도 해당 기능을 테스트할 수 있는 UI를 추가해야 합니다. 어떻게 테스트할 것인지, 어떻게 UI를 구성해야 효과적으로 테스트할 수 있을지 개발, PM과 함께 Sync Meeting을 진행합니다. Sync Meeting에서 결정된 사항들이 TestApp에 반영됩니다.

TestApp은 단순히 테스트용으로 만들어진 App이기 때문에 이슈가 발생했을 때 SDK의 이슈인지, SDK가 아닌 TestApp의 이슈인지 구분해야 합니다. SDK 이슈인지, TestApp 이슈인지 애매한 경우에는 슬랙 채널에 문의해서 확인하고 이슈로 티켓팅하고 있습니다.

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2022-11-01-what-CPaaS-QA-does/testapp.png" | absolute_url}}' alt='absolute'>
  <figcaption>TestApp 화면</figcaption>
</figure>

테스트의 관점에서는 UI보다는 기능에 초점을 맞춰서 테스트를 진행한다는 점이 B2C 서비스와 제일 다른 점인 것 같습니다. 몇몇 기능들은 TestApp의 UI 변화로 기능 동작을 확인할 수 있지만, 중요 체크포인트인 SDK API의 callback 로그는 네트워크 로그나 TestApp의 이벤트 로그 영역에서 확인하고 있습니다.

# 테스트 자동화 이야기

QA 이야기에 테스트 자동화 이야기도 빼놓을 수 없겠죠. 테스트 자동화는 적절하게 활용하면 QA와 개발팀의 부담을 많이 줄여줄 수 있습니다. Epic Studio는 조직 전체적으로 품질을 굉장히 강조하는 조직입니다. 개발팀에서도 unit test 등을 적극적으로 활용하고 있고, Web 같은 경우는 E2E 테스트를 개발 조직 자체적으로 운영하고 있습니다. Web Unit의 Jace가 작성한 E2E 테스트 구축기는 "[멈춰! 버그 멈춰! E2E 테스트로 버그 멈추기 Feat. Playwright](https://hyperconnect.github.io/2022/01/28/e2e-test-with-playwright.html)" 이 링크에서 확인하실 수 있습니다. 

QA팀에서도 테스트 자동화를 도입하기 위해 노력하고 있는데요, API 테스트 코드를 작성해서 Backend 개발팀에 공유한 바 있습니다. QA팀에서 작성한 API 테스트 코드는 Backend 배포 후 모니터링하는 데 사용되고 있습니다. 

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2022-11-01-what-CPaaS-QA-does/slack.png" | absolute_url}}' alt='absolute'>
  <figcaption>테스트는 CI에서 수행되고 테스트 결과가 슬랙 채널로 공유됩니다.</figcaption>
</figure>

현재는 모바일 TestApp을 대상으로 테스트 자동화를 도입하기 위해 논의를 진행하고 있습니다. 초기 단계에서는 개발자분들께서 구조를 잡아주시고, 차후에는 필요한 TC를 QA에서 직접 코드를 작성해서 추가하는 방향으로 진행될 예정입니다.

하이퍼커넥트 CPaaS QA로 일하면서 놀랐던 점은 개발자 분들도 테스트 자동화에 많은 관심을 갖고 계시다는 것이었습니다. 개발자 분들과 함께 구축하게 되면 더 효율적이고 퀄리티 있게 테스트 자동화를 적용할 수 있을 것 같아서 더욱 기대가 됩니다. 테스트 자동화가 잘 진행되어서 실제로 활용되고 자리를 잡으면 성공사례로 또 소개하러 오겠습니다. 🙌

# 마치며

CPaaS QA에서 어떤 일을 하는지 소개할 기회가 생겨 글을 쓰게 되었는데, 저 스스로도 어떤 일을 해 왔고 또 할 것인지 정리가 되는 좋은 경험이었던 것 같습니다. 하이퍼커넥트의 QA Team은 앞으로도 다양한 테스트 설계 기법과 효율적인 테스트 방법으로 품질을 높이는 방법을 고민하고 적용함으로써 회사 내의 사업적인 리스크와 제품적인 리스크를 줄일 수 있도록 노력할 것입니다.

이것으로 글을 마칩니다. 감사합니다.

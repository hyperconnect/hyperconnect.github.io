---
layout: post
date: 2022-03-02
title: 하쿠나 입장 API 개선하기 - 괴물 API 리팩토링과 성능개선하기
author: karol
tags: testing refactoring
excerpt: 하쿠나의 괴물 API 중 하나인 입장 API 개선 feature를 진행하며 어떤 장벽들이 있었고 이를 어떻게 해결하며 결과를 이끌어 냈는지에 대해 설명합니다.
---

<!-- 이미지 좀 더 괜찮은거 없으려나 -->

![liveroom_hakuna_logo]({{"/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_hakuna_logo.png"}}){: height="150px" .center-image }

안녕하세요. 하이퍼커넥트 하쿠나 스튜디오 Backend 팀의 Karol입니다. 최근 저희 팀에서는 팀의 오랜 숙원이었던 `입장 API`를 리팩토링하고 성능을 개선하는 작업을 진행했었는데요. 이번 글을 통하여 이 가장 오래된 레거시 중 하나였고, 성능상 치명적이었던 `입장 API`을 어떤 식으로 개선하였는지, 그리고 어떤 결과를 얻었는지 공유드리고자 합니다.

# 하쿠나 간단 소개와 백엔드 팀이 가지는 과제

![liveroom_hakuna]({{"/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_hakuna.png"}}){: height="300px" .center-image }

먼저 간단하게 하쿠나는 어떤 서비스인지 설명드리고 개발팀에서 달성해야하는 목표를 설명드리려고 합니다. 저희 서비스는 여러분들이 익히 아시는 트x치, 아xx카TV와 같은 **소셜 라이브 스트리밍 서비스**입니다. 소셜 라이브 스트리밍 서비스에서는 실시간으로 사용자간의 다양한 상호작용이 일어납니다. 이를 위해 저희 backend 팀에서는 아래와 같은 주요 목표를 세우고 개발에 임하고 있습니다. 

- 라이브 스트리밍 서비스로서 유저에게 **실시간성(Real-Time) 제공**
- 서비스 내부에서 별도의 재화가 이동이 있기 때문에 유저에게 **일관성(Consistency) 제공**
- 글로벌로 서비스로서 **24시간 무중단**으로 운영
- 아이템과 레벨, 그리고 유저간의 랭킹 등 **다양한 feature** 존재

이러한 특성들을 고려하면 저희가 운영하고 있는 서비스는 게임으로 분류되지는 않지만 사실 게임에 굉장히 가까운 서비스라고 설명할 수 있겠죠.

# 하쿠나에서 입장하기 API란

하쿠나와 같은 **소셜 라이브 스트리밍 서비스에서 입장하기는 가장 기본이 되는 API**입니다. 호스트가 있는 방에 입장을 할 수 있어야 그 이후에 호스트와의 상호작용이 가능하기 때문입니다. 

서비스의 가장 기본이 되는 기능이라는 것은 어떤 의미를 가지고 있을까요? 어떤 API 보다 먼저 개발되었고 가장 오래된 API라는 의미이기도 합니다. 하쿠나 서비스는 올해로 4년차에 접어들었습니다. 유저들의 유입도 초창기에 비해서 훨씬 많아졌고 트래픽도 많아졌습니다. 지금도 성장하고 있는 하쿠나는 앞으로도 트래픽은 점점 늘것이라고 예상하고 있습니다. 이렇게 **계속해서 서비스가 성장하기 때문에 나중을 위해서는 이 API의 성능상의 개선이 필요한 상황에 도달**하게 되었습니다. 그렇다면 입장하기 API는 어떤 상태였는지 데이터를 통해 확인해보도록 하겠습니다.

## APM을 통한 asis 상황 판단

하쿠나 서비스에서는 APM으로 하이퍼커넥트 회사 전체적으로 사용하는 APM인 [OpenTelemetry](https://opentelemetry.io/)를 이용하여 데이터를 수집하고 [kibana](https://www.elastic.co/kr/kibana/)를 통해 확인하고 있습니다. 아래의 이미지가 이를 통해 확인한 입장하기 API의 응답 latency의 평균값과 p95값입니다. 데이터를 보시면 실시간으로 응답을 제공한다고 보기에는 무리가 있는 수치라는 것을 확인하실 수 있습니다. **이러한 데이터를 근거로 현재 `입장하기 API`는 더 이상 라이브 스트리밍 서비스로서 유저에게 실시간성(Real-Time)을 제공하지 못하고 있다고 판단하였고 개선의 필요성에 대한 팀 내 논의를 통해 개선 작업을 진행하게되었습니다.**

<ul style="display: flex; justify-content: space-between; list-style: none; margin: 0 auto; padding: 0; max-width: 960px;">
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_asis_1.png" style="width: 480px; height: 220px;" alt="liveroom_asis_1" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">avg 그래프</p>
    </li> 
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_asis_2.png" style="width: 480px; height: 220px;" alt="liveroom_asis_2" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">p95 그래프</p>
    </li>
</ul>

## 괴물 메서드(Monster Method)

[`레거시 코드 활용 전략(Michael Feathers 저)`](https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=168779479)이라는 책에는 아래와 같은 문구가 나옵니다. 

> 대규모 메서드는 다루기 힘든 수준이라면, 괴물 메서드는 재앙이라고 부를 만하다. 괴물 메서드는 **너무나 길고 복잡해서 손대고 싶지 않은 메서드를 의미**한다.

하쿠나 서비스의 4년을 지탱해온 이 코드는 이 기간 동안 수많은 사람들에 의해서 수많은 부가적인 기능들이 추가되었고 괴물 메서드에서 괴물 클래스로... 이제는 끔찍한 괴물 API가 되어있었습니다. **입장 API** 코드를 둘러싼 상황은 아래와 같았습니다.

- 정확한 Context의 범위와 영향을 아는 사람이 없다.
- 테스트 코드가 전무하다.
- class 구조로 인해 순환 참조가 발생하기 쉽게되어있다.
- 많은 Domain Event가 무분별하게 발생한다.
- 제대로된 문서도 없다.

... 다시 보더라도 수정하는 사람 입장에서는 끔찍하네요. 😂

아래부터는 **라이브룸 입장 API**는 괴물 API라고 부르도록 하겠습니다.

# 괴물 API를 다루는 과정

저는 API를 개선할 때 아래의 3단계의 과정을 통해 진행하고 있습니다.

1. 분석하기
2. 리팩토링하기
3. 성능 개선하기

한 과정의 사이클이 마무리되면 다시 1번부터 3번의 과정을 반복해가며 개선을 진행합니다.

각 과정에 대해서는 아래에서 자세히 설명하도록 하겠습니다.

## 분석하기

위 3단계 중에서는 분석하기가 가장 중요한 부분입니다. 리팩토링, 그리고 개선하기에 투자되는 시간만큼, 또는 그 이상의 시간을 분석하기에 사용할 필요가 있습니다. 분석하기를 통해서 우리는 아래의 3가지 부분을 확정할 수 있기 때문입니다. **이후의 단계에서 어떤 부분을 리팩토링하고 어떤 부분을 개선할 것인지 또한 이 단계에서 윤곽이 잡히게 되기 때문에 다시 한번 굉장히 중요한 단계라고 강조드리고 싶습니다.**

1. **어디를** 수정해야하는지
2. **어떻게** 수정해야하는지
3. **어느정도로** 수정해야하는지

분석하기 단계에서는 APM을 통해 latency, throughput에 대한 분석을 진행합니다. 또한 해당 API의 현재 비즈니스 로직을 분석합니다.

### APM을 통한 분석

**APM을 통해서는 해당 API가 얼마나 호출되는지, 호출했을때 응답까지 걸리는 시간은 얼마인지, 다른 컴포넌트들과 얼마나 데이터를 주고 받는지 등의 정보를 알 수 있습니다.** 위에서 보았던 latency가 APM을 통해서 얻을 수 있었던 대표적인 데이터 정보입니다. 또한 1분 동안 얼마나 호출되는 지(TPM)의 정보도 아래 처럼 얻을 수 있습니다. 추가적으로 HyperConnect에서 사용하는 APM에서는 어떤 쿼리 및 명령어(RDBMS, Redis 등)가 실행되는지도 알 수 있습니다. ~~(기적의 APM)~~

<ul style="display: flex; justify-content: space-between; list-style: none; margin: 0 auto; padding: 0; max-width: 960px;">
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_analize_1.png" style="width: 480px; height: 220px;" alt="liveroom_analize_1" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">throughput</p>
    </li> 
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_analize_2.png" style="width: 360px;" alt="liveroom_analize_2" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">APM에 나온 JPA의 N + 1</p>
    </li>
</ul>

### 수도 코드(Pseudo-code) 작성하기

제가 분석하기 단계에서 두번째로 하는 일은 **API의 EndPoint를 기준으로 Reqeust가 들어오고 Response로 나가기까지의 로직을 하나하나 수도코드로 작성하는 것**입니다. **수도 코드란 프로그램 코드를 작성할 때 사용하기 위해, 프로그램의 진행 과정을 이해하기 쉬운 말로 단계별로 기록해 놓은 것**입니다. 사실 상당히 귀찮은 일이고 시간도 굉장히 잡아먹습니다. 하지만 API를 분석할 때 코드를 하나하나 따라가며 수도 코드를 작성하게되면 막연했던 API와 친해지고 좀 더 구체적으로 어디를 어떻게 수정해야할 지 고민하는 일에 큰 도움이 됩니다. 아래의 이미지들이 제가 괴물 API의 수도 코드를 한글로 작성한 것입니다. 저 같은 경우는 수도 코드 중간중간 수정 포인트를 진한 글씨로 표시하고 이후에 이 수도코드를 기반으로 수정을 시작합니다.

<!-- 요건 약간 보안적인 부분도 걸린다.. 줄좀 그어야할듯? -->

![liveroom_analize_3](/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_analize_3.png)

## 리팩토링하기

괴물 API의 코드에 선뜻 손을 대는 것은 쉽지 않습니다. 위에서와 같이 수도 코드를 이용하여 코드 분석을 마무리하였다고 해서 바로 코드 변경을 진행했을때 의도한 올바른 수정이 이루어 질것이라고 자신있게 말하기는 어렵습니다. 우리는 이 코드가 올바르게 수정될 것이라는 확신이 필요합니다. 그렇기 때문에 우선 어느 정도 코드의 리팩토링을 진행하는 것으로 코드에 확신을 가질 필요가 있습니다.

**리팩토링이란 결과의 변경 없이 코드의 구조를 재조정하는 것**을 말합니다. 리팩토링도 확실성을 가지고 할 필요가 있습니다. 리팩토링의 확실성을 주는 것이 바로 테스트 코드입니다. 하지만 괴물 메서드에서 파생된 이 괴물 API는 테스트 코드가 없습니다. 테스트 코드는 수동 리팩토링을 할 때 대표적으로 아래와 같은 실수를 방지해줍니다.

- 추출한 메서드에서 전달받아야할 파라미터를 로컬 변수로 선언해버리는 일
- 추출한 메서드에서 동일한 타입의 파라미터를 잘못 전달하는 일

### 테스트 코드로 리팩토링에 확실성 부여하기

아래의 코드를 보면 어디가 잘못되었는지 알 수 있으신가요 ?

```kotlin
@Transactional
fun publishLiveRoomParticipantsChangedBrokerEvent(
    userId: Long,
    liveRoomId: Long
) {
    val participant = liveRoomParticipantService.getParticipant(liveRoomId, userId)
    [...하략...]
```

그냥 눈으로 봐서는 알 수 없습니다. 잘못된 부분은 파라미터의 전달 부분입니다. 사실 `liveRoomParticipantService#getParticipant` 메서드는 userId, liveRoomId를 순서로 파라미터를 받아야하는데 위 코드에서는 잘못되었습니다. 테스트 코드를 작성하면 이러한 리팩토링을 진행할 때 명확하게 잘 리팩토링을 진행했다라는 사실을 알려줄 수 있습니다. 간단하게 아래와 같은 테스트 코드를 짠다고 해보겠습니다. 아래의 코드는 위 리팩토링에 실수가 없다는 사실을 증명해줍니다. 저희 팀에서는 테스트 프레임워크로는 [JUnit5](https://junit.org/junit5/)을 사용하고 있으며 UnitTest mocking에는 [mockk](https://mockk.io/)를 이용하고 있습니다.

```kotlin
@Test
fun `liveRoomEntranceAndLeaveService_exactly_call_liveRoomParticipantService_getParticipant`() {
    // given
    val userId = 1L
    val liveRoomId = 2L
    
    // when 
    liveRoomEntranceAndLeaveService.publishLiveRoomParticipantsChangedBrokerEvent(userId, liveRoomId)
    
    // then
    verify(exactly = 1) { liveRoomParticipantService.getParticipant(userId, liveRoomId) } // getParticipant 메서드가 정확한 파라미터를 가지고 정확하게 1번 호출된 다는 사실을 검증합니다.
}
```

이렇게 리팩토링을 하는 과정에서의 실수를 방지하기 위해서라도 테스트 코드는 반드시 작성하도록 합시다. kotlin은 NamedParameter가 있으니 괜찮다고 안심하면 안됩니다. 어느 정도 도움은 되겠지만 결국 같은 타입을 잘못 전달하는 실수까지는 막을 수 없습니다.

### 마법의 툴 Intellij로 리팩토링에 확실성 부여하기

그런데 리팩토링 하고자하는 메서드가 너무 복잡해서 도저히 테스트 코드를 짤 엄두가 안날 경우가 있습니다. (대부분의 괴물 메서드들이 그렇지요) 이럴 경우 어떻게 확신을 가지고 리팩토링을 할 수 있을까요 ? **실수를 줄이는 방법은 사람의 손을 타지 않게 하는 것입니다.** Intellij를 이용하고 있으시다면 Intellij의 refactoring 기능을 이용하면 규모가 큰 메서드를 어느 정도 쪼개버릴 수 있습니다. 규모가 큰 괴물 메서드를 여러 메서드로 쪼갠다면 이전보다는 테스트 코드 작성이 감당할 수 있는 난이도가 됩니다. 그 후 테스트 코드를 쪼개 놓은 메서드 별로 작성하면 되겠죠.

Intellij의 경우 대표적으로 변수 추출하기, 메서드 추출하기, 클래스 추출하기 등을 할 수 있습니다. 여기서는 메서드 추출하기만 보여드리도록 하겠습니다.

### 메서드 추출하기

아래는 샘플 코드입니다. 아래의 코드는 한 메서드에서 데이터의 검증 및 일반적인 비즈니스 로직이 있으며 마지막에 domain event를 발행하는 형식을 가지고 있습니다. 여기서 domain event를 발행하는 로직만 메서드 추출을 진행해보도록 하겠습니다.

```kotlin
fun validateAndPublishEvent(liveRoomId: Long, userId: Long) {
    
    [...데이터 검증...]

    [...비즈니스 로직...]

    val event = LiveRoomTopParticipantsChangedBrokerEvent(liveRoomId, userId)

    domainEventPublisher.publishEvent(event)
}
```

아래 이미지를 보시면 Intellij를 통해서 리팩토링 할 수 있는 목록들입니다. 자주 사용하는 리팩토링 방법들은 단축키를 외워두시면 더 빠르게 진행할 수 있습니다.

![liveroom_extract_method_1](/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_extract_method_1.png)

```kotlin
private fun validateAndPublishEvent(liveRoomId: Long, userId: Long) {
    publishEvent(liveRoomId, userId)
}

private fun publishEvent(liveRoomId: Long, userId: Long) {
    val event = LiveRoomTopParticipantsChangedBrokerEvent(
        liveRoomId = liveRoomId,
        userId = userId
    )
    domainEventPublisher.publishEvent(event)
}
```

이렇게 추출을 하고나면 추출된 메서드는 이후 테스트를 작성할 때 [mockk의 dynamic call](https://mockk.io/#private-functions-mocking--dynamic-calls) 등을 이용하여 private functions mocking을하여 해당 메서드에 의존없는 테스트를 작성 할 수 있게 됩니다. 또한 별도로 reflection 등을 통해서 해당 메서드만 테스트 할 수도 있습니다. 이러한 기법들은 다음에 또 자세히 전달드리는 시간을 가져보도록 하겠습니다.

## 성능 개선하기

서비스의 성장에 따라 이전에는 성능에 문제를 주지 않았던 부분이 성능상에 영향을 주기 시작합니다. 입장하기 API 뿐만 아니라 다른 케이스에서도 이런 경우를 더러 확인했었는데요. 경험상 대부분의 원인은 아래의 케이스로 귀결되는 것을 확인했습니다. 

- JPA의 N + 1
- 로직적 N + 1

이번 글에서는 로직적 N + 1에서 대해서 좀 더 자세히 이야기해보도록 하겠습니다.

### 로직적 N + 1 해결하기

JPA에서 N + 1이 어떤 현상인지 간단히 말씀드리면 **테이블간 join이 있는 경우 데이터를 가져올 때 main 테이블을 1번 쿼리하고 sub 테이블을 main 테이블에서 가져온 N 개의 row에 만큼 순차적으로 다시 쿼리해서 가져오는 현상**을 말합니다. 이때 1번의 쿼리로 될 부분이 N + 1번 일어나기 때문에 성능상 loss가 생기게 됩니다. 일반적인 비즈니스 로직에서도 이렇게 JPA에서의 N + 1과 유사한 현상이 발생하여 성능적인 loss를 일으킬 수 있기때문에 이는 피하는것이 좋습니다. 

이러한 현상은 N개의 데이터와 M개의 데이터를 서로 다른 DataSource에서 가져와 매핑할 때 주로 발생합니다. 저희 서비스에서 문제가 된 예를 하나 들어 보도록 하겠습니다. 메인정보는 RDB에 있고 추가적으로 원하는 부가적인 정보가 Redis에 있었던 경우입니다.

1. RDB에서 N개의 데이터의 집합을 가져옵니다.
2. N개의 데이터를 순환하며 Redis에 정보를 요청합니다.

굉장히 심플한 로직입니다. 논리적으로 문제는 없고, 실제로도 의도한 결과를 제공합니다. 하지만 2번에서 루프를 순환을하며 Redis에 한건씩 조회하는 것은 데이터의 규모 N이 커질 경우 문제가 될 수 있습니다. 모두가 알고 있는 것처럼 Redis는 상당히 빠른 인메모리 시스템입니다. 진짜 빠릅니다. [벤치마킹](https://redis.io/topics/benchmarks)에 따르면 100Byte key-value 기준 초당 10만 명령어도 처리할 수 있다고합니다. **하지만 실제 서비스에서 레디스에 도달히기 위한 네트워크 전송은 결코 빠르지 않다라는 사실을 잊어버리면 안됩니다. N이 100이라고하면 200번의 네트워크 전송이 있는 것입니다.** 

![liveroom_n_plus_one_2]({{"/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_n_plus_one_2.png"}}){: height="300px" .center-image }

이유를 알았으니 해결 방법은 간단합니다. **해결 방법은 순환하지 않고 한번에 데이터를 가져온 후 CPU 자원을 이용하여 어플리케이션 내부에서 매핑하는 것입니다.** 그렇다면 로직은 아래처럼 변경될 것입니다.

1. RDB에서 N개의 데이터의 집합을 가져옵니다.
2. M개의 데이터 집합을 **Redis에서 한번에(한번이 아니더라도 적은 횟수로)** 가져옵니다.
3. 두 데이터 집합을 Map으로 만듭니다.
4. 더 작은 데이터 집합을 순회하며 상대방 데이터 집합에서 데이터를 매핑합니다.

![liveroom_n_plus_one_3]({{"/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_n_plus_one_3.png"}}){: height="300px" .center-image }

### 동기적으로 처리할 부분과 비동기적으로 처리할 이벤트 나누기

성능 개선을 위한 JPA의 N+1 제거, 로직적 N+1 제거에 이어서 진행한 **3번째 작업은 괴물 API의 로직중 동기적으로 반드시 처리해야하는 로직과 그렇지 않고 비동기적으로 처리할 수 있는 로직을 나누는 작업**이었습니다. API를 호출했을 때 해당 API가 처리하는 로직을 뜯어보면 그 API가 반드시 해야하는 일이 있고 파생되어 이루어지는 일이 있습니다. 그리고 즉시 처리되어야하는 일과 조금은 천천히 처리되어도 되는 일이 있습니다. 그렇기 때문에 API에서 요청을 받고 응답을 반환하는 사이에 모든 로직을 동기적으로 처리할 필요는 없으며 이를 적절히 나눈다면 유저가 좀 더 빠른 경험을 얻을 수 있습니다. 

이 괴물 API는 아쉽게도 이런 부분이 고려가 잘 되어있지 않았고 모든 로직이 동기적으로 이루어지고 있었습니다. 간단히 보여드리면 아래와 같은 API는 아래와 같은 flow을 가지고 있었습니다. 동기적으로 순차 처리가 되기 때문에 유저는 아래 모든 로직이 완료되기 전에는 응답을 받을 수 없습니다.

![liveroom_async_1]({{"/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_async_1.png"}}){: height="300px" .center-image }

따라서 로직을 아래와 같이 변경하였습니다. 실제로 입장 API에 반드시 필요한 로직을 제외한 로직은 비동기적으로 처리될 수 있도록 하였습니다. 이렇게 변경함으로써 성능적 향상 뿐만 아니라 입장 API는 입장이라는 핵심 기능에만 집중할 수 있도록 처리하여 이후의 유지보수에도 좋은 영향을 줄 수 있습니다. 

추가적으로 `입장 한 방의 정보를 업데이트 하고 해당 방의 유저들에게 전달` 로직은 이벤트 처리 로직으로 빠른 시간내에 입장인원이 많아지면 동일한 비즈니스로직이 여러번 실행되게 됩니다. 이렇게 중복적으로 로직이 처리되는 로직에 대해서 [`debouncing`](https://levelup.gitconnected.com/debounce-in-javascript-improve-your-applications-performance-5b01855e086) 적용하는 작업도 진행을 하였습니다.

![liveroom_async_2]({{"/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_async_2.png"}}){: height="300px" .center-image }

## 괴물 API와의 사투 끝에 얻어낸 결과

이렇게 괴물 API와 싸워내어 아래와 같은 결과를 얻어내었습니다.

<ul style="display: flex; justify-content: space-between; list-style: none; margin: 0 auto; padding: 0; max-width: 960px;">
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_tobe_1.png" style="width: 480px; height: 220px;" alt="liveroom_tobe_1" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">avg 그래프</p>
    </li> 
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_tobe_2.png" style="width: 480px; height: 220px;" alt="liveroom_tobe_2" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">p95 그래프</p>
    </li>
</ul>

성능적 향상만 놓고 봤을 때, **동일 API에 대해서 Latency의 평균, p95 모두 대략 85% 가량 성능 개선** 되었습니다. 

![liveroom_tobe_3]({{"/assets/2022-03-02-develop-liveroom-entrance-on-hakuna-1/liveroom_tobe_3.png"}}){: height="300px" .center-image }

그리고 추가적으로 위의 그래프는 p99 그래프 입니다. 이 그래프는 스파이크 등을 분석하여 API의 안정성을 확인해줍니다. 이 그래프를 보았을 때 스파이크가 없다라는 것이 확인이 되어집니다. 이를 통해 **안정성 또한 개선**되었다고 판단할 수 있습니다.

# 마무리

오늘은 간단하게 하쿠나 서비스에 대한 설명과 함께 어떻게 하쿠나 백엔드팀에서는 오래된 괴물 API를 개선하는지 그 과정과 결과를 함께 공유하는 자리를 가져보았습니다.

서비스가 성장함에 따라 갖춰야하는 능력도 바뀌게 됩니다. 저희는 빠르게 지속적으로 성장해야함과 더불어 안정화를 찾아가는 단계에 접어들었습니다. 개인적으로 **서비스의 성장과 본인의 성장**은 별개라고 생각합니다. 하지만 이 **두가지를 모두 만족할 수 있는 시기**가 있다고 생각하는데요. **그게 서비스가 안정화를 찾아가는 시기이고 그게 바로 지금 하쿠나의 시기**라고 생각합니다. :)

기가막힌 타이밍으로 서비스의 성장과 개인 성장 모두 이룰 수 있는 하쿠나팀의 채용공고가 올라와 있습니다. 많은지원 부탁드립니다. 🙏 [Java Backend Software Engineer(Hakuna)
](https://career.hyperconnect.com/job/bfd1a67a-3f4c-4774-8ceb-b6b97fa4b5a1/) 

감사합니다.

# References

[1] Working Effectively with Legacy Code

[2] Clean Architecture

[3] [https://en.wikipedia.org/wiki/Lehman%27s_laws_of_software_evolution](https://en.wikipedia.org/wiki/Lehman%27s_laws_of_software_evolution)

[4] [위키피디아_의사코드](https://ko.wikipedia.org/wiki/%EC%9D%98%EC%82%AC%EC%BD%94%EB%93%9C)

[5] [위키피디아_리팩토링](https://ko.wikipedia.org/wiki/%EB%A6%AC%ED%8C%A9%ED%84%B0%EB%A7%81)

[6] [https://levelup.gitconnected.com/debounce-in-javascript-improve-your-applications-performance-5b01855e086](https://levelup.gitconnected.com/debounce-in-javascript-improve-your-applications-performance-5b01855e086)

[7] [https://mockk.io/#private-functions-mocking--dynamic-calls](https://mockk.io/#private-functions-mocking--dynamic-calls)

[8] [https://www.imperva.com/learn/performance/round-trip-time-rtt/](https://www.imperva.com/learn/performance/round-trip-time-rtt/)

[9] [https://redis.io/topics/benchmarks](https://redis.io/topics/benchmarks)
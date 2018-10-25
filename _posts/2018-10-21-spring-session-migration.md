---
layout: post
date: 2018-10-21
title: "Spring Session 으로의 마이그레이션 작업기"
author: devin
published: true
lang: ko
excerpt: Spring Session 을 프로덕션 환경에 적용하면서 겪었던 일들을 소개합니다.
tags: spring spring-session
---

## TL;DR

* Spring Session Redis 이 지원해주는 Session Event 구현이 Redis 에 부하를 줄 수 있어 사용하지 않았습니다.
* 세션 읽기/쓰기 때 Redis 부하를 줄이기 위해 간단한 최적화를 하였습니다.

## 들어가며

아자르 API 서버는 Spring + Jetty 조합을 사용하고 있습니다. 그리고 세션 관리는 [jetty-session-redis](https://github.com/ovea-deprecated/jetty-session-redis)
라는 모듈을 fork 해서 사용하고 있었습니다. 그런데 Spring Boot 로 마이그레이션을 하게 되면서 Jetty 버전 문제 등으로 위 모듈을 그대로 사용하기 어려워지게 되었습니다.
그리하여 이를 대체할 수 있는 모듈을 찾고 있었는데, Spring Session 을 사용하면 쉽게 대체될 것이라 판단했습니다. 그 이유는
[HttpSession Integration](https://docs.spring.io/spring-session/docs/current/reference/html5/#httpsession) 이 손쉽게 되었고,
웹 서버에 의존적이지 않고, 커뮤니티의 지원을 비교적 손쉽게 받을 수 있을 것이라 생각되었기 때문입니다.

## 작업을 시작하기 전

작업을 준비하면서 사용 사례를 조사하다가 [Production Considerations for Spring Session Redis in Cloud-Native Environments](https://medium.com/@odedia/production-considerations-for-spring-session-redis-in-cloud-native-environments-bd6aee3b7d34)
라는 글을 찾게 되었는데, 그 내용을 간단히 요약하면 아래와 같습니다.

> * Spring Session Redis 에서 만료된 세션들을 정리하는 루틴이 매 분 실행된다.
> 그런데 이 루틴이 많은 수의 Redis Operation 을 유발하는데, 서버가 여러 대인 경우에 이것이 서버 수만큼 배로 증폭된다.
>
> * 한편 Session Event 를 구현하기 위해서 [Redis Keyspace Notification](https://redis.io/topics/notifications) 을 활용하는데,
> 세션이 만료되거나 삭제될 때마다 세션을 다시 한 번 Redis 로부터 가져오는 로직이 있다. 이 역시 많은 수의 Redis Operation 을
> 발생시키는 데에 기여를 하고 있으며, 역시 서버 수만큼 배로 증폭된다.

일단 위 로직이 하는 일이 무엇이며, Azar 서버에서도 필요한 구현인지 먼저 확인을 해보기로 했습니다.

## 세션 만료 처리

위에서 언급한 로직의 목적을 파악하기 위해 Spring Session Redis 의 해당 부분을 살펴본 결과,
Servlet Session Event 를 구현하기 위한 것으로 파악되었습니다. 그런데 구현이 약간 복잡하게 되어 있었습니다.

```java
public void cleanExpiredSessions() {
    long now = System.currentTimeMillis();
    long prevMin = roundDownMinute(now);

    if (logger.isDebugEnabled()) {
        logger.debug("Cleaning up sessions expiring at " + new Date(prevMin));
    }

    String expirationKey = getExpirationKey(prevMin);
    Set<Object> sessionsToExpire = this.redis.boundSetOps(expirationKey).members();
    this.redis.delete(expirationKey);
    for (Object session : sessionsToExpire) {
        String sessionKey = getSessionKey((String) session);
        touch(sessionKey);
    }
}
```

* `expirationKey` 에는 어떤 세션이 만료될 것인지에 대한 Set 이 저장됩니다.
* 새로운 세션이 생기거나 기존 세션의 만료 시각이 변경되면 이 Set 에도 반영이 되어야 합니다.
* 매 분 이 Set 의 원소들을 순회하면서 Redis 에 `EXISTS` 커맨드를 보냅니다.

왜 이런 일을 해야 하는가에 대한 설명은 [이 곳](https://docs.spring.io/spring-session/docs/current-SNAPSHOT/reference/html5/#api-redisoperationssessionrepository-expiration)
에 있습니다. 간단히 요약을 하면 세션 만료에 대한 Redis Notification 이 제 시간에 오지 않을 수 있으니, 세션들의 만료 시각을 직접 트래킹하다가
만료될 시점에 Redis 에 touch (`EXISTS`) 를 해주면 Redis Notification 을 놓치는 일 없이 받을 수가 있다는 것입니다. 다만 위의 구현이 Redis Operation 수를 증폭시키는 데에 기여하고 있고,
Azar 서버에서는 Session Event 를 사용하는 부분이 없었기 때문에, 이 로직을 남겨둘 필요는 없었습니다.

따라서 `RedisHttpSessionConfiguration` 의 설정에서
`RedisOperationsSessionRepository#cleanupExpiredSessions` 의 스케쥴링을 하지 않도록 변경하고,
Redis Keyspace Notification 역시 받을 필요가 없었기 때문에 `configureRedisAction` 를 `ConfigureRedisAction.NO_OP`
으로 변경하였습니다.

```java
@Override
public void configureTasks(ScheduledTaskRegistrar taskRegistrar) {
    // No-op
}

@Bean
public static ConfigureRedisAction configureRedisAction() {
    return ConfigureRedisAction.NO_OP;
}
```

## 세션 인덱스

Spring Session 에서는 [`FindByIndexNameSessionRepository`](https://docs.spring.io/spring-session/docs/current/api/org/springframework/session/FindByIndexNameSessionRepository.html) 라는 것을 제공하고 있습니다.
Spring Session Redis 역시 이를 구현하고 있는데, 이의 역할은 이름에서도 드러나듯이 이름 (ex. username) 으로 세션을 가져올 수
있게 해 주는 인터페이스입니다.

Spring Session Redis 의 구현은 간단합니다. `spring:session:index:FindByIndexNameSessionRepository.PRINCIPAL_NAME_INDEX_NAME:$username` 
이라는 Set 을 만들고, 원소로서 세션의 ID 를 넣어두는 것입니다. 그리고 세션이 만료된 경우에는 Set 에서 제거하면 됩니다.
그런데 세션 만료 처리 로직을 비활성화시키게 되면서 인덱스 제거도 제대로 이루어지지 않게 되어 인덱스가 계속 늘어날 수밖에 없는 문제가 생기게 되었습니다.

Azar 서버에서는 이 기능 역시 필요가 없었기 때문에 이를 비활성화시키고자 하였으나, 이는 `RedisOperationsSessionRepository` 구현에서
분리될 수 없는 부분이었습니다. 이는 `RedisOperationsSessionRepository` 를 고쳐서 사용하게 되는 계기를 제공했습니다.
이 외에 또 하나의 중요한 이유가 있는데, 바로 아래에서 설명하도록 하겠습니다.

## Redis Commands

최초에 저희는 간단히 Spring Session Redis 를 수정하지 않은 버전을 먼저 내보내 보았습니다. 실서버에 1% 트래픽을 대상으로 배포를 해본 결과는 아래와 같았습니다.

![before_optimization_redis_commands]({{ "/assets/2018-10-21-spring-session-migration/before_optimization_redis_commands.png" | absolute_url }})

Get Type 커맨드는 많으면 분당 2.5만, Set Type 커맨드는 많으면 분당 5만까지 높아지는 모습을 볼 수 있었습니다.
만약 100% 배포를 실시했다면 약 100배가 될테니 각각 250만, 500만 번의 커맨드가 실행되었을 것이라 예상할 수 있습니다.

Spring Session Redis 에서는 기본적으로는 매 요청마다 세션을 불러오고 있습니다. 또한 한 요청 내에서 여러 번 세션을 가져오는 경우가 있는데,
이 때도 매번 Redis 에서 새로운 값을 불러오고 있었습니다. 이렇게 불러오는 것이 일관성이 있을 수 있지만,
저희는 아래와 같은 간단한 전략으로 Redis 로 보내는 커맨드 수를 많이 낮출 수 있을 것이라 판단했습니다.

- 어플리케이션 서버에서 세션을 캐싱하면 한 요청 내에서 여러 번 Redis 로 요청을 보내는 일은 줄어들 것입니다.
- Session Affinity (a.k.a Sticky Session) 기능을 사용하면 여러 요청 사이에서도 세션을 캐싱할 수 있을 것입니다.
- 자주 바뀌지만 어플리케이션에 필수적이지 않은 몇 가지 값들은 매번 Redis 에 쓰지 않아도 치명적이지 않을 것입니다.

위 전략을 실제로 적용하기 위해 `RedisOperationsSessionRepository` 의 구현을 고치기로 결정하였습니다.

## Custom RedisOperationsSessionRepository

`SessionRepository` 를 직접 구현하게 되면서, 앞서 논의했던 대로 세션 만료 처리 부분은 구현에서 제외시키고
마찬가지로 세션 인덱스 부분도 구현에서 제외시키는 것으로 Scalability 문제를 해결할 수 있게 되었습니다.
처음에는 커뮤니티의 힘을 받아 금방 해결될 줄 알았는데 여기까지 와버리고 말았습니다. 기본적인 구현은
`RedisOperationsSessionRepository` 을 참고하되, 몇 가지 부분만 수정하였습니다.

### 세션 로컬 캐싱

저희는 이미 로드 밸런서의 Session Affinity 기능을 사용하고 있었기 때문에 로컬에 세션을 캐싱하는 것이 큰 작업 없이
바로 가능했습니다. Repository 내부에 짧은 만료 시간을 가진 [Caffeine](https://github.com/ben-manes/caffeine) 캐시를 두고 이를 사용했습니다.
내부에 캐시를 하게 되면 여러 스레드에서 동시에 접근할 수 있기 때문에 thread-safe 하게 코드를 작성하는 것에 주의를 기울였습니다.

### Flush 주기 조절

Spring 의 Session 인터페이스에서 제공되는 값 중에 `lastAccessedTime` 이라는 값이 있습니다.
이런 값들은 세션 접근 시마다 바뀌지만 서버에서 중요하게 사용되는 곳이 없었습니다.
바로 바로 반영이 되어야 하는 값들은 바로 flush 를 하고, 앞선 값과 같은 메타성 데이터들은
따로 prefix 를 두어서 관리를 함과 동시에 적절한 flush 주기를 두어서 주기가 돌아올 때마다 메타성 데이터를 포함한
모든 변경된 값들을 세션의 모든 값을 Redis 에 쓰도록 하였습니다.

Spring Session Redis 에서는 `Session#setAttribute` 를 사용하면 이를 delta 라는 Map 에 관리를 하고
이후에 flush 를 하는 방식을 사용하는데 저희도 이런 메커니즘으로 바로 flush 를 해야할 값과 아닌 값을 구분했습니다.

## 서버 배포

이번에 세션 모듈을 변경하면서 기존 세션을 새 서버에서는 이용할 수 없지만 Session Affinity 기능을 사용하고 있었기 때문에
새 서버를 내보내는 것 자체는 문제가 되지 않았습니다. 그러나 만약 새로운 서버에서 문제가 될 부분이 있는 경우에 롤백을 진행해야 하는데,
이 때는 새로운 세션을 가진 유저들도 어쩔 수 없이 기존 서버로 연결할 수밖에 없는데, 이 경우에 유저들이 모두 로그아웃이 되고
새로 로그인을 해야 하는 경우가 생길 수 있습니다. 리스크를 최소화하기 위해 새 서버로의 트래픽 비율을 로드 밸런서에서 별도로 조정을 하는 것으로
장애 발생 가능성을 최소화하고자 했습니다.

## 결과

성공적으로 전체 배포를 완료한 이후에 나타난 결과는 아래와 같습니다.

![after_optimization_redis_commands]({{ "/assets/2018-10-21-spring-session-migration/after_optimization_redis_commands.png" | absolute_url }})

서버가 받는 트래픽이 100배가 되었음에도 불구하고, Get Type 커맨드 수가 최적화 하지 않은 구현으로 1% 만 배포했을 때의 2배 정도밖에 높아지지 않았습니다.
마찬가지로 Set Type 커맨드 수 역시 약 4배 정도 높아진 데에 그쳤습니다. 또한 기존 구현을 사용하면 나타날 수 있는 Redis Command 수 그래프에 피크도 없습니다.

위 결과로 판단할 때 한 요청에서 여러 번 세션을 가져오는 경우가 많았고, 실질적인 세션 값이 변경되지 않았는데
매번 lastAccessTime 과 같은 값을 반영하기 위해 Set Type 커맨드 수가 많이 사용되었음을 알 수 있습니다.

## 맺으며

Spring Session Redis 를 사용하면 쉽게 세션 클러스터링을 할 수 있지만 Azar 정도의 트래픽에서는 유명한 프로젝트라도
프로덕션 환경에서 사용할 때 여러 방면에서 검토를 해야 합니다. 저희는 사실상 Spring Session Redis 가 아니라
Spring Session + Custom Session Repository 를 쓰고 있는 셈이지만 기존 구현을 차용했기 때문에
시간과 노력을 많이 아낄 수 있었고 그 이후로도 패치한 적 없을 정도로 큰 문제 없이 사용하고 있습니다.
세션 클러스터링을 위해 Spring Session Redis 를 고려 중이신 분들께 이 작업기가 도움이 되었으면 좋겠습니다.

## References

* [Spring Session](https://spring.io/projects/spring-session)
* [Spring Session: RedisOperationsSessionRepository](https://docs.spring.io/spring-session/docs/current-SNAPSHOT/reference/html5/#api-redisoperationssessionrepository)
* [Production Considerations for Spring Session Redis in Cloud-Native Environments](https://medium.com/@odedia/production-considerations-for-spring-session-redis-in-cloud-native-environments-bd6aee3b7d34)
* [Why does Spring Session use spring:session:expirations?](https://github.com/spring-projects/spring-session/issues/92)
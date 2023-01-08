---
layout: post
date: 2023-01-09
title: Spring Session + Custom Session Repository 기반 세션 저장소의 메모리 누수 해결
author: dante.r
tags: spring-session session memory-leak 
excerpt: Spring Session + Custom Session Repository 를 사용할 때 발생한 메모리 누수 현상을 해결한 경험을 공유합니다.
last_modified_at: 2023-01-09
---

안녕하세요, Azar API Dev Team의 Dante.R 입니다.

이 글에서는 팀에서 Spring Session + Custom Session Repository 기반 세션 저장소의 메모리 누수 현상을 해결한 경험을 공유합니다.

# 배경
아자르는 유저 정보를 저장하기 위해 레디스 기반의 Spring Session + Custom Session Repository 를 사용하고 있습니다.[[1]](https://hyperconnect.github.io/2018/10/21/spring-session-migration.html) 

어느 날부터 트래픽이 최고점인 시간대에 세션 레디스 클러스터의 메모리 사용량이 85% 이상이라는 alert 이 연속해서 발생했습니다. 지난 12개월간의 메모리 사용량 지표를 확인해보니 메모리 사용량이 선형으로 증가함을 확인할 수 있었습니다.
 
세션 레디스 클러스터의 메모리 사용량이 트래픽에 비례하여 증가한 것이 아니었기 때문에, 이는 곧 메모리 누수 현상이 발생하고 있음을 의미합니다. <br>

어떤 원인으로 레디스 세션 클러스터에 메모리 누수가 발생한 것일까요?

# Spring Session 동작 원리
문제의 원인을 살펴보기 전, Spring Session 의 동작 원리를 간단히 살펴보겠습니다.

Spring Session 라이브러리는 HttpSession 을 Spring Session 으로 변환시켜주는 역할을 합니다. 

HttpSession 은 Tomcat 과 같은 단일 서버의 application container 에 저장되어, 여러 개의 서버 인스턴스를 사용하는 경우 세션 동기화 작업(= 세션 클러스터링)을 추가적으로 해줘야 합니다. Spring Session 은 HttpSession 을 변환해 공통 저장소에 저장하고 이를 기반으로 동작함으로써 추가 작업없이 세션 클러스터링 기능을 지원해주는 라이브러리 입니다.[[2]](https://spring.io/projects/spring-session) 

Spring Session 라이브러리는 `@EnableSpringHttpSession` 어노테이션을 통해 HttpSession 을 Spring Session 으로 변환합니다. 해당 어노테이션을 선언하면 `springSessionRepositoryFilter` 라는 Bean 이 생성됩니다. 

SpringSessionRepositoryFilter 는 HttpServletRequest 를 `SessionRepositoryRequestWrapper` 로 래핑하고, 필터 체인의 다음 필터에 래핑된 SessionRepositoryFilter 를 전달합니다. 그리고 필터 로직 수행이 완료되면 SessionRepository 를 사용하여 해당 세션을 저장합니다.

```java
protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain) throws ServletException, IOException {
    request.setAttribute(SESSION_REPOSITORY_ATTR, this.sessionRepository);
    SessionRepositoryFilter<S>.SessionRepositoryRequestWrapper wrappedRequest = new SessionRepositoryFilter.SessionRepositoryRequestWrapper(request, response);
    SessionRepositoryFilter.SessionRepositoryResponseWrapper wrappedResponse = new SessionRepositoryFilter.SessionRepositoryResponseWrapper(wrappedRequest, response);

    try {
        filterChain.doFilter(wrappedRequest, wrappedResponse);
    } finally {
        wrappedRequest.commitSession();
    }
}

private void commitSession() {
    SessionRepositoryFilter<S>.SessionRepositoryRequestWrapper.HttpSessionWrapper wrappedSession = this.getCurrentSession();
    if (wrappedSession == null) {
        if (this.isInvalidateClientSession()) {
            SessionRepositoryFilter.this.httpSessionIdResolver.expireSession(this, this.response);
        }
    } else {
        S session = wrappedSession.getSession();
        this.clearRequestedSessionCache();
        SessionRepositoryFilter.this.sessionRepository.save(session);
        String sessionId = session.getId();
        if (!this.isRequestedSessionIdValid() || !sessionId.equals(this.getRequestedSessionId())) {
            SessionRepositoryFilter.this.httpSessionIdResolver.setSessionId(this, this.response, sessionId);
        }
    }

}
```

# Custom Session Repository
아자르에서 사용하고 있는 Custom Session Repository 의 특징에 대해 간략하게 말씀드리겠습니다.

1. 커스텀 필터에서 Spring Session 을 통해 세션 정보를 얻고 ThreadLocal 에 저장합니다. 인가가 필요한 API에서 해당 세션 정보를 꺼내서 사용합니다. 이렇게 요청 스레드에 유저 세션을 바인딩 해두면 Redis Operation 을 줄일 수 있고 애플리케이션 로그에서 세션 컨텍스트를 추적할 수 있다는 장점이 있습니다.
    ```java
    private static final ThreadLocal<UserSession> threadUserSession = new ThreadLocal<UserSession>();

    public static void setUserSession(UserSession userSession) {
        ...
        threadUserSession.set(userSession);
    }
    ```
2. 유저의 세션 정보를 담은 UserSession 객체를 HttpSession 에 저장합니다.
3. 요청 트랜잭션을 수행하면서 변경된 세션 정보를 delta 로 저장하고, 이를 아자르에서 생성한 UserSessionFilter 의 종료부에서 레디스에 저장합니다. 하나의 요청에서 세션에 저장된 값이 여러 번 변경될 수 있어 변경사항을 모두 기록하고, 한번에 변경사항을 세션 레디스에 저장합니다. Spring Session 공식 문서에서 delta 형태로 저장하는 것을 권장하기 때문에 이와 같이 구현했습니다.[[3]](https://docs.spring.io/spring-session/docs/2.2.x/reference/html/custom-sessionrepository.html)
    ```java
    @Override
    public void save(AzarSession azarSession) {
        ...
        // delta 값을 저장
        azarSession.saveDelta();
        ...
    }
    
    ...
    public void doFilter(ServletRequest servletRequest, ServletResponse servletResponse, FilterChain filterChain) {
        ...
        try {
            ...
        } finally {
            HttpSession httpSession = request.getSession(false);
            // userSession 정보에 변경사항이 있을 때만, userSession 정보를 저장
            if (httpSession != null && UserSessionUtils.isDirty()) {
                UserSessionUtils.persistUserSession(httpSession);
            }
        }
    }
    ...

    public static void persistUserSession(HttpSession httpSession) {
        ...
        UserSession userSession = threadUserSession.get();
        httpSession.setAttribute(SESSION_KEY, userSession);
        httpSession.setAttribute("lastModified", System.currentTimeMillis());
        ...
    }
    ```
4. 세션 만료에 대한 Redis Notification 관련 기능을 Off 했습니다. 불필요한 Redis Operation 를 줄이고, Session Event 를 사용하지 않기 때문입니다.

# TTL 이 설정되어 있지 않은 세션 정보
세션 정보를 레디스에 저장할 때, TTL(Time-To-Live) 을 설정해 저장하기 때문에 세션 정보가 일정 기간이 지나면 삭제가 되어야 합니다. 메모리 누수 현상이 발생했을 때는 이 TTL 설정이 의도한 대로 적용되지 않아서 삭제되지 않은 세션 정보가 존재하는 것임을 의심할 수 있습니다.

이를 확인하기 위해, 현재 레디스 내에서 TTL 이 설정되어 있지 않은 세션 정보가 존재하는지 확인하기 위해 스크립트를 돌려보았습니다. TTL 이 걸리지 않은 모든 키를 찾아야 하기 때문에 **전체 검색** 을 해야 합니다. `KEYS` 명령어는 한번에 모든 키를 스캔해서 조회를 해야하기 때문에, 이를 프로덕션 환경의 master 노드에서 돌리면 전체 시스템에서 장애가 날 수 있습니다. replica 노드에서 `KEYS` 명령어를 실행할 수 있지만, 아래와 같은 이유로 해당 명령어를 사용하지 않았습니다.
1. replica 노드에 접속한 다른 클라이언트의 명령어가 수행될 수 없습니다.
2. 만약 master 노드에서 장애가 발생해 replica 가 master 로 승격을 한다면 어떤 문제가 발생할 지 알 수 없습니다.
3. 수억개의 정보가 한 번에 로드 되기 때문에 굉장히 큰 메모리를 사용합니다.
4. TTL 이 설정되지 않은 키의 갯수를 대략적으로 파악하면 되는 것이었기 때문에 굳이 모든 키를 확인할 필요가 없습니다.

반면, `SCAN` 명령어를 사용하면 Cursor 기반으로 Bucket 단위로 조회하기 때문에 프로덕션 환경에서 장애 없이 전체 검색을 할 수 있습니다.[[4]](https://redis.io/commands/scan/)

```sh
#!/bin/sh

cursor=-1
host=${redis-host}
pattern=${redis_key_pattern}

while [ $cursor -ne 0 ]; do
  if [ $cursor -eq -1 ]
  then
    cursor=0
  fi

  reply=`redis-cli -h $host SCAN $cursor MATCH $pattern COUNT 10000`
  cursor=`expr "$reply" : '\([0-9]*[0-9]\)'`
  keys=`echo $reply | cut -d' ' -f2-`

  for key in ${keys// / } ; do
    ttl=`redis-cli -h $host TTL $key`

    # TTL 이 설정되지 않은 경우, TTL 명령어에 대한 응답값은 -1로 반환됩니다.
    if [ $ttl -eq -1 ]
    then
      echo "$key"
    fi
  done
done

```
스크립트를 통해 TTL 이 걸리지 않은 세션 정보가 굉장히 많은 것을 확인했습니다. TTL 이 설정되지 않은 세션 정보의 내용을 확인해보았는데, 공통적으로 전체 세션 정보 중 **일부** 만 저장되어 있는 것을 확인할 수 있었습니다.

# 문제 확인
세션을 저장하는 전체적인 코드를 살펴보았지만 아무리 살펴보아도 세션 정보의 일부만이 저장되고 TTL 설정이 적용되지 않는 Flow가 존재하지 않았습니다. 로직상으로 세션을 생성할 때 TTL 을 설정하고 저장하고, 세션을 load 할 때도 다시 TTL 을 설정하기 때문입니다.

코드만으로는 문제의 원인을 발견을 할 수 없어 한참을 헤매다, 서버 요청 기록이 포함된 로그 탐색을 통해 문제의 원인을 발견할 수 있었습니다. 이슈가 있었던 세션 데이터에 대한 로그를 살펴본 결과, 세션을 날려버리는 logout API가 세션 인증이 필요한 API 요청과 동시에 들어올 때 이와 같은 현상이 발생하는 것 같은 기록을 확인할 수 있었습니다. 

이를 재현하기 위해 임의로 logout API 와 인증이 필요한 API 요청을 동시에 실행해보았습니다. 실제로 레디스에 TTL 이 설정되지 않은 세션 정보가 저장됨을 확인했고, 실제로 일부 필드에 대해서만 저장되어 있는 것도 재현할 수 있었습니다.

```kotlin
​
fun main(args: Array<String>): Unit = runBlocking {
    val cookie = requestLogin()
    val a = async(Dispatchers.IO) { requestRemember(cookie) }
    delay(2)
    val b = async(Dispatchers.IO) { requestLogout(cookie) }
    awaitAll(a, b)
}
```

이 Flow 에서 TTL 이 설정되지 않고 일부 정보만 저장되는 이유는 아래와 같습니다.
1. logout API에서는 현재 세션 정보를 invalidate 하는 메소드를 호출해서 세션의 정보를 삭제합니다.
2. 동시에 들어온 다른 요청에서는 해당 세션 정보에 변경이 발생하고, 변경 사항만을 threadLocal 에 저장해두었다가 요청 처리가 종료되는 시점에 레디스에 저장을 합니다.

이 저장 시점에는 1의 로그아웃에 의해 해당 key에 대한 데이터가 이미 존재하지 않습니다. ThreadLocal에 있는 일부 변경사항을 저장하는 과정에서 TTL 이 설정되지 않은 채 일부 정보만이 저장되는 것이었습니다.

# 레디스 동시성 문제
위의 동시성 문제를 해결하기 위해서는 세션을 변경하는 요청에서 레디스에 세션 정보가 존재하는 경우에만 변경 내용을 저장하게 하면 됩니다. 여기서도 단순히 순차적으로 세션 정보 존재 여부를 조회하고, 이 결과를 기반으로 저장할지 말지를 결정하는 것만으로는 문제를 해결할 수 없습니다.

특정 요청에서 연속적으로 여러 Redis 명령을 수행한다고 하더라도, 다른 요청에서 그 중간에 명령을 수행해서 예상치 못한 결과를 만드는 것을 막을 수 없기 때문입니다. 이와 같은 문제는 `Redis Transaction` 혹은 `lua-script` 를 통해 해결할 수 있습니다.

Redis Transaction 에서는 `MULTI`, `EXEC`, `WATCH` 과 같은 특수한 명령어들을 사용해서 원하는 명령어들이 방해받지 않고 연속적으로 수행되게 할 수 있습니다. `MULTI` 명령어를 이용하면 앞으로 수행하고 싶은 여러 명령어들을 큐(QUEUE) 에 쌓아둡니다. 이 상태에서 `EXEC` 명령어를 실행하면 그 동안 큐에 쌓인 명령어를 한번에 순차적으로 실행하는 구조입니다. 그 중간에 **절대** 다른 명령어가 끼어들어가지 못한다는 장점을 가집니다. `WATCH` 명령어를 사용하면 특정 키에 대해 낙관적 락을 걸 수 있습니다. 낙관적 락을 통해 다른 클라이언트 혹은 트랜잭션에서 1회까지만 값을 변경할 수 있음을 보장합니다. 만약 `WATCH` 명령어에 의해 낙관적 락이 걸린 키의 값이 2회 이상 변경을 시도하는 경우 해당 명령어들은 모두 실행이 되지 않고 nil 을 반환합니다.[[5]](https://redis.io/docs/manual/transactions/)

lua-script 를 사용하는 방법 역시 Redis Transaction 과 마찬가지로 한 번에 여러 명령어들이 수행되게 하는 형태입니다. 다만 Redis Transaction 이 가지지 못하는 아래와 같은 장점들을 추가로 가지고 있습니다.[[6]](https://redis.io/docs/manual/programmability/eval-intro/)
1. 로컬 변수, 조건문, 반복문 등을 활용해 프로그래밍을 하듯 로직을 넣어 스크립트를 구현할 수 있다는 장점을 가집니다.
2. script 가 실행되는 동안 서버의 모든 동작이 block 되기 때문에 마치 락(Lock) 을 획득하고 동작을 하는 형태를 보장합니다.

이러한 장점 때문에 레디스 공식 문서에서는 Redis Transaction 대신 lua-script 를 사용하는 것을 권장하고, 아자르에서는 lua-script 기반으로 문제를 해결했습니다.[[5]](https://redis.io/docs/manual/transactions/)

세션 정보를 저장할 때, 아래처럼 lua-script 를 사용해 레디스에 저장을 하는 방식으로 변경했습니다. 새로 생성된 세션인 경우 이전 세션이 존재하지 않기 때문에 바로 저장을 하고, 존재하는 세션의 변경 사항에 대해 저장을 하는 경우 해당 세션 키가 존재하면 저장합니다.
```java
public class SessionScriptFactory {
    private final DefaultRedisScript<Void> script;
    private final Object[] params;
    private final List<String> keys;

    private static final String REDIS_SCRIPT_SAVE_DELTA_PREFIX = "local v = redis.call('exists', KEYS[1]);\n if v == 1 then ";
    private static final String REDIS_SCRIPT_SAVE_DELTA_POSTFIX = "return \n else return end";


    public SessionScriptFactory(String redisKey, HashMap<String, Object> delta, boolean isNew) {
        // stream 내부에서 유사 final 처럼 동작하게 하기 위함입니다.
        final int[] index = {1};

        List<String> keys = new ArrayList<>();
        keys.add(redisKey);

        List<Object> params = new ArrayList<>();
        StringBuilder lua = new StringBuilder("redis.call('hmset', KEYS[1]");

        delta.forEach((key, value) -> {
            // 레디스의 hmset 명령어는 one-based index
            lua.append(", ARGV[").append(index[0]).append("], ARGV[").append(index[0] + 1).append("]");
            index[0] += 2;
            keys.add(key);
            params.add(value);
        });

        lua.append(");\n");

        DefaultRedisScript<Void> script = new DefaultRedisScript<>();

        // 새로 생성된 세션의 경우, 바로 저장.
        // 기존에 존재하던 세션의 경우, exists 로 찾았을 때 존재한다면 저장해서 동시성 이슈로 ttl 이 설정되지 않은채 저장되는 key 에 대한 방어
        if (isNew) {
            script.setScriptText(lua.toString());
        } else {
            script.setScriptText(REDIS_SCRIPT_SAVE_DELTA_PREFIX + lua + REDIS_SCRIPT_SAVE_DELTA_POSTFIX);
        }

        script.setResultType(Void.class);

        this.script = script;
        this.params = params.toArray();
        this.keys = keys;
    }
}
```

# 직렬화 문제가 발생
lua-script 기반으로 세션 정보를 저장하는 방식을 바꾼 이후, 직렬화 문제가 발생했습니다. `"lastAccessedTime"` 으로 저장되던 필드가 "`"\lastAccessedTime\"` 형태로 저장되었습니다.

저장하는 시점에 Serializer 가 달라져서 생겼을 것이라 생각했고, 기존에 세션을 저장할 때 사용하던 메소드인 redisTemplate.boundHashOps.putAll 을 확인해보았습니다. Map 의 Key 에 대해서는 rawHashKey 를 사용하고, Value 에 대해서는 rawHashValue 를 사용하는 것을 확인할 수 있습니다.

```java
for (Map.Entry<? extends HK, ? extends HV> entry : m.entrySet()) {
   hashes.put(rawHashKey(entry.getKey()), rawHashValue(entry.getValue()));
}
```

rawHashKey 의 Serializer 는 RedisConfig 를 통해 정의가 되어있고, StringRedisSerializer 를 사용하는 것을 확인했습니다.
```java
private RedisTemplate<Object, Object> createRedisTemplate(
    LettuceConnectionFactory lettuceConnectionFactory,
    RedisSerializer<?> redisSerializer
) {
    RedisTemplate<Object, Object> redisTemplate = new RedisTemplate<>();
    redisTemplate.setKeySerializer(new StringRedisSerializer());
    redisTemplate.setHashKeySerializer(new StringRedisSerializer());
    redisTemplate.setDefaultSerializer(redisSerializer);
    redisTemplate.setConnectionFactory(lettuceConnectionFactory);
    redisTemplate.setBeanClassLoader(this.classLoader);
    redisTemplate.afterPropertiesSet();
    return redisTemplate;
}
```

기존에는 StringRedisSerializer 를 사용하고 있었는데, lua-script 를 사용해 세션 정보를 저장하는 과정에서 잘못된 스크립트를 생성해 DefaultSerializer 를 사용하게 되었고 이 결과 직렬화 문제가 발생한 것이었습니다. 스크립트를 생성하는 코드에서 Map 의 키에 해당하는 부분을 'ARGV' 가 아닌 'KEY' 로 변경하면, HashKeySerializer 를 사용하게 되어 직렬화 문제를 해결할 수 있습니다. 코드를 아래처럼 수정하고 테스트를 해봤더니 정상적으로 직렬화가 되는 것을 확인할 수 있었습니다.
```java
// Key 는 StringSerializer, Value 는 defaultSerializer 를 타야하기 때문에, 아래처럼 script 를 작성합니다.
delta.forEach((key, value) -> {
    lua.append(", KEYS[").append(index[0] + 1).append("], ARGV[").append(index[0]).append("]");
    index[0] += 1;
    keys.add(key);
    params.add(value);
});
```

# 세션 레디스 클러스터 청소
메모리 누수가 발생하는 근본적인 문제를 해결했으나, 레디스 클러스터에 TTL 이 설정되지 않은채 저장되어 있는 값들을 삭제해야 합니다. 위에서 살펴보았던 TTL 이 설정되지 않은 세션 정보를 확인하기 위한 스크립트에 TTL 을 설정하는 명령을 추가해 돌려보았습니다.

```sh
#!/bin/bash

while [ $cursor -ne 0 ]; do
  
  ...
  count=0

  for key in ${keys// / } ; do
    ttl=`redis-cli -h $host TTL $key`
    act=""

    if [ $ttl -eq -1 ]
    then
      result=`redis-cli -h $host EXPIRE $key $expire`
      act=" -> $expire"
      ((count++))
    fi

    echo "$key: $ttl$act"
  done
  if [ $count -gt 0 ]
  then
    echo 'sleep'
    sleep 1s
  fi
done
```

위 스크립트를 돌린 결과, TTL 이 설정되어 있지 않은 세션 정보가 모두 삭제되었고 트래픽이 최고점인 시간대에 메모리 사용률이 85% 이상이던 것이 20% 수준으로 정리된 것을 확인할 수 있었습니다. 

![after_script]({{"/assets/2023-01-09-redis-session/after_script.png" | absolute_url}}) <br>

# 마무리
오늘은 Spring Session + Custom Session Repository 에서 발생한 메모리 누수의 원인 및 해결 방안에 대해 살펴보았습니다.

레디스에서 발생할 수 있는 **동시성 문제** 를 해결할 수 있는 방법에 대해 살펴보았고, lua-script 를 사용할 때 Serializer 에 대해 주의를 해야한다는 점을 알 수 있었습니다.

또한, 레디스에서 메모리 누수가 의심이 될 때 프로덕션 환경에서 TTL 이 설정되지 않은 키를 검색하는지, 그리고 이를 청산하는 지에 대해서도 공유할 수 있었습니다.

# Reference
[1] [Spring Session으로의 마이그레이션 작업기](https://hyperconnect.github.io/2018/10/21/spring-session-migration.html) <br>
[2] [Spring Session 동작 원리](https://spring.io/projects/spring-session)<br>
[3] [Custom Session Repository](https://docs.spring.io/spring-session/docs/2.2.x/reference/html/custom-sessionrepository.html)<br>
[4] [Redis SCAN Command](https://redis.io/commands/scan/)<br>
[5] [Redis Transaction](https://redis.io/docs/manual/transactions/)<br>
[6] [Redis Lua-Script](https://redis.io/docs/manual/programmability/eval-intro/)<br>
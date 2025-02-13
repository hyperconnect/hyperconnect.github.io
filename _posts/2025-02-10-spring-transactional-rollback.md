---
layout: post
date: 2025-02-10
title: Spring Transactional Rollback Deep Dive
author: ledger
tags: spring transcational rollback
excerpt: Spring Transactional Rollback 이 되는 케이스를 심층적으로 살펴보고 예시로 확인해봅니다.
last_modified_at: 2025-02-10
---

안녕하세요. Azar API Dev Team의 Ledger입니다. 이번 글에서는 Spring Transactional 동작에서 Checked Exception과 Unchecked Exception의 롤백(rollback) 처리에 관한 내용을 다뤄보겠습니다. 여러 사례를 통해 예외 처리 코드를 작성해 보고, 자주 혼동되는 부분들을 정리해 보았습니다.

# 그래서 언제 롤백 되는 건데!!

트랜잭션 범위 내에서 예외가 발생하면 롤백 되는건 익히 알고 있지만, 예외 처리를 해도 롤백 될 때가 있습니다. 정확히 언제 롤백이 될까요? 보통 Unchecked Exception과 Checked Exception 관련된 내용을 위주로 떠올리지만, 앞으로 나올 문제들을 모두 해결하려면 트랜잭션 프록시의 세부 동작이나 트랜잭션과 스레드의 상관관계와 같은 더 많은 내용을 이해하고 있어야 합니다.

먼저 Unchecked Exception과 롤백 마킹에 대해서 간단히 살펴보겠습니다.

# Unchecked Exception의 롤백 마킹

Spring에서는 트랜잭션 진행 중 예외가 발생할 경우 [rollbackOn](https://github.com/spring-projects/spring-framework/blob/6.1.x/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L679)에서 Unchecked 인지 체크합니다. Unchecked일 경우 [processRollback](https://github.com/spring-projects/spring-framework/blob/6.2.x/spring-tx/src/main/java/org/springframework/transaction/support/AbstractPlatformTransactionManager.java#L902) 부분에서 각 기본 설정값의 영향으로 참여 중인 트랜잭션을 `rollback-only`로 마킹합니다. 의도를 이해해 보자면 일부 트랜잭션이 실패할 경우, 전체 트랜잭션을 롤백 하는 것입니다. Checked Exception은 예상된 예외로 이를 처리하도록 의도된 것이고, Unchecked Exception은 예상치 못한 예외로 발생 시 롤백을 시도합니다.

롤백 마킹에 대한 설정은 Spring `@Transactional`의 `rollbackFor` 설정을 보면 확인할 수 있고, default 설정은 Unchecked Exception인 RuntimeException과 Error입니다.

그렇다면 Unchecked Exception은 try catch로 잡아도 무조건 롤백이 될까요? 그렇지 않습니다. 이걸 이해하려면 롤백이 마킹된다는 개념을 이해하고 있어야 합니다. 이어서 아래 문제들을 통해 확인해 보겠습니다. 아래 문제들은 @Transactional 메소드를 제외하고 별도로 설정된 Transaction Advice는 없다고 가정합니다.

# 같은 서비스 내에서 @Transactional 호출 시 동작

```kotlin
@Service
class PizzaService {
    fun eatPizza() {
        pizza()
    }

    @Transactional
    fun pizza() {
        // ...
    }
}
```

**문제 1.** eatPizza 메소드 내의 pizza가 호출되면 새로운 트랜잭션이 열릴까요?

정답은 **X**입니다. 이유는 스프링 `@Transactional` 어노테이션은 Spring AOP 기반으로 동작하는데 동일한 클래스 내에서 `@Transactional` 이 적용된 내부 메서드를 호출하는 경우, 호출되는 메서드는 **프록시 객체를 거치지 않고 직접 호출되기 때문에 프록시(TransactionInterceptor)가 동작하지 않습니다.**

위 트랜잭션을 실행시키고 싶다면 pizza를 별도의 서비스로 분리하거나 트랜잭션 템플릿을 사용해 직접 트랜잭션을 열고 닫게 구현하면 됩니다. 아래 그림 1은 프록시 호출 구조에 대해 간단히 정리합니다.

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2025-02-10-spring-transactional-rollback/proxy.png" | absolute_url}}' alt='그림 1. 프록시 호출 구조'>
  <figcaption>그림 1. 프록시 호출 구조</figcaption>
</figure>

그림 1에서 프록시 동작을 코드로 간단히 표현하면 아래와 같습니다.

```kotlin
class TransactionProxy {
    fun invokeWithinTransaction() {
        try {
            // 트랜잭션 전처리
            tm.begin()

            // 타겟 비즈니스 로직 (ex. pizza)
            invocation.proceedWithInvocation()

            // 트랜잭션 후처리
            tm.commit()
        } catch (ex: Exception) {
            // 트랜잭션 오류 발생 시 롤백
            tm.rollback()
        }
    }
}
```

위의 방법 대신 AspectJ를 활용할 수도 있지만, 본문에서는 Spring AOP 사용 사례에 대해서만 다룹니다. 이어서 아래 문제를 확인해 보겠습니다.

# TransactionInterceptor와 롤백의 상관관계

**문제 2.** 아래 pizza를 호출할 시 RuntimeException이 예외로 발생하면 eatPizza의 트랜잭션이 롤백 될까요?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 롤백이 될까?
        try {
            pizza()
        } catch (e: Exception) {
            // error ignore
        }
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    fun pizza() {
        throw RuntimeException("RuntimeException") // Unchecked Exception 발생
    }
}
```

정답은 **X**입니다. 아래 풀이를 보겠습니다.

- `@Transactional(propagation = Propagation.REQUIRES_NEW)`: 같은 서비스 내에서 `@Transactional` 어노테이션을 호출했기 때문에 프록시 객체를 거치지 않아 새로운 트랜잭션은 열리지 않습니다.
- `TransactionInterceptor`: 정상적으로 프록시 동작을 거치게 수행했다면 동작은 다음과 같습니다. 트랜잭션이 열릴 때 TransactionInterceptor가 동작하고 exception이 발생했다면 [completeTransactionAfterThrowing](https://github.com/spring-projects/spring-framework/blob/6.2.x/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L384)에서 진행 중인 트랜잭션의 상태를 롤백으로 [마킹](https://github.com/spring-projects/spring-framework/blob/6.2.x/spring-tx/src/main/java/org/springframework/transaction/interceptor/TransactionAspectSupport.java#L716)해둡니다.

2번 문제에서는 pizza에서 예외가 발생했지만 TransactionInterceptor가 동작하지 않았고 eatPizza에서는 예외를 try catch로 잡았습니다. 트랜잭션을 커밋 할 시점에 eatPizza의 TransactionInterceptor 동작에서 롤백 마크가 되어있나 찾았지만 트랜잭션 내부에서 예외가 발생하지 않고 예외를 처리했기 때문에 마킹된 롤백은 없었습니다. 즉 예외가 발생한 pizza에서는 TransactionInterceptor 동작이 수행되지 않았고 TransactionInterceptor 동작이 수행되는 eatPizza에서는 예외를 모두 잡고 트랜잭션이 정상적으로 수행됐습니다.

**문제 3.** 아래 PickleService의 eatPickle을 호출할 시 RuntimeException이 예외로 발생하면 eatPizza의 트랜잭션이 롤백 될까요?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 롤백이 될까?
        pizza()
        try {
            pickleService.eatPickle()
        } catch (e: Exception) {
            // error ignore
        }
    }

    private fun pizza() {
        // ...
    }
}

@Service
class PickleService {
    @Transactional
    fun eatPickle() {
        throw RuntimeException("RuntimeException") // Unchecked Exception 발생
    }
}
```

정답은 **O**입니다. 아래 풀이를 보겠습니다.

- 다른 서비스를 통해 `@Transactional` 어노테이션 메서드를 호출했지만 기본 전파 옵션을 사용했기 때문에 새로운 트랜잭션에서 열지 않고 부모 트랜잭션에서 동작이 수행됩니다.
- 프록시 객체를 정상적으로 거쳤기 때문에 TransactionInterceptor 동작이 수행됐고 **eatPickle에서는 Unchecked Exception인 RuntimeException이 발생하고 발생된 예외에 따라 트랜잭션에 롤백 마킹을 하게 됩니다.**
- eatPizza에서 예외를 처리했지만 이미 eatPickle에서 트랜잭션에 롤백 마킹이 되어 있기 때문에 커밋 시점에 해당 트랜잭션은 롤백 됩니다.

**문제 4.** 아래 PickleService의 eatPickle을 호출할 시 RuntimeException이 예외로 발생하면 eatPizza의 트랜잭션이 롤백 될까요?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 롤백이 될까?
        try {
            pickleService.eatPickle()
            pizza()
        } catch (e: Exception) {
            // error ignore
        }
        pizza()
    }

    private fun pizza() {
        // ...
    }
}

@Service
class PickleService {
    // 문제 3과 달리 @Transactional 생략
    fun eatPickle() {
        throw RuntimeException("RuntimeException") // Unchecked Exception 발생
    }
}
```

정답은 **X**입니다.

문제 2번과 유사하게 TransactionInterceptor 동작이 eatPickle에서 수행되지 않아 롤백 마킹을 안 했고, eatPizza에서는 예외를 처리했기 때문에 롤백 마크가 없고 발생된 예외도 없어 정상적으로 트랜잭션이 수행되었습니다.

문제 2, 3, 4를 통해 TransactionInterceptor와 롤백의 상관관계에 대해 알아보았습니다. 정리해 보면 아래와 같습니다.

- 예외를 처리하지 않으면 커밋을 못하고 어떤 예외든 명시적으로 롤백 해버린다.
- 하나의 트랜잭션으로 동작할 때, 예외를 PizzaService에서 처리하더라도 PickleService에서 TransactionInterceptor 동작이 수행되고 Unchecked Exception이 발생하는 경우, 롤백이 마킹되어 트랜잭션이 커밋 시점에 롤백된다.
- 하나의 트랜잭션으로 동작할 때, 예외를 PizzaService에서 처리하고 PickleService에서 Checked Exception이 발생한 경우, TransactionInterceptor가 동작했더라도 롤백이 마킹되지 않고 최종적으로는 예외가 외부로 전달되지 않았기 때문에 트랜잭션은 롤백되지 않는다.
- 모든 메서드 내에서 예외를 처리했다면 트랜잭션은 롤백 되지 않는다.

# 심화: Kotlin의 UndeclaredThrowableException

**문제 5.** 아래 PickleService의 eatPickle을 호출할 시 IOException이 예외로 발생하면 eatPizza의 트랜잭션이 롤백 될까요?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 롤백이 될까?
        try {
            pickleService.eatPickle()
            pizza()
        } catch (e: Exception) {
            // error ignore
        }
    }

    private fun pizza() {
        // ...
    }
}

@Service
class PickleService {
    @Transactional
    fun eatPickle() {
        throw IOException("IOException") // Checked Exception 발생
    }
}
```

정답은 **O**입니다.

다 알았다고 생각했는데 또 이상한 부분이 나왔습니다. IOException은 Checked Exception이기 때문에 롤백이 안될 텐데 왜 롤백이 될까요? 정답은 Kotlin에 있습니다.

Java에서는 Checked Exception의 경우 반드시 함수 내에서 예외를 처리해야만 합니다. 만약 그렇지 않을 경우 throws를 통해 예외가 발생함을 명시해야만 합니다. 다만 Kotlin에서는 Checked Exception을 일종의 불필요한 안티 패턴으로 규정하여 이러한 제약을 제거하였고, 위에 코드와 같이 Checked Exception이 함수에서 발생한 후 별도의 throws 나 예외 처리를 하지 않아도 컴파일 에러가 나지 않습니다.

다만 문제가 있는데, 만약 Java와 같이 사용하다 Checked Exception이 발생할 경우 Checked Exception이 아닌 UndeclaredThrowableException으로 바뀌어 Exception이 발생하게 됩니다. **UndeclaredThrowableException은 RuntimeException을 상속받기 때문에 Unchecked Exception이고 결국에는 롤백이 마킹되어 커밋 시점에 롤백이 됩니다.**

그럼 어떻게 롤백이 안되게 올바르게 작성해 볼 수 있을까요?

**문제 6.** 아래 PickleService의 eatPickle을 호출할 시 IOException이 예외로 발생하면 eatPizza의 트랜잭션이 롤백 될까요?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 롤백이 될까?
        try {
            pickleService.eatPickle()
            pizza()
        } catch (e: Exception) {
            // error ignore
        }
    }

    private fun pizza() {
        // ...
    }
}

@Service
class PickleService {
    @Throws(IOException::class) // 문제 5와 달리 @Throws 추가
    @Transactional
    fun eatPickle() {
        throw IOException("IOException") // Checked Exception 발생
    }
}
```

정답은 **X**입니다.

Kotlin에서는 `@Throws` 어노테이션을 통해 해당 Kotlin 함수가 예외를 던질 수 있다는 Java의 throws와 동일한 것을 작성할 수 있습니다. 이렇게 하면 UndeclaredThrowableException이 아닌 의도한 예외인 IOException이 던져져 롤백이 마킹되지 않고 트랜잭션이 정상 수행됩니다.

# 심화: @Transactional 전파 REQUIRES_NEW

먼저 간단하게 Spring Transaction의 상태 관리에 대해 살펴보겠습니다.

Spring Transaction은 ThreadLocal로 트랜잭션의 상태를 관리합니다. 그것이 트랜잭션이 스레드 별로 동시성 이슈 없이 동기화될 수 있는 이유입니다. 만약 `@Async` 어노테이션을 통해 트랜잭션 중 다른 스레드로 함수를 실행시키면 해당 비동기 동작은 기존 트랜잭션에 포함되지 않은 채 별도로 동작하게 됩니다.

그렇다면 `@Transactional(propagation = Propagation.REQUIRES_NEW)`가 적용된 아래의 경우, 각각의 트랜잭션은 어떻게 생성되며, 어떤 스레드에서 실행될까요?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 어떤 트랜잭션과 스레드에서 동작할까?
        pizza()
        pickleService.eatPickle()
    }
}

@Service
class PickleService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    fun eatPickle() { // 어떤 트랜잭션과 스레드에서 동작할까?
        // ...
    }
}
```

동작은 다음과 같습니다.

- 기존 부모 트랜잭션이 없었다고 가정한다면 eatPizza 에서부터 새로운 트랜잭션이 열리며 동작
- eatPickle은 새로 연 eatPickle 트랜잭션에서 동작하지만 기존 스레드인 eatPizza 스레드에서 수행

**그럼 이어서 문제 7입니다.** 아래 PickleService의 eatPickle을 호출할 시 RuntimeException이 예외로 발생하면 eatPizza의 트랜잭션이 롤백 될까요?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 이 트랜잭션은 롤백이 될까?
        try {
            pickleService.eatPickle()
        } catch (e: Exception) {
            // error ignore
        }
    }
}

@Service
class PickleService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    fun eatPickle() { // 어떤 트랜잭션과 스레드에서 동작할까?
        throw RuntimeException("RuntimeException") // Unchecked Exception 발생
    }
}
```

정답은 **X**입니다.

eatPickle의 TransactionInterceptor에서 롤백 마킹을 하게 되지만, 롤백 마킹은 새로운 트랜잭션인 eatPickle에서 되기 때문에 기존 트랜잭션은 예외를 처리했다면 롤백 되지 않습니다. 핵심은 어떤 스레드에서 동작하고 있으며 어떤 트랜잭션에서 수행되고 커밋 되고 있는가입니다. 좀 더 잘 이해하기 위해 아래 문제를 보겠습니다.

**문제 8.** 아래 PickleService의 eatPickle을 호출할 시 eatPizza에서 RuntimeException이 예외로 발생하면 eatPickle의 트랜잭션이 롤백 될까?

```kotlin
@Service
class PizzaService {
    @Transactional
    fun eatPizza() { // 어떤 트랜잭션과 스레드에서 동작할까?
        pizza()
        pickleService.eatPickle() 
        throw RuntimeException("RuntimeException") // Unchecked Exception 발생
    }
}

@Service
class PickleService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    fun eatPickle() { // 이 트랜잭션은 롤백이 될까?
        // ... 
    }
}
```

정답은 **X**입니다.

eatPizza는 롤백 되겠지만 eatPickle은 이미 새로운 트랜잭션에서 열고 닫혔기 때문에 문제가 되지 않습니다.

지금까지의 동작을 모두 이해하고 나면, 실제 사례에서 복잡한 요구사항이 있더라도 일관성을 유지하며 효과적으로 비즈니스 로직을 작성할 수 있습니다. 아래 사례는 하나의 이벤트 처리를 일관성 있게 유지하면서도 긴 트랜잭션을 효율적으로 줄인 예시입니다.

# 실제 사례로 알아보는 효율적인 트랜잭션 사용과 예외 처리

예시로 지난번 작성한 글인 [카프카를 활용한 무손실 이벤트 처리](https://hyperconnect.github.io/2024/11/11/azar-data-life-cycle-policy.html)를 통해 설명해 보겠습니다. 당시 발행된 이벤트에 대해 무손실 처리를 하기 위해 예외 발생 시 전체를 재시도 하는 문제가 있었습니다. 발행된 이벤트 처리가 특정 사용자에 대해 매우 긴 트랜잭션으로 작동하면서 지속적인 실패와 재시도가 발생하는 상황이었습니다. 따라서 처리를 분리해야 했습니다. 해결 방법은 여러 가지가 있을 수 있지만, 여기서는 효율적으로 트랜잭션을 관리하는 방법을 선택했습니다. 한 리스너에서 일관된 이벤트 처리를 유지하면서, 내부적으로 트랜잭션을 분리하여 처리하는 방식입니다.

```kotlin
@KafkaListener
fun handle(
    records: List<ConsumerRecord<AccountEventKey, AccountEventValue>>,
    acknowledgment: Acknowledgment
) {
    try {
        dataLifeCyclePolicyService.deletePersonalInfo(userId)
    } catch (ex: Exception) {
        // 어떠한 예외라도 발생 시 nack 하여 실패했던 작업을 재시도합니다.
        acknowledgment.nack(index, NACK_SLEEP_MS)
    }

    /** 모두 성공한 경우에만 최종 커밋하여 다음 이벤트를 받습니다. **/
    acknowledgment.acknowledge()
}
```

위의 DataLifeCyclePolicyService에서 deletePersonalInfo를 호출할 시 유저들의 개인정보를 모두 삭제하는데 긴 트랜잭션으로 중간에 하나라도 실패하면 전체 롤백 하여 재시도 하는 문제가 있습니다. 이걸 어떻게 무손실을 유지하며 개선해 볼 수 있을까요?

```kotlin
@Service
class DataLifeCyclePolicyService(
    private val userFollowService: UserFollowService
) {
    @Transactional
    fun deletePersonalInfo(userId: Long) { // Long Transaction
        // ...

        // 만약 userFollowService.deleteByUserId(userId) 이후 예외가 발생한다면 어떻게 될까?
        userFollowService.deleteByUserId(userId)
        
        // ...
    }
}

@Service
class UserFollowService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    fun deleteByUserId(userId: Long) { // 신규 트랜잭션으로 동작
        // delete
    }
}
```

정답은 문제 8에 있습니다. 위 코드의 deleteByUserId 메서드 수행 시 유저에 대한 삭제 데이터가 커서 deletePersonalInfo 트랜잭션 처리에 긴 시간이 걸린다고 가정합니다. 긴 시간을 소모해서 deletePersonalInfo 트랜잭션은 계속 길어져 문제가 발생하게 됩니다. 타임아웃에 걸리면 전체가 롤백 되고 카프카에서 전체를 다시 재시도하게 됩니다. 그렇다면 계속해서 재시도하고 데이터는 삭제되지 못하는 문제가 발생하게 됩니다.

위의 예시처럼 userFollowService.deleteByUserId를 별도의 트랜잭션으로 만든다면 userFollowService.deleteByUserId의 데이터 삭제가 실패했을 경우 동일 스레드에서 동작 중이기 때문에 부모 트랜잭션까지 예외가 전파되어 모두 재시도하여 무손실을 보장할 수 있고 userFollowService.deleteByUserId에는 성공했으나 이후에 실패한다면 userFollowService.deleteByUserId의 내용은 롤백이 되지 않아 다시 재시도 하더라도 좀 더 짧은 트랜잭션으로 재시도할 수 있습니다.

```kotlin
@Service
class UserFollowService(
    private val userFollowRepository: UserFollowRepository,
    private val transactionService: TransactionService // custom transaction service
) {
    fun deleteByUserId(userId: Long) {
        while (true) {
            transactionService.executeInNewTransaction { // 신규 트랜잭션에서 동작
                val userFollows = userFollowRepository.findByUserId(userId, BATCH_SIZE)
                if (userFollows.isEmpty()) {
                    return
                }
                userFollows.forEach {
                    userFollowRepository.delete(it)
                }
            }
        }
    }
}
```

만약 userFollowService.deleteByUserId에서 처리해야 할 데이터가 너무 커서, 위의 방법만으로는 긴 트랜잭션 문제를 해결할 수 없다면, 유저별 팔로워 삭제를 커서 기반으로 재구성할 수 있습니다. 커서별로 삭제 시 새로운 트랜잭션을 생성하여 각각의 삭제 작업이 짧은 트랜잭션으로 이루어지도록 합니다. 이를 통해 전체 작업이 무손실로 진행되도록 구성할 수 있습니다. 이를 그림으로 표현하면 아래와 같습니다.

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2025-02-10-spring-transactional-rollback/example.png" | absolute_url}}' alt='그림 2. 효율적인 트랜잭션 사용과 예외 처리 사례'>
  <figcaption>그림 2. 효율적인 트랜잭션 사용과 예외 처리 사례</figcaption>
</figure>

# 마치며

이번 글에서는 하이퍼커넥트에서 사용하는 사례와 함께 Spring `@Transactional` 동작과 롤백에 대해서 살펴보았습니다. 정확한 동작을 이해하려면 **TransactionInterceptor와 롤백 마킹 그리고 더 잘 활용하기 위해 스프링의 전파 옵션과 스레드의 상관관계를 이해해야 합니다.** 이런 여러 가지 고민을 하고 있는 Azar API 팀의 또 다른 이야기를 전해드리겠다는 인사와 함께 이 글을 마치겠습니다.

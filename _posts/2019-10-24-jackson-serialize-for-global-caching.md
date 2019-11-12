---
layout: post
date: 2019-10-28
title: Jackson 직렬화 옵션의 적절한 활용과 Jackson에 기여하기까지 (feat. 글로벌 캐싱)
author: fitz
tags: java serialize json jackson redis opensource spring-data-redis
excerpt: 글로벌캐싱을 하기 위해 자바의 오픈소스 JSON 직렬화 라이브러리인 Jackson의 직렬화 옵션을 활용한 경험과 Jackson에 기여한 경험을 이야기합니다.
---
안녕하세요, 하이퍼커넥트 Azar API팀의 Fitz 입니다.

이 글에서는 아자르 API에서 로컬 캐싱을 글로벌 캐싱으로 개선하며 데이터의 일관성을 보장하기 위해 Jackson의 직렬화 옵션을 활용한 경험과 Jackson에 개선되었으면 좋겠다고 생각한 점을 Jackson에 이슈업하고 코드로 기여한 경험을 공유합니다. 

아자르 API에서는 sticky session을 사용합니다. 그래서 "동일한 유저는 동일한 서버로만 접속한다"라는 것이 보장되어 로컬 캐싱으로 처리하던 로직이 있었습니다.
이 캐싱 로직을 범용적으로 사용할 수 있도록 하고, sticky session에서 독립적이면서 scalable한 구조로 개선하기 위해 글로벌 캐싱을 적용하기로 했습니다.

또한 특별한 사항으로는 이 캐싱이 적용되는 로직에는 무거운 트랜잭션이 많기 때문에 예외가 발생하면 예외까지도 캐싱해줘야하는 요구사항이 있었습니다.

캐시 데이터를 저장할 저장소는 [Redis](https://redis.io/)를 사용하기로 했고, 레디스에 객체의 데이터를 저장하기 위해선 객체를 직렬화/역직렬화 해주는 과정이 필요하기에 이를 구현하기로 했습니다. 


## 직렬화/역직렬화 데이터의 일관성

일반적인 로컬 캐싱에서는 객체 자체가 메모리에 보관되기 때문에 값의 일관성을 쉽게 보장할 수 있습니다. 
하지만 외부에 데이터를 저장하는 글로벌 캐싱의 경우는 직렬화 옵션에 따라 직렬화 과정에서 실제 객체의 값과 다른 값이 생성될 수도 있고, 역직렬화 과정에서 기존의 값과 다른 값이 객체에 주입될 가능성이 있습니다.

이러한 데이터 불일치성을 해결하기 위해 Jackson의 visibility 옵션을 활용하였습니다.

### Jackson의 Visibility

Jackson은 field, getter, setter, constructor 등 여러가지 방식으로 직렬화/역직렬화를 제공합니다.

그리고 visibility 옵션을 이용하여 어떤 것들을, 어떤 접근제한자를 이용하여 직렬화/역직렬화할지 선택할 수 있습니다.

예를 들면 모든 visibility를 막아두고, 모든 getter만 이용하여 직렬화한다면 아래처럼 객체가 직렬화됩니다. 
생성자와 propertyA가 보이지 않기 때문에 propertyB만 직렬화가 되었습니다.

```java
class Data {
    private String propertyA;
    private String propertyB;

    public Data(String propertyA, String propertyB) {
        this.propertyA = propertyA;
        this.propertyB = propertyB;
    }

    public String getPropertyB() {
        return propertyB;
    }

    public void setPropertyB(String propertyB) {
        this.propertyB = propertyB;
    }
}

Data data = new Data("A", "B");

String json = new ObjectMapper()
        .setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.NONE)
        .setVisibility(PropertyAccessor.GETTER, JsonAutoDetect.Visibility.ANY)
        .writeValueAsString(data);

System.out.println(json); // ==> {"propertyB":"B"}
```

하지만 이 변환된 JSON을 동일한 타입으로 역직렬화하려면 에러가 발생합니다. 역직렬화할 때 객체를 생성할 constructor 혹은 값을 주입해줄 setter가 visibility 옵션에 의해 가려져 보이지 않기 때문입니다.


### 캐싱에서의 Visibility 활용
결론부터 말씀드리자면 다른 visibility는 모두 비활성화하고 field만 보이도록 했습니다. 그 이유는 아래와 같습니다.
- 간혹 getter에 부가적인 로직이 들어있어 getter를 사용하면 다른 값으로 직렬화될 가능성이 있습니다.
- immutability을 위해 setter를 제공하지 않는 경우가 있습니다.
- constructor 혹은 setter의 파라미터 이름이 필드명과 일치하지 않을 가능성이 있습니다.

위의 내용은 사실 전부 하나의 요인에서 나오고 있습니다. constructor, getter, setter 등은 사람이 로직을 임의로 정의하고 변경할 수 있기 때문입니다.

이러한 점은 자바의 기본 클래스인 `Throwable`에서도 나타납니다. `Throwable`의 메세지 필드의 이름은 `detailMessage`입니다. 이 필드는 immutable로 getter만 제공되고, constructor에서만 초기화할 수 있습니다.

하지만 getter와 constructor에서 사용되는 이름은 `message`입니다. getter의 이름은 `getMessage()`이며 constructor에서는 `message`란 변수명으로 받고 있습니다. 
이로 인해 직렬화시에는 `detailMessage`와 `message`라는 필드가 동시에 생성되고, 역직렬화시에 중복으로 데이터 주입이 이루어집니다.

```java
// in Throwable.java
private String detailMessage;

public Throwable(String message) {
    fillInStackTrace();
    detailMessage = message;
}

public String getMessage() {
    return detailMessage;
}
```

캐싱은 보다 상위 개념이기에 클래스들은 캐싱의 존재를 몰라야합니다. 그렇기에 개발자가 클래스를 개발할 때마다 캐싱을 고려해서 클래스를 만들지는 않을 것입니다. 그래서 개발자가 값에 대한 오퍼레이션을 임의로 정의할 수 있는 constructor, getter, setter 등을 제외하고 데이터 고유의 값인 field의 값만을 가지고 직렬화하도록 설계했습니다.

또한 데이터가 불일치하는 상황이 발생하면 예외를 발생시키도록 역직렬화 옵션에 `FAIL_ON_UNKNOWN_PROPERTIES`을 활성화시켰습니다. (기본값이 활성화입니다.)

```java
new ObjectMapper()
    .setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.NONE)
    .setVisibility(PropertyAccessor.FIELD, JsonAutoDetect.Visibility.ANY);
```


## 명확한 타입의 필요성

캐싱 기능은 `Spring Data Redis`의 `RedisCacheManager`를 이용해 캐싱을 구현했습니다. 

그래서 `Spring Data Redis`에서 제공하는 Serializer에 제가 정의한 ObjectMapper를 넘기도록 구현하였고, 범용적인 타입을 캐싱해야했기 때문에 `GenericJackson2JsonRedisSerializer` 클래스를 사용했습니다. 

하지만 배열을 역직렬화하는 과정에서 문제가 발생하였고, Spring Data Redis의 코드를 열어보니 아래와 같은 코드가 나왔습니다.

```java
// in GenericJackson2JsonRedisSerializer.java
@Override
public Object deserialize(@Nullable byte[] source) throws SerializationException {
    return deserialize(source, Object.class);
}
```

범용적인 캐싱을 구현하고 있었기에 구체적인 타입을 지정하지 못하고 역직렬화할 클래스의 타입을 Object 타입으로 넘기고 있었습니다. 
하지만 이렇게 역직렬화의 타입을 Object로 일괄적으로 적용할 시에는 배열타입을 역직렬화하지 못하는 문제가 발생했습니다.

그 이유는 `DefaultTyping` 옵션 때문입니다. 일반적으로는 역직렬화할 타입에 대한 정보를 `ObjectMapper`의 `readValue` 메소드에 넘겨주는데 Jackson이 이 값을 이용해 역직렬화할 타입을 파악하여 역직렬화를 해주고 있습니다. 
하지만 Object 타입으로 역직렬화하게 되면 이러한 타입에 대한 정보가 없기 때문에 역직렬화가 불가능하게되는 문제가 발생합니다.

그래서 Jackson은 `DefaultTyping` 옵션을 통해 JSON 자체에 타입 정보를 명시합니다. 아래의 예를 보면 어떻게 타입이 명시되는지 볼 수 있습니다.

```java
package test;

class Data {
    private String propertyA;
    private String propertyB;
    private List<String> propertyC;
    private String[] propertyD;
}

ObjectMapper objectMapper = new ObjectMapper()
    .enableDefaultTypingAsProperty(ObjectMapper.DefaultTyping.NON_FINAL, "@class");
objectMapper.writeValueAsString(new Data("A", "B", new ArrayList<>(), new String[]{}));

// 변환 후..
{
  "@class" : "test.Data",
  "propertyA" : "A",
  "propertyB" : "B",
  "propertyC" : [ "java.util.ArrayList", [ ] ],
  "propertyD" : [ ]
}
``` 

여기서 확인해보면 `String[]` 타입은 타입에 대한 명시가 되지 않은 것을 확인할 수 있습니다. 하지만 이 JSON은 정상적으로 역직렬화가 가능합니다. `test.Data`라는 타입에서 `propertyD`는 `String[]` 속성이라는 것을 유추할 수 있기 때문입니다.

아래의 상황이라면 어떨까요?

```java
objectMapper.writeValueAsString(new String[]{}); // ==> 변환 후 : "[]" 
```

`[]` 문자열은 `ArrayList`인지, `String[]`인지, 혹은 다른 리스트 타입인지 유추하기가 어렵습니다. 그래서 예외를 던지며 직렬화에 실패하게 됩니다. 
 
그래서 배열의 경우는 배열이라는 명확한 타입을 `ObjectMapper`의 `readValue` 메소드의 인자로 넘겨주어야했고, 범용적인 타입을 사용하는 `GenericJackson2JsonRedisSerializer`를 사용하는 대신 `ObjectMapper`를 직접 사용하여 직렬화 로직을 정의하게 되었습니다. 

캐싱은 핵심 로직과 독립적이기 때문에 이는 Aspect로 분리하여 개발하고 있었습니다. 그래서 `ProceedingJoinPoint` 클래스를 이용하여 메소드의 반환 타입을 가져올 수 있었고, 이를 역직렬화할 명확한 타입으로 줄 수 있었습니다.

```java
public Object cacheAroundAdvice(ProceedingJoinPoint pjp, ...) throws Throwable {

    MethodSignature signature = (MethodSignature) pjp.getSignature();

    ...
    
    deserializedValue = objectMapper.readValue(serializedValue, signature.getReturnType());
    
    ...
}
```

## self-reference 문제

요구사항 중 **무거운 트랜잭션이 많기 때문에 예외가 발생하면 예외까지도 캐싱해줘야한다** 라는 요구사항이 있었습니다.

만들어두었던 `ObjectMapper`를 이용하여 예외도 함께 직렬화하려고 했지만 문제가 발생했습니다. 
왜냐하면 Throwable의 `cause` 필드는 따로 세팅되지 않으면 자기 자신(`this`)을 가리키는 self-reference 필드이기 때문입니다.

```java
// in Throwable.java
private Throwable cause = this;

public Throwable(Throwable cause) {
    fillInStackTrace();
    detailMessage = (cause==null ? null : cause.toString());
    this.cause = cause;
}

public synchronized Throwable getCause() {
    return (cause==this ? null : cause);
}
```

self-reference 필드를 직렬화하려고 하면 직렬화 과정중에 무한 루프에 빠질 수 있습니다. 물론 Jackson 내부적으로 무한 루프를 막을 수 있는 로직이 있긴 하지만 이 로직은 결국 예외를 발생시켜 직렬화가 실패합니다.

self-reference를 찾으면 직렬화를 실패시킬 수 있는 `FAIL_ON_SELF_REFERENCE` 옵션도 있지만 이 역시도 직렬화가 실패하는 문제를 가지고 있습니다.

Jackson에는 이 self-reference를 무시할 수 있는 옵션이 없기 때문에 ObjectMapper를 다시 정의해야 했습니다.

Throwable의 `getCause()` 메소드는 `cause` 필드가 `this`일 경우 `null`을 반환합니다. 이 점을 이용하여 getter & constructor를 visibility에 포함시키면 직렬화 후에 역직렬화시에 `null`값으로 주입이 가능합니다. 

그래서 모든 visibility를 적용한 ObjectMapper를 따로 하나 더 정의하여 예외의 경우는 이것으로 직렬화/역직렬화 시켜 문제를 해결할 수 있었습니다. 
`detailMessage` 필드에 의해 사용하지 않는 값도 함께 생성되므로 이로 인한 직렬화 실패를 막기 위해 `FAIL_ON_UNKNOWN_PROPERTIES` 옵션을 false로 설정했습니다.

```java
new ObjectMapper()
    .setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY)
    .configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
```


## Jackson에 기여하기

사실 여기서 겪었던 self-reference 문제는 간단하게 해결이 가능합니다. 

Jackson에서 self-reference를 null로 치환해주기만 하면 무한루프, 직렬화 실패가 일어나지 않을 것이고, 예외용 ObjectMapper를 따로 정의해주지 않아도 됩니다.

이러한 self-reference를 null로 치환해주는 옵션이 있으면 이러한 문제를 간단하게 해결할 수 있을 것이라는 생각에 짧은 영어 지식으로 Jackson의 깃허브에 [이슈](https://github.com/FasterXML/jackson-databind/issues/2501)를 올렸습니다. 

그리고 Jackson 개발자에게 코멘트로 괜찮은 아이디어라는 답변을 받았고, 아이디어를 제안한 김에 코드까지 기여하면 좋겠다고 생각하여 이를 코드로 작성하였습니다.

코드를 클론받고 `ObjectMapper` 클래스가 직렬화하는 과정을 살펴보았습니다. 그리고 `BeanPropertyWriter` 클래스에서 self-reference를 핸들링하는 것을 확인했습니다.

`SerializationFeature` 클래스의 `FAIL_ON_SELF_REFERENCE` 옵션은 self-reference를 발견하면 직렬화를 실패시키는 옵션인데 이 옵션은 기본적으로 활성화가 되어있습니다. 그래서 역할이 중복될 가능성이 있으므로 하위 호환성을 고려해야 했습니다. 

이 옵션이 활성화되어있으면 제가 추가한 옵션인 `WRITE_SELF_REFERENCES_AS_NULL`은 무시하도록 개발하였고, 기본값을 비활성화로 설정하여 이 옵션이 추가된 릴리즈 버전부터 선택적으로 사용할 수 있도록 설정했습니다.

추가적으로 테스트 케이스까지 작성하여 동작을 확인한 다음 [Pull Request](https://github.com/FasterXML/jackson-databind/pull/2516)를 보냈고, 고맙다는 댓글과 함께 머지되었습니다. (이슈와 PR에 거의 하루도 지나지 않아서 코멘트가 달리는 것을 보니 Jackson이 특히 이슈와 PR에 대한 피드백이 빠른 것 같습니다.) 

## 마무리

간단하게 생각했던 직렬화에서도 요구사항에 맞는 올바른 직렬화와 역직렬화를 하기 위해서는 여러 옵션들을 고려해야합니다. 

옵션에 대해 잘 알아보고 사용하지 않으면 프로덕션에서 예상치 못한 예외가 발생할 수 있기에 옵션의 종류에 대해서도 살펴봄과 동시에 테스트시에도 여러 데이터 타입에 대해 테스트를 해보아야합니다.

또한 guava 모듈 등 Jackson에서 제공하는 여러 모듈들에 대해서도 알아보고 사용해보면 여러 직렬화 문제를 해결하는데에 도움이 될 수 있을 것입니다. 

감사합니다.

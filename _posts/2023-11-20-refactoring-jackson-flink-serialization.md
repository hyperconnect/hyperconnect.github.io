---
layout: post
date: 2023-11-20
title: Jackson과 Scala 기반 Flink를 사용한 코드 리팩토링 과정에서 발생한 Serialization 관련 이슈 해결하기
author: suno
tags: jackson flink serialize
excerpt: Jackson과 Scala 기반 Flink를 사용한 코드를 리팩토링하는 과정에서 발생한 Serialization 관련 이슈들을 살펴보고 이를 해결한 방법들을 공유합니다.
last_modified_at: 2023-11-20
---

안녕하세요! Azar Matching Dev Team의 Suno 입니다.

이 글에서는 Scala Flink 코드의 리팩토링 과정에서 발생한 Jackson과 Flink의 Serialization 이슈를 해결한 경험을 공유합니다. 크게 Jackson 파트와 Flink 파트로 나누어 구성되어 있습니다.

# 들어가며

Azar는 하이퍼커넥트의 대표 Product로 2013년 첫 출시 이후 긴 시간동안 지금까지 많은 유저들에게 사랑받고 있습니다. Product에는 지속적으로 다양한 종류의 변화가 있어왔지만, 즉각적으로 영상 기술을 기반으로 새로운 사람들을 만나는 경험을 제공하는 "1:1 Video Chat"이 저희의 핵심 기능으로 자리잡은 상황입니다. 

Azar Studio의 Matching Dev Team에서는 초당 천 단위로 들어오는 유저들의 요청을 기반으로 신속하게 대화할 상대방을 결정하는 Match Making 영역을 담당하고 있습니다. 저희는 Apache Flink의 고성능 실시간 스트리밍 처리를 기반으로 다양한 요구사항을 만족시키기 위한 컴포넌트들을 개발하고 있습니다.

Azar는 오랜 기간동안 서비스된 만큼 대부분의 프로젝트에는 회사 초창기부터 존재해왔던 레거시 코드들이 존재합니다. 당연히 저희 팀도 예외가 아니었는데요, Scala로 작성된 최신 프로젝트에 일부 Java 코드가 남아 있어서 호환성 문제로 인한 성능이나 코드 유지보수성에 악영향을 미쳤습니다. 이번에 저는 이러한 부분을 Scala로 리팩토링 하며 최신화 했고, 코드베이스에서 기존의 Java 코드를 완전히 없애는 작업까지 진행하게 되었습니다.

# 리팩토링

이 글에서 다룰 이슈와 관계가 있는 리팩토링만 간략하게 공유드리겠습니다.

아래는 `UserProfile`이라는 DTO를 Java 클래스(POJO)에서 Scala case class로 리팩토링한 예시입니다. (Scala의 case class는 데이터를 담는 용도로 사용되며, Kotlin의 data class와 같습니다.)

*UserProfile.java*
```java
public class UserProfile (
  private String userId;
  private long requestedTime;
  @Nullable private Gender gender;
  private ExtraInfo extraInfo;
  
  public UserProfile(
      String userId,
      long requestedTime,
      @Nullable Gender gender,
      ExtraInfo extraInfo) {
    this.userId = userId;
    this.requestedTime = requestedTime;
    this.gender = gender;
    this.extraInfo = extraInfo;
  }

  public String getUserId() {
    return userId;
  }

  public void setUserId(String userId) {
    this.userId = userId;
  }

  ...
}

public enum Gender { ... }
```

*UserProfile.scala*
```scala
case class UserProfile (
  @BeanProperty userId: String,
  @BeanProperty requestedTime: Long,
  @BeanProperty gender: Option[Gender],
  @BeanProperty extraInfo: ExtraInfo
)

object Gender extends Enumeration { ... }
```

리팩토링에서 이루어진 변화는 크게 2가지입니다.

1. POJO가 Scala case class로 변경되었습니다.
2. 일부 필드(멤버 변수)의 타입이 Scala에 맞게 변경되었습니다.
  - `@Nullable` → `Option`
  - Java collection → Scala collection (e.g. `Map`, `Set`)
  - Java enum → Scala Enumeration

POJO를 case class로 Scala스럽게 변경하면서 일부 필드의 타입이 변경되었고 이로 인해 몇 가지 긍정적인 효과를 얻을 수 있었습니다. 먼저 nullable한 필드를 `Option` 필드로 변경하면서 nullability를 컴파일 타임에 알 수 있게 되어 코드의 안정성을 강화할 수 있었습니다. 또, 기존에는 레거시 코드로 인해 POJO 하위에 Scala case class를 필드로 가지는 경우가 있었는데, 이런 경우 Flink 내부적으로 POJO가 아닌 `GenericType`으로 인식하게 되면서 serialization 성능이 떨어지는 문제가 있었습니다. POJO를 모두 제거하고 case class 의 필드 타입도 모두 POJO 대신 case class로 변경하면서 Flink의 serialization 속도가 향상될 수 있었습니다.

반면, 리팩토링으로 인해 serialization 코드에서 예상치 못한 이슈들이 발생하게 되었습니다. 지금부터 그 문제 상황과 찾아낸 해결 방법에 대해서 공유하겠습니다.

# Jackson Serialization으로부터 발생한 이슈

저희 프로젝트는 JSON serialization 라이브러리로 Jackson을 사용하고 있습니다. 리팩토링 이전에는 Jackson을 통해 serialize가 이루어지는 대부분의 클래스들이 Java 클래스로 작성되어 있었습니다. 외부 시스템과의 인터페이스 역할을 하는 클래스들이었기 때문에 만들어진 시점부터 거의 변경되지 않은 상태로 있었는데, 이번 리팩토링으로 필드 타입들이 Scala 타입으로 변경되면서 결국 문제가 발생하게 되었습니다.

## 필드 타입의 변경으로 발생한 Serialization 오류

예시를 들어 설명해 보겠습니다. 아래 `Person` 클래스는 `Color`라는 Scala Enumeration과 `Option[Int]`를 필드로 가지고 있습니다. 이 클래스의 인스턴스를 Jackson을 이용해 serialize하게 되면 잘못된 출력을 하게 됩니다.

```scala
case class Person(
  @BeanProperty name: String,
  @BeanProperty age: Option[Int],
  @BeanProperty favoriteColor: Color
)
object Color extends Enumeration {
  type Color = Value
  val RED, BLUE, GREEN = Value
}

val objectMapper = new ObjectMapper()
println(objectMapper.writeValueAsString(Person("Suno", Some(27), Color.BLUE)))

// 기대했던 출력
// > {"name":"Suno","age": 27,"favoriteColor": "BLUE"}

// 실제 출력 결과
// Option 필드와 Enumeration 필드가 비정상
// > {"name":"Suno","age":{"empty":false,"defined":true},"favoriteColor":{}}
```

## jackson-module-scala

이 문제를 해결하기 위해서 [jackson-module-scala](https://github.com/FasterXML/jackson-module-scala#readme)라는 라이브러리를 찾아서 사용하게 되었습니다. 이 라이브러리는 `DefaultScalaModule`이라는 Jackson module을 제공하는데, 이 모듈을 사용하면 Jackson에서 Scala case class, `Sequence`, `Map`, `Tuple`, `Option`, Enumeration의 de/serialize가 지원이 됩니다. 

jackson-module-scala를 적용한 이후, 유닛 테스트를 통해서 대부분 정상적으로 serialize되는 것이 확인되었습니다. 그러나 Scala Enumeration의 경우에는 여전히 기존의 Java enum과 다르게 serialize되는 문제가 지속되었습니다.

```scala
val objectMapper = new ObjectMapper().registerModule(DefaultScalaModule)
println(objectMapper.writeValueAsString(Person("Suno", Some(27), Color.BLUE)))

// Enumeration 필드가 비정상
// > {"name":"Suno","age":27,"favoriteColor":{"enumClass":"Main$Color$2","value":"BLUE"}}
```

jackson-module-scala를 적용한 상태로 serialize를 해 보면 위와 같이 출력되는 것을 확인할 수 있습니다. Scala Enumeration은 Java와 다르게 런타임에서 각 enum의 타입이 아닌 `Enumeration#Value`라는 [하나의 타입으로 인식](https://www.baeldung.com/scala/case-objects-vs-enumerations#a-summary-of-scala-enumerations)이 됩니다 (*참고로 Scala 3부터는 [Java enum과 동일한 방식](https://docs.scala-lang.org/scala3/reference/enums/enums.html#compatibility-with-java-enums)으로 구현되게 바뀌어 아래 서술할 내용은 해당되지 않습니다!*). 이로 인해 reflection을 통한 타입 추론이 불가능해져, jackson-module-scala에서는 Scala Enumeration을 serialize할 경우 [Enumeration 타입을 함께 적어주도록 구현](https://github.com/FasterXML/jackson-module-scala/wiki/Enumerations#backward-compatibility)된 것입니다.

jackson-module-scala의 [wiki](https://github.com/FasterXML/jackson-module-scala/wiki/Enumerations)를 살펴보면 이를 어떻게 해결할 수 있는지 서술되어 있습니다. Enumeration 필드에 `@JsonScalaEnumeration` 어노테이션을 달아주면 serialize가 기존과 같이 정상적으로 작동하게 됩니다.

```scala
class ColorType extends TypeReference[Color.type]
case class ColorHolder(@JsonScalaEnumeration(classOf[ColorType]) color: Color.Color)
```

위 방법으로 Jackson과 관련된 serialization 이슈를 해결할 수 있으나, 고민 끝에 저는 모든 Enumeration 필드에 어노테이션을 추가하는 것은 저희 프로젝트에서는 적절하지 않은 방법이라고 판단했습니다. 대량의 boilerplate가 추가되는 것이 좋은 해결방안이라고 생각하지 않았기 때문인데요. 대신에 저는 다음과 같이 커스텀 `ObjectMapper`를 구현해서 다른 방법으로 이슈를 해결하기로 결정했습니다.

### 커스텀 ObjectMapper의 구현

```scala
import com.fasterxml.jackson.core.JsonGenerator
import com.fasterxml.jackson.databind.{JsonSerializer, Module, ObjectMapper, SerializerProvider}
import com.fasterxml.jackson.databind.module.SimpleModule
import com.fasterxml.jackson.module.scala.{DefaultScalaModule, ScalaObjectMapper}

class HyperObjectMapper extends ObjectMapper() with ScalaObjectMapper {  // (1)
  
  this.registerModule(DefaultScalaModule)                                // (2)

  val enumSerializerModule: Module = new SimpleModule()                  // (3)
    .addSerializer(classOf[Color], new ScalaEnumSerializer(Color))
  this.registerModule(enumSerializerModule)
}

// 'Enum.toString()' 메소드를 이용한 커스텀 JsonSerializer
class ScalaEnumSerializer[T <: Enumeration](e: T) extends JsonSerializer[T#Value] {
  override def serialize(value: T#Value, generator: JsonGenerator, provider: SerializerProvider): Unit =
    generator.writeString(value.toString)
}
```

커스텀 `ObjectMapper`인 `HyperObjectMapper` 의 구현을 살펴보겠습니다.

(1) Jackson의 `ObjectMapper`를 상속받고, jackson-module-scala에서 유틸리티 메소드들을 추가한 `ScalaObjectMapper` trait을 가집니다.

(2) 앞서 언급했던 Jackson module인 `DefaultScalaModule`을 등록합니다.

(3) 프로젝트에서 사용하는 **모든** Enumeration들의 커스텀 JsonSerializer를 추가하는 모듈을 만들고 이를 등록합니다.

코드베이스에서 `ObjectMapper` 를 모두 `HyperObjectMapper`로 변경하고, 마침내 Scala 클래스들을 기존 POJO들과 동일하게 serialize되게 만들 수 있었습니다. 👏

커스텀 `ObjectMapper`를 구현해서 사용하는 방법은 모든 클래스들의 Enumeration 필드에 어노테이션을 추가하지 않고 문제를 해결할 수 있다는 장점이 있습니다. 또한 매번 등록해야 하는 `DefaultScalaModule`을 wrapping한 덕분에 code duplication을 줄일 수 있다는 장점도 있습니다. 그러나 커스텀 `ObjectMapper` 코드에 코드베이스에서 사용하는 모든 Enumeration을 등록해야 하기 때문에, 확장성이 떨어진다는 단점이 있습니다. Deserialization은 위 방법으로 해결할 수 없다는 것도 문제입니다. 하지만 저희는 단점보다 장점이 더 크다고 판단하여 커스텀 `ObjectMapper`를 사용하게 되었습니다. 여러분도 trade-off를 고려하여 상황에 적절한 방법을 선택하시기 바랍니다.

# Flink Serialization으로부터 발생한 이슈

저희 프로젝트에서는 Jackson의 serialization 뿐만 아니라, Flink Streaming에서도 operator간의 데이터 전송을 위해 serialization과 deserialization이 이루어지고 있습니다. 불행하게도 앞서 살펴본 리팩토링 작업이 Flink serialization에도 영향을 미쳐 런타임 에러가 발생하게 되었습니다.

Flink는 [조건을 만족하는 데이터 타입](https://nightlies.apache.org/flink/flink-docs-release-1.17/docs/dev/datastream/fault-tolerance/serialization/types_serialization/)에 한해 빠른 속도의 serialization을 제공하고 있습니다. 조건을 만족하는 대표적인 것이 POJO와 Scala case class입니다. 리팩토링 작업은 POJO 클래스를 Scala case class로 변경하는 것이었기 때문에, 저는 별다른 문제 없이 serialization이 가능할 것이라고 예상했습니다. 그러나 실제로 진행해 보니 POJO와 Scala case class는 각각 [POJOSerializer](https://github.com/apache/flink/blob/release-1.17.0/flink-core/src/main/java/org/apache/flink/api/java/typeutils/runtime/PojoSerializer.java)와 [ScalaCaseClassSerializer](https://github.com/apache/flink/blob/release-1.17.0/flink-scala/src/main/scala/org/apache/flink/api/scala/typeutils/ScalaCaseClassSerializer.scala)로 다르게 구현이 되어 있어, 이에 맞춘 변경 작업을 진행해야 했습니다.

ScalaCaseClassSerializer가 case class를 성공적으로 serialize하기 위해서는 다음과 같은 조건이 필요합니다. (모든 조건을 나열한 것이 아닙니다!)

1. 필드가 하나 이상인 *클래스*를 상속받지 않아야 합니다.
2. *Scala* 타입 필드에 null값이 존재하지 않아야 합니다 (Java 타입은 예외, e.g. String, java.util.Date)

각각에 대해 어떻게 해결했는지 살펴보겠습니다.

## 1. 클래스 상속 조건 해결하기

먼저 클래스 상속 조건에 대해 살펴보겠습니다. ScalaCaseClassSerializer는 POJOSerializer와 달리 [TupleSerializerBase](https://github.com/apache/flink/blob/release-1.17.0/flink-core/src/main/java/org/apache/flink/api/java/typeutils/runtime/TupleSerializerBase.java)를 상속받고 있어, serialization되는 case class들은 상속 관계를 가지면 안 됩니다. (대신 런타임에 reflection을 사용하지 않아 더 빠르다는 장점이 있습니다!) 저는 이 문제를 해결하기 위한 3가지 방법을 찾았는데 이것을 공유드리겠습니다.

**a. POJOSerializer 사용하기**

Scala case class도 조건을 만족한다면 POJOSerializer로 serialize될 수 있습니다. 하지만 마지막 조건 때문에 사용하기 어렵습니다.

- public한 case class여야 합니다.
- 인자가 0개인 default constructor가 존재해야 합니다.
- 모든 필드는 getter와 setter 함수로 접근 가능해야 합니다.
- 필드의 타입이 등록된 serializer에서 지원되는 것이어야 합니다. (`Option`, `Either` 등 미지원)

**b. flink-adt 사용하기**

[flink-adt](https://github.com/findify/flink-adt#readme)라는 라이브러리를 사용하면 sealed trait을 이용한 상속 관계가 case class에 존재하더라도 ScalaCaseClassSerializer가 성공적으로 serialize할 수 있습니다. 그러나, 저희 프로젝트는 flink-adt를 사용할 수 없는 환경이어서 적용하지 못했습니다.

**c. 클래스 상속 관계 제거하기**

조건이 맞는다면 가장 쉬운 방법으로, 클래스의 상속 관계를 제거하는 방법이 있습니다.

*상속 관계 제거 전*
```scala
case class RequestBase(
  requestId: String
  ...
)

class NormalRequest(
  requestId: String
  ...
) extends RequestBase(requestId)

class SpecialRequest(
  requestId: String
  ...
) extends RequestBase(requestId)
```

*상속 관계 제거 후*
```scala
object RequestType extends Enumeration {
  type RequestType = Value
  val normal, special = Value
}

case class Request(
  requestType: RequestType
  requestId: String
)
```

저희 프로젝트에서 Flink Streaming에 사용되는 클래스의 상속은 위와 같이 하위 클래스간의 필드 변화 없이 단순히 하위 클래스간의 구분을 위한 것이었습니다. 덕분에 두 하위 클래스를 하나로 합치고 `requestType`이라는 필드로 구분되도록 수정하여 ScalaCaseClassSerializer를 통한 serialization이 가능하도록 만들었습니다.

## 2. 런타임의 null값 제거하기

ScalaCaseClassSerializer가 클래스 인스턴스를 serialize할 때, Scala 타입 필드에 null값이 있으면 런타임 에러가 나게 됩니다 ([source code](https://github.com/apache/flink/blob/af6eff873a53bbdc85a2b1018140754e65758e3e/flink-scala/src/main/scala/org/apache/flink/api/scala/typeutils/CaseClassSerializer.scala#L105-L110)). 따라서 `Option`을 null값 대신 사용하는 것이 권장됩니다. 처음에는 null값이 들어올 수 있는 필드들을 `Option`으로 바꾸기만 하면 되는 작업이라고 생각했지만, 런타임에 null값이 발생하는 필드들을 모두 파악하는 것은 쉬운 일이 아니었습니다. 기존 코드가 Java로 작성되어 있었기 때문에 관련된 코드베이스가 모두 null값을 처리하는 로직을 가지고 있었기 때문입니다. 몇 번의 시행착오를 거친 결과 안정적으로 변경할 수 있는 프로세스를 터득했는데, 다음과 같습니다.

1. 코드에서 null값이 들어올 수 있는 필드를 전부 찾아냅니다. 기존 Java 코드가 `@Nullable`과 같은 어노테이션으로 분류가 되어 있었다면 쉽게 찾을 수 있습니다. 만약 그렇지 않다면, case class가 생성되는 코드를 일일이 확인해서 찾아내야 합니다. (IntelliJ의 경우 `Find Usages -> Method 'apply'`로 확인) 

2. null값이 들어올 수 있는 필드를 모두 `Option` 필드로 변경합니다.

3. 변경된 필드를 읽거나 쓰는 코드를 일일이 확인해서 알맞게 수정합니다. 이것을 나중에 하는 이유는, 컴파일 에러와 경고를 통해서 빠짐없이 모든 필드를 변경할 수 있기 때문입니다. 대부분 컴파일 에러가 나지만, 아래와 같은 코드는 에러가 아닌 경고가 출력이 되기 때문에, 경고도 모두 확인해야 합니다.

```
val optionField: Option[Int] = Some(1)
if (optionField == 1) { ... }
```

## Flink Operator에서 발생하는 TypeInformation 추론 이슈

저희 프로젝트는 Flink streaming API를 Scala가 아닌 Java 버전으로 사용하고 있습니다. flink-streaming-scala가 [Flink 1.17부터 deprecate될 예정](https://cwiki.apache.org/confluence/display/FLINK/FLIP-265+Deprecate+and+remove+Scala+API+support)이기 때문입니다. Java API를 사용하게 되면, Scala case class의 적절한 TypeInformation을 API에서 추론하지 못해 성능이 저하되는 문제가 있습니다. 보통 다음과 같은 경고 로그가 발생한다면 특정 Flink operator에서 TypeInformation을 제대로 추론하지 못하고 있다는 뜻입니다.

```
No fields were detected for class scala.Option so it cannot be used as a POJO type and must be processed as GenericType.
```

이 경고 로그가 발생하는 과정은 다음과 같습니다.

1. 특정 Flink operator의 출력 타입이 Scala case class일 때, 이를 case class로 인식하지 못함
2. Fallback으로 출력 타입을 POJO로 인식을 하려고 시도함
3. PojoSerializer가 지원하지 않는 `Option` 타입을 만나 위의 경고가 출력

이것을 해결하기 위한 2가지 방법을 소개드리겠습니다.

**1. DataStream API에서 TypeInformation을 명시적으로 적어주기**

```scala
import org.apache.flink.api.scala.createTypeInformation

val newStream: DataStream[Person] = stream
  .map(myFlinkOperator, createTypeInformation[Person])
```

먼저 Flink JobGraph를 생성하는 코드에 TypeInformation을 명시적으로 적어 주는 방법이 있습니다. flink-scala에서 제공하는 `createTypeInformation` 매크로를 사용하면 case class의 TypeInformation을 쉽게 생성할 수 있습니다. 참고로 `createTypeInformation` 매크로가 위치한 flink-scala 라이브러리는 flink-streaming-scala와 다르게 계속 maintain되고 있습니다.

**2. Operator에서 TypeInformation을 명시적으로 적어주기**

```scala
import org.apache.flink.api.scala.createTypeInformation

class MyFlinkeOperator extends MapFunction[Person, Person] with ResultTypeQueryable[Person] {
  override def getProducedType: TypeInformation[Person] = createTypeInformation[Person]
}
```

다음으로 각 operator에 TypeInformation을 적어 주는 방법이 있습니다. `ResultTypeQueryable` 인터페이스를 상속받게 되면 `getProducedType` 함수를 구현해야 하는데, 여기서 명시적으로 TypeInformation을 제공할 수 있습니다.

저희 프로젝트의 경우 위의 방법으로 모든 Flink serialization 이슈가 해결되었으나, 이 코드 외에도 문제가 발생한다면 OutputTag, AsyncDataStream 등 Flink Streaming API 전반에서 TypeInformation이 올바르게 생성되고 있는지 확인해야 합니다.

# 마치며

이 글에서는 리팩토링으로 인해 발생할 수 있는 Serialization 이슈들의 종류와, 이후 이를 해결하는 방법에 대한 디테일한 내용 위주로 설명을 드렸습니다. 여기서 다루지는 않았지만 이슈를 찾아내는 과정은 쉽지 않았습니다. Jackson 의 경우 serialization 테스트 코드가 일부 작성되어 있었고, 이를 활용할 수 있었던 반면 Flink 는 serialization 테스트 코드가 없었기 때문에 직접 서버를 실행시켜보면서 발생하는 런타임 에러를 통해 이슈를 발견해야만 했습니다. 이 과정을 통해 그동안 그다지 중요하지 않다고 여겨져 왔던 serialization 관련 테스트 코드들의 중요성을 느꼈습니다. ChatGPT, GitHub Copilot 등을 활용할 수 있게 되면서 유닛 테스트를 작성하는 데 드는 노력이 많이 줄어들었는데, 이 글을 계기로 각자의 프로젝트에 serialization 테스트 코드를 작성해 보면 어떨까 제안하면서 긴 글을 마치겠습니다. 읽어주셔서 감사합니다!

# References

- [https://github.com/FasterXML/jackson-module-scala#readme](https://github.com/FasterXML/jackson-module-scala#readme)
- [https://github.com/FasterXML/jackson-module-scala/wiki/Enumerations](https://github.com/FasterXML/jackson-module-scala/wiki/Enumerations)
- [https://github.com/findify/flink-adt#readme](https://github.com/findify/flink-adt#readme)
- [https://github.com/apache/flink](https://github.com/apache/flink)
- [https://www.baeldung.com/scala/case-objects-vs-enumerations](https://www.baeldung.com/scala/case-objects-vs-enumerations)
- [https://docs.scala-lang.org/scala3/reference](https://docs.scala-lang.org/scala3/reference)
- [https://nightlies.apache.org/flink/flink-docs-release-1.17](https://nightlies.apache.org/flink/flink-docs-release-1.17)

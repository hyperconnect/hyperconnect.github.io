---
layout: post
date: 2019-11-18
title: 흔한 RxJava Subject 오용 사례들
author: evan
tags: android rxjava reactive
excerpt: RxJava 를 사용할 때 흔히 보이는 Subject 오용 사례를 통해 Subject 를 사용할 때 특별히 신경써야 하는 부분들에 대해 알아봅시다.
last_modified_at: 2019-11-18
---

안드로이드 앱 제작에 있어 RxJava 가 대세 기술로 떠오른지 제법 되었습니다. 제가 RxJava 를 처음 접하면서 기존 코드와의 이질감에 상당한 거부감을 느꼈던 것이 엊그제 같은데 이제 RxJava 없이는 더 이상 앱을 만들지 못하는 몸이 되어버렸습니다.

RxJava 를 잘 사용하면 놀라울 정도의 코드 유연성, 생산성, 안정성을 모두 확보할 수 있습니다. 이 중에 하나만이라도 제대로 하기 어려운데 모두 다 가질 수 있다니 약장수 냄새가 나는 것 같지만 이것은 실제 경험담입니다. 물론 여기에는 **잘 사용하면**이라는 마법의 전제가 붙습니다.

그렇다면 RxJava 를 잘 사용한다는 것은 무엇일까요? 이에 대해서 이야기를 하자면 끝이 없습니다. 과장 조금 보태서 수십장의 논문으로 써야하는 정도이죠. 하나의 blog post 에서 다룰 수 있도록 문제를 조금 비틀어서, **잘 사용하는 것**보다 **잘못 사용하는 경우**를 다뤄보려 합니다. 잘못 사용하는 경우 중에서도 가장 흔히 범하는 실수인 **Subject 오용**에 대해 이야기해 보겠습니다.

### 되도록 Subject 를 사용하지 말아라

Rx 를 공부하다보면 **Subject 를 되도록 사용하지 말라**는 말을 여기저기서 접할 수 있습니다. 처음에는 이 말을 듣고 **아니 왜 기껏 쓰라고 만들어놓은 것을 또 쓰지 말라는거지? 이렇게 편한데!** 라고 생각을 했었습니다. 사용하지 말라는 이유를 읽어봐도 도대체가 무슨 소린지 납득이 되지 않았기 때문이죠. 그 이유라는 것이 대강 다음과 같습니다.

1. Subject 는 mutable 하기 때문에 함수형 프로그래밍에 적합하지 않다.
2. Subject 를 사용하면 Observable (Reactive Stream) 규약을 깨뜨리기 쉽다.

꽤 오랜 기간 RxJava 를 빡세게 써보고 나서야 이들이 모두 맞는 말임을 알았지만 처음에는 전혀 와닿지 않을 것입니다. 이 글에서는 RxJava 를 사용해보면서 `Subject` 오용시에 실제로 겪었던 몇가지 문제점들에 대해 알려드리고자 합니다.

## 예제1

`서버에서 받아온 데이터를 emit 하는 Single<Data>` 를 반환하는 `getServerData()` 라는 메서드를 작성해야 하는 상황을 가정해보겠습니다. RxJava 를 접한지 얼마 되지 않으신 분들은 높은 확률로 다음과 같은 방법으로 코드를 작성할 것입니다.

```kotlin
fun getServerData(): Single<Data> {
    val resultSubject = SingleSubject.create<Data>()
    getServerDataApiCall(onSuccess = {
        resultSubject.onSuccess(it)
    }, onError = {
        resultSubject.onError(it)
    })
    return resultSubject
}
```

얼핏 보면 잘 동작할 것만 같은 이 코드에는 여러가지 문제점이 있습니다.

### 문제1. 구독이 발생하기 이전에 데이터를 불러오기 시작한다.

그 중 가장 큰 문제점이라 하면 `getServerData()` 가 반환한 `Single<Data>` 가 구독되기도 전에 서버에서 데이터를 가져오기 시작한다는 점입니다.

보통은 위와 같이 메서드를 만들어 놓고,

```kotlin
getServerData().subscribe {
    // Process data
}
```

이렇게 바로 구독을 하기 때문에 문제가 없을 것 처럼 보입니다. 하지만 `getServerData()` 를 호출하기만 하고 구독을 하지 않는다면 어떻게 될까요?

```kotlin
getServerData() /* .subscribe {} */
```

이 경우에는 데이터를 받아 볼 사람이 없기 때문에 API 호출이 필요가 없는 상황인데도 API 호출을 하게 되는 문제가 있습니다.

여기서, **기껏 Single 을 만들어놓고 구독을 안한다는 것이 말이 되느냐?** 고 반문하실 수도 있겠습니다. 네, 물론 위의 코드는 아무런 의미가 없는 코드이며 아무도 일부러 이런 코드를 작성하지는 않겠죠. 하지만 비즈니스 로직이 복잡해지고, 그에 따라 체인이 복잡해지면 이야기가 달라집니다.

```kotlin
fun getAlternativeData(): Maybe<Data> {
    // alternative 데이터를 가져오는 로직
}

// alternative 데이터와 서버 데이터를 순차적으로 가져오되, 제일 처음으로 가져온 하나의 데이터만 취하여 처리한다.
Maybe
    .concat(
        getAlternativeData(),
        getServerData().toMaybe()
    )
    .take(1)
    .subscribe {
        // Process data
    }
```

이 때 만약 alternative 데이터를 성공적으로 받아왔을 경우 `getServerData()` 에 대한 구독은 발생하지 않고 그냥 넘어가게 됩니다. 구독이 발생하지 않았다는 이야기는 서버 데이터가 필요없다는 이야기이고, 이는 곧 API 호출을 안해도 된다는 말입니다. 하지만 저희가 작성한 메서드는 `Single<Data>` 의 구독 시점이 아니라 `getServerData()` 의 호출 시점에 API 를 호출하기 때문에, 결국 API 호출이 필요하지 않은 경우에도 API 호출을 하게 되는 것입니다.

RxJava 의 모든 비동기 스트림은 구독이 시작되었을때 emission 을 시작하고, 구독이 끝났을 때 emission 을 정지하는 것이 규약입니다. 관련 내용은 [여기](http://reactivex.io/documentation/contract.html)에서 확인하실 수 있습니다.

> An Observable may begin issuing notifications to an observer immediately after the Observable receives a Subscribe notification from the observer.
>
> When an observer issues an Unsubscribe notification to an Observable, the Observable will attempt to stop issuing notifications to the observer. It is not guaranteed, however, that the Observable will issue no notifications to the observer after an observer issues it an Unsubscribe notification.

**must** 가 아니라 **may** 라고 표현하고 있기는 하지만 RxJava 의 모든 operator 와 동작들이 이런 컨벤션을 바탕으로 제작되었기 때문에, RxJava 를 제대로 활용하려면 모든 비동기 스트림이 이 규약을 따르도록 만드는 것이 좋습니다.

### 문제2. 다수의 구독, 재구독에 대한 처리가 미흡하다.

RxJava 에서는 명시적으로 Hot Observable 을 만들지 않는 이상 기본적으로 모든 Observable 은 Cold Observable 입니다. 즉, 구독이 발생할 때마다 emission 이 처음부터 시작된다는 뜻이죠.

`getServerData()` 를 다음과 같이 사용하는 경우를 가정해보겠습니다.

```kotlin
val dataFromServer = getServerData()
dataFromServer.subscribe {
    // data processing logic 1
}
dataFromServer.subscribe {
    // data processing logic 2
}
```

저희는 `getServerData()` 를 따로 Hot Observable 로 설계하지 않았기 때문에 기본적으로 Cold Observable 로 동작해야 합니다. Cold Observable 로 동작할 경우 위의 코드에서 API 호출이 2번 발생해야 하는데, 실제로는 1번 밖에 요청되지 않습니다. 마치 Hot Observable 처럼 동작하는 것이죠. 이는 의도하지 않은 동작이기 때문에, 이 상태에서 `getServerData()` 사용처가 많아지면 많아질수록 버그가 발생할 확률도 높아지게 됩니다.

그런데 여기서 더 중요한 문제가 있습니다. 실제로 많이 접하게 되는 요구사항인 `API 호출이 실패하면 최대 3회까지 재시도`하는 로직을 RxJava 로 작성한다고 해봅시다. 

```kotlin
getServerData()
    .retry(3)
    .subscribe {
        // ...
    }
```

RxJava 를 사용하지 않았으면 힘들게 구현했을 재시도 로직이 정말 간단하게 구현되었죠. 하지만! 애석하게도 이 코드는 저희가 원하는대로 동작하지 않습니다. `retry()` operator 는 `onError()` 발생시 원본 스트림을 재구독 하도록 작성되어 있는데, 저희가 만든 `getServerData()` 는 구독을 여러번 한다고 해서 API 호출을 여러번 하도록 만들어지지 않았기 때문입니다.

### 문제 3. 취소 처리가 미흡하다.

서버 데이터를 가져오는 도중에 Activity 가 종료되는 등의 이유로 더 이상 서버 데이터를 가져올 필요가 없을 경우 `getServerData()` 에 대한 구독을 dispose 하게 됩니다. 하지만 여기에서는 dispose 를 해도 서버에 대한 요청이 취소되지 않습니다.

### 해결

그렇다면 위에서 언급한 문제가 없도록 만들려면 어떻게 해야 할까요? `Subject` 를 사용하는 대신 다음과 같이 `create()` 를 사용하면 됩니다.

```kotlin
fun getServerData(): Single<Data> {
    return Single.create { emitter ->
        getServerDataApiCall(onSuccess = {
            emitter.onSuccess(it)
        }, onError = {
            emitter.onError(it)
        })
    }
}
```

비동기 스트림을 만드는 방법으로는 `create()` 외에도 `fromCallable()`, `defer()`, `generate()` 등이 있습니다. 이 메서드들을 활용하면 대부분의 경우에 올바른 스트림을 만들 수 있습니다.

## 예제2

이제 `Single.create()` 를 사용하여 `getServerData()` 를 올바르게 수정하였지만, 여기서 또 흔하게 하는 실수가 있습니다. 이번에는 서버에서 데이터를 가져온 후 2개의 Fragment 에 이를 보여주는 상황을 가정해보겠습니다. 이 경우 또한 보통 다음과 같이 코드를 작성할 것입니다.

```kotlin
class DataRepository {
    private var dataLoading = false
    private val loadedData = BehaviorSubject.create<Data>()

    fun loadData() {
        if (!dataLoading) {
            dataLoading = true
            getServerData()
                .subscribe({
                    dataLoading = false
                    loadedData.onNext(it)
                }, {
                    dataLoading = false
                    loadedData.onError(it)
                })
        }
    }

    fun getLoadedData(): Observable<Data> = loadedData
}

class Fragment1 : Fragment() {
    @Inject
    lateinit var dataRepository: DataRepository

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        dataRepository.loadData()
        dataRepository.getLoadedData()
            .subscribe {
                textView.text = it.toString()
            }
    }
}

class Fragment2 : Fragment() {
    // Fragment1 과 동일한 code
}
```

### 문제

여기에는 다음과 같은 문제들이 존재합니다.

1. 반응형 스트림은 구독을 하면 아이템이 emit 되어야 하는데, 여기서는 `loadData()` 를 호출하기 전까지 `getLoadedData()` 는 어떠한 아이템도 emit 하지 않습니다. `loadData()` 호출 상태에 따라 emission 이 달라지므로 stateful 한 코드입니다. 상태는 많으면 많을수록 관리 비용이 증가하게 됩니다.
2. `getLoadedData()` 를 사용하는 쪽에서 `loadData()` 를 반드시 미리 호출해줘야 한다는 사실을 항상 알고있어야 합니다. 알아야 할 게 많으면 많을수록 버그 발생 가능성은 높아지는 법입니다. 메서드 사용자가 혹시라도 이런 부분을 놓치게 되면 아이템이 emit 되지 않는 현상에 대해 디버깅하는 시간을 추가적으로 소모해야 하고, 작업 시간이 증가되는 결과를 낳습니다.
3. `loadData()` 호출 시점이 애매해질 수 있습니다. 예제에서처럼 `getLoadedData()` 가 단순하게 호출되는 경우라면 큰 문제가 없지만, 비즈니스 로직이 복잡해지면 Rx 체인이 거대해지게 되고, 이 거대한 체인 중간에 `getLoadedData()` 가 끼어들어가게 되면 그 때는 `loadData()` 를 언제 어디에서 호출해줘야 하는지 알기 어렵게 됩니다.
4. [예제1 의 문제2](#문제2-다수의-구독-재구독에-대한-처리가-미흡하다) 가 여기서도 동일하게 존재합니다. 데이터 로딩에 재시도 전략을 적용하기 위해 `getLoadedData()` 에 `retry()` operator 를 적용해도 원하는 대로 동작하지 않습니다.
5. [예제1 의 문제3](#문제-3-취소-처리가-미흡하다) 가 여기서도 동일하게 존재합니다. 데이터 로딩 중에 `dispose()` 를 호출하여 취소하여도 실제 서버 요청은 취소되지 않습니다.

### 해결

동일한 데이터를 여러 곳에서 사용할 경우 대부분 Hot Observable 을 만들어 사용하면 좋습니다.

```kotlin
class DataRepository {
    private val dataLoader = getServerData().cache()

    fun loadData(): Observable<Data> = dataLoader
}

class Fragment1 : Fragment() {
    @Inject
    lateinit var dataRepository: DataRepository

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        dataRepository.loadData()
            .subscribe {
                textView.text = it.toString()
            }
    }
}

class Fragment2 : Fragment() {
    // Fragment1 과 동일한 code
}
```

사실 이 코드도 실제 상황에서 모든 경우를 다 커버해주지는 못하지만, 일반적인 경우에서는 위에 언급한 문제들은 모두 해결되게 됩니다.

## 결론

`Subject` 자체는 나쁜 것이 아닙니다. 나쁜 것이라면 RxJava 에서 아예 만들지를 않았겠죠. 좋은 의도를 가지고 만들어진 클래스이나, 막상 사용하다보니 잘못 사용하게 되는 경우가 많은 것이 문제입니다.

`Subject` 를 적재적소에 잘 사용하려면 많은 경험이 필요하지만, 그 전에는 일단 위에서 예를 들었던 두가지 예제의 경우만 유의해도 RxJava 를 꽤 나이스하게 활용할 수 있습니다.

1. `Subject` 를 사용하기 전에 `create()`, `fromCallable()`, `defer()` 를 사용해 스트림을 만들 수 있는지부터 먼저 생각해본다.
2. 다른 스트림을 구독한 뒤에 그 구독 결과를 `Subject` 로 넘겨서 사용하는 패턴을 피한다.

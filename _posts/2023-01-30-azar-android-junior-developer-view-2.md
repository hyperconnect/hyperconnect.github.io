---
layout: post
date: 2023-01-30
title: Junior 개발자의 글로벌 서비스 경험기 2탄
author: tay, mason
authors:
  - tay
  - mason
tags: android junior
excerpt: 아자르 Android팀의 주니어 개발자들의 글로벌 서비스 경험 중 '네트워크'와 '이미지 최적화' 그리고 '리모컨과 A/B 테스트'에 대한 이야기를 소개합니다.
---

안녕하세요 👋
하이퍼커넥트 아자르 스튜디오 Android 팀의 Tay, Mason 입니다.

지난 [Junior 개발자의 글로벌 서비스 경험기 1탄](https://hyperconnect.github.io/2022/07/06/azar-android-junior-developer-view.html) 에서는 언어에 관련된 이야기와 앱갤러리에 관한 이야기를 전해드렸었는데요.<br>
1탄에서 예고했던 것 처럼 2탄에서는 저희가 네트워크가 느린 국가를 고려했던 경험과 이미지 최적화를 위한 노력, 그리고 리모컨을 활용한 경험에 대해 이야기 해보도록 하겠습니다.

## 캐싱

### 네트워크가 느린 국가를 고려하자!

여러분들은 네트워크가 느린 환경에 대비하여 코드를 구현하고 계신가요?

글로벌 서비스인 아자르를 개발하면서 느꼈던 점은, 네트워크가 느린 국가가 생각보다 많다는 점이었습니다.
이런 환경에 대비하여 아자르는 api 결과값을 빈번하게 메모리 캐쉬하고 있습니다. 또한 아자르는 반응형으로 구현되어 있어서, 이를 위한 캐시 클래스를 자체적으로 만들어서 사용 중인데요. 한 번 살펴보도록 하겠습니다.

### 네트워크가 느린 국가

![internet_speeds_by_country]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/internet_speeds_by_country.jpeg" | absolute_url}})

튀르키예, 알제리, 인도 국가 사용자들은 아자르 앱 사용량의 30~40%가 될 만큼 높은 비율을 차지하고 있는데요. 이 국가들에서 적게는 4배, 많게는 11배 정도의 속도 차이가 있는 것을 볼 수 있습니다. (어디까지나 이는 평균치이며, 실제로는 더 느린 경우도 존재할 것입니다. 🤦‍♂️)

### 맞닥뜨린 문제

|광고 진입 화면|보상형 광고|
|---------|---------|
|![gemshop]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/gemshop.png" | absolute_url}})|![reward_ad]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/reward_ad.png" | absolute_url}})|


아자르에는 버튼을 누른 유저에게 광고를 띄우고 보상을 제공하는 기능(보상형 광고)이 있습니다.<br>
광고는 약 30초의 영상 데이터로 100 MB 정도의 용량입니다. 이를 인도 국가의 bandwidth인 17.8 Mbps로 계산해 본다면, 유저에게 전달되기까지 약 45초가 소요된다는 것을 알 수 있습니다.

물론 구글은 로드가 길어지는 경우를 막기 위해, 영상이 20% 정도 버퍼링 될 경우 광고를 재생할 수 있도록 제공하고 있는데요. 20%로 계산을 해도 9초간 딜레이가 발생하게 됩니다.

9초란 시간이 짧아 보일 수 있지만, 앱에서 9초간 프로그레스바가 돌고 있다면 유저 입장에서는 에러가 발생했다고 인식할 수 있을 만큼 긴 시간입니다.

또한 앞서 말씀드렸듯 이는 평균치로 계산한 값이기에 실제로는 더 느린 경우가 다수 존재하고, 광고 시청 중 버퍼링이 걸리는 경우도 고려해야 합니다.

광고의 eCPM(광고수익)이 높아지기 위해서는 광고가 로드되고, CTR(클릭율)이 높아야 하는 것이 기본 요소인데요. 위처럼 광고 시청에 딜레이가 생기게 된다면, 어떤 요소를 넣더라도 유저의 이탈률이 높아질 것입니다. 결국 이는 앱의 광고 수익을 저하시킬 수 있는 요인이 됩니다.

### 미리 로드하고 캐싱하자!

|AS-IS|TO-BE|
|--------|--------|
|![reward_load_flow_as_is]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/reward_load_flow_as_is.png" | absolute_url}})|![reward_ad_load_to_be]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/reward_ad_load_to_be.png" | absolute_url}})|

사실 해결책은 간단합니다. 광고의 로드 시점을 버튼 클릭이 아닌 앱 실행 시로 변경 후 캐싱해 두는 것입니다. 아자르는 이러한 캐싱을 좀 더 유연하게 처리하기 위해, 반응형으로 캐시 클래스를 만들어서 사용 중인데요. 코드를 간략하게 첨부해 보겠습니다.

```kotlin
/**
* @param streamSupplier up-stream을 새로 생성해주는 lambda.
*/
class Cache<T> private constructor(
    defaultValue: T? = null,
    private val streamSupplier: () -> Observable<T>
) {
    private var cachedValue: T? = defaultValue
    private val validSubject = BehaviorSubject.createDefault(defaultValue != null)
    private val loader =
            validSubject
                .distinctUntilChanged()
                .filter { !it }
                .switchMap {
                    streamSupplier()
                        .doOnEach {
                            when {
                                it.isOnComplete -> {
                                    cachedValue = it.value
                                    validSubject.onNext(true)
                                }
                                it.isOnError -> {
                                    validSubject.onNext(false)
                                }
                            }
                        }
                }
                .publish()
                .refCount()
}
```

사용처

```kotlin
val rewardedAdCache = 
        Cache.create<RewardedAd> {
            Observable.create {
                RewardedAd.load()
            }
        }

fun onCreate() {
    // 이미 캐쉬된 RewardAd가 있다면 캐쉬된 값을 emit 한다.
    // 캐쉬된 RewardAd가 없다면 서버로부터 새로 값을 가져와 emit 한다.
    rewardedAdCache.observe()
        .subscribe({},{})

    reloadRewardedAdButton.setOnClickListener {
        // RewardAd 를 갱신한다.
        // rewardedAdCache.observe() 는 새로 가져온 RewardAd 을 추가로 emit 한다.
        rewardedAdCache.invalidate()
    }
}
```

결과적으로는 유저에게 최대한 딜레이 없이 보상형 광고를 제공할 수 있었고, 광고 수익을 높일 수 있었습니다.

네트워크가 느린 환경을 고려한다는 것은 단순하지만 놓치기 쉬운 부분이기에, 항상 염두에 두고 구현하는 습관을 기르면 좋을 것 같습니다.


## 이미지 관련 메모리 최적화

앞서 말씀드린 네트워크 속도를 고려하는 것도 중요하지만 Android 상에서 제공되는 힙 메모리가 무한이 아니기 때문에 메모리에 대한 고민 또한 필요합니다.<br>
즉, 앱에서 사용되는 메모리를 최적화 해주는 것도 중요합니다. (~~사실 이건 글로벌 앱 뿐만 아니라 모든 앱의 공통된 숙명입니다..~~ 😅)

### 어떻게 낭비가 되고 있었는가?

1. 아자르에서 제공하는 placeholder 프로필 이미지와 기본 프로필 이미지는 1080x1080 으로 꽤 큰 크기로 한 장에 4.6MB 정도를 차지하고 있습니다.

2. 아자르 앱에서 사용하는 오픈소스 소프트웨어 목록을 보시면 아셨겠지만 아자르는 이미지 로드 라이브러리로 Fresco를 사용하고 있습니다. Fresco는 프로필 이미지 로딩이 완료되더라도 placeholder의 reference를 해제하지 않아 placeholder가 계속해서 메모리에 올라가 있는 상태가 됩니다.

3. 아자르에서는 placeholder 와 기본 프로필 이미지에 대해 같은 리소스를 사용하고 있는데 프로필 이미지가 없는 경우, 같은 이미지에 대해 메모리를 이중으로 사용하게 됩니다.

정리해보자면 placeholder, 기본 프로필 이미지에 사용되는 이미지가 꽤 큰 크기이므로 최적화를 적절하게 하지 않으면 불필요한 메모리를 지속적으로 잡아먹게 되고 결국 Out of Memory 로부터 고통받을 수 있는 상황입니다. 😱

### 그래서 어떻게 해결할 것인가?

이상적으로는 보여지지 않는 이미지를 메모리에서 해제해주면 해결이 될 것으로 보입니다. 하지만..! Fresco 가 이를 지원해주지 않는 이상 오픈 소스를 사용하는 입장에서는 해결이 쉽지 않을 듯 합니다.

그래서 Azar Android 팀은 아래와 같은 방법을 통해 해결하였습니다.

1. 이미지 포맷을 ARGB_8888 에서 RGB_565 포맷으로 변경하자.
2. placeholder와 기본 프로필 이미지가 동일하므로 프로필 기본 이미지를 출력해야 할 때 별도로 로딩하지 말고 placeholder를 그대로 보여주도록 하자.
3. recycle 되는 view 에서 placeholder 를 해제하도록 하자.
4. (덤으로..) WebP 를 사용해서 앱 용량을 낮추고 품질은 지키자.

### 품질 저하를 걱정하는 리뷰어

2,3 번의 경우 내부 처리에 대한 작업이므로 사용자에게 직접적인 체감이 되는 부분은 없으나 1번의 경우 사용자에게 직접적으로 체감이 될 수 있는 영역이였기에 품질 저하에 걱정이 되는 부분도 있었습니다.

![image_format_review]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/image_format_review.png" | absolute_url}})

다행히도 실제로 작업을 해보니 placeholder와 기본 프로필 이미지에 사용되는 이미지는 사진만큼 정교하고 많은 색상을 사용하지 않기 때문에 눈으로 보기에 뚜렷한 품질 저하는 없었습니다.

> ARGB_8888과 RGB_565 란?
>
> ARGB_8888은 한 pixel을 4byte를 이용해서 색을 표현하는 방식으로 4byte를 사용하기 때문에 색 표현이 우수하다는 장점이 있습니다.
>
> RGB_565는 한 pixel을 2byte로 표현하는 방식이고 16bit를 쪼개서 R(5bit), G(6bit), B(5bit)로 표현하는 방식이다. 2byte를 쪼개서 색을 표현하기 때문에 ARGB_8888 보다 색 표현력이 덜하지만 용량이 작아지는 장점이 있습니다.

|ARGB_8888|RGB_565|
|-------|---------|
|![image_format_argb8888]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/image_format_argb8888.jpg" | absolute_url}}){: width="500px" }|![image_format_rgb565]({{"/assets/2023-01-30-azar-android-junior-developer-view-2/image_format_rgb565.jpg" | absolute_url}}){: width="510px" }|

### Azar Android 팀은 여기서 멈추지 않습니다 !

기본 프로필 이미지의 경우 프로필 카드가 노출되는 곳이라면 어디서든 사용되는 이미지라고 생각해볼 수 있습니다.

그렇다면 어떻게 하면 자주 사용되는 이 기본 프로필 이미지를 로드하는데에 드는 시간을 줄일 수 있을까요?

바로 캐싱을 하는 것입니다. 저희 팀에서 사용하고 있는 이미지 메모리 캐싱 코드를 간략하게 보여드리도록 하겠습니다.

```kotlin
private val caches = SparseArray<WeakReference<Bitmap>>()

fun getBitmap(id: Int): Bitmap? {
    return caches[id]?.get() ?: synchronized(caches) {
        caches[id]?.get() ?: run {
        ... // bitmap 가져올 때의 옵션 설정 등 전처리 코드.
        val bitmap = BitmapFactory.decodeResource(resources, id, options)
        
        bitmap?.let {
            ... // bitmap 후처리 코드.
        }?.also { caches[id] = WeakReferences(it) }
    }
}

```

### 무엇을 얻었는가?

이론적으로 최적화를 진행했지만 실제 메모리 감소를 측정하는 것이 쉽지는 않았습니다.

Android Studio 에서 제공하는 Profiler를 사용했는데 일정 시간 이후 앱이 죽는다거나 메모리 사용량을 MB 단위로 보는 것이 편한데 자꾸 자동으로 GB 단위로 변경된다거나 하는 등의 문제 때문에 측정이 어려웠습니다.

해서 정확한 수치는 아니지만 반복해서 테스트, 측정 해보았을 때 특정 화면, 특정 동작에서 대략 100~130MB 정도 사용되던 메모리가 최적화 작업 이후에는 60~130MB 정도로 최적화 효과를 얻을 수 있었습니다.

## 리모컨과 A/B 테스트

많은 기업에서 A/B 테스트와 세그먼트별 설정이 필요할 때 `Remote Config` 라는 기능을 사용하고 있을 것입니다.

하지만 저희 Azar Android 팀은 해당 기능을 더 편리하고 더 유연하게 사용하고자 Firebase 뿐만 아니라 서버 컨트롤, 클라이언트 컨트롤도 가능하도록 구조를 만들어서 사용하고 있는데요.

어떻게 사용하고 있는지에 대해 간략하게 설명드리도록 하겠습니다.

### 우선 Firebase의 Remote Config가 무엇인가?

앱의 수정사항이 발생했을 때에 운영팀에서는 개발자를 통해서 원하는 방향이 sync가 되어야 하고, 배포까지 진행을 해야 합니다. 

또한, 원하는 타겟층이 있다면 이를 구분지을 수 있는 특정 value를 만들어야 하는 수고까지 추가됩니다.

이를 한번에 해결할 수 있는 방법이 `Remote Config` 라는 기능입니다.

개발자를 통하지 않고 운영팀에서 스스로 값을 수정할 수 있고 배포 없이 특정 타겟층에게만 적용이 가능하게 하는 기능입니다.

### 그래서 아자르에선?

이런 막강한 기능을 가진 `Remote Config` 를 더 편리하게 쓰기 위해 value getter 시에 5단계를 두어서 사용하고 있습니다.

1. 개발 모드에서 설정된 Config 를 사용
2. 서버에서 내려준 Config 를 사용
3. 앱 내 저장소(Shared Preferences) 에 저장된 Config 를 사용
4. Default 로 설정해둔 Config 를 사용
5. empty("") 값 사용

보통은 2번과 4번을 사용하고 NonNull Value로 만들기 위해서 추가로 5번을 사용할 것입니다.

하지만 아자르에서는 QA 테스트를 위해 클라이언트에서 Config 값을 쉽게 바꿀 수 있게 1번을 추가하여 사용중입니다.

또한, 서버에서 내려주는 값을 정상적으로 받아오지 못했을 경우를 대비해서 이전에 정상적으로 받아온 값을 앱 내 저장소에 캐싱해두고 해당 값을 사용하도록 3번을 추가하여 사용하고 있습니다.

이로 인해서 QA 테스트 진행 시에 `Remote Config` 값을 직접 수정하거나 QA용으로 별도 분리하여 관리할 필요 없이 클라이언트에서 잠시 바꾸는 것으로도 쉽게 테스트 할 수 있다는 이점까지 누릴 수 있게 되었습니다.

### fetch 전략

다음으로는 Remote Config 를 불러오는 fetch 에 대해 설명드리도록 하겠습니다. 

[Firebase 에서 제안하는 fetch 방식](https://firebase.google.com/docs/remote-config/loading)은 3가지가 있습니다.

1. 로드 시 가져와 활성화
    - 이 전략은 앱이 처음 시작될 때 `fetchAndActivate()` 을 호출해 새 값을 가져와 로드가 완료가 되는 즉시 활성화를 합니다.
    - 앱 사용 중에 값이 바뀐다면 원치 않는 동작을 야기할 수 있으므로 주의해야 합니다.
2. 로딩 화면 뒤에서 활성화
    - 로딩 화면에서 fetch를 실행한 후 로딩이 완료되었을 때에 activateFetched로 바꾸어 주는 방식입니다.
    - 네트워크가 느린 환경에서 로딩 화면이 굉장히 길게 보일 수 있기 때문에 사용자 경험에 안좋은 영향을 줄 수 있어 주의해야 합니다.
3. 다음 시작 시 새 값 로드
    - 앱 시작 시에 기존에 저장된 값을 가져와 사용하고 fetch를 비동기로 수행합니다. 즉, 최신 값은 다음 시작 시에 적용될 수 있습니다.

이 중에서 Azar Android는 3번과 유사한 전략을 사용하고 있습니다.

앱 시작 시에 비동기로 fetch를 수행하여 이 값을 캐싱하고 값을 get할 때에 앞서 설명드린 5가지 단계 중 3번에서 사용되게 됩니다.

### 그렇다면 Default 값 관리는..?

대부분 xml 로 default 값을 정의해놓고 사용할 것으로 예상이 되는데요 !

저희팀은 조금이라도 더 효율적으로 관리를 하기 위해 구글 스프레드시트와 파이썬 스크립트를 활용하고 있습니다.

1. 구글 스프레드 시트에 필요한 Remote Config Key, default value를 입력
2. 파이썬 스크립트를 통해 해당 스프레드 시트를 읽어와서 파일로 자동 생성

### 무엇을 얻었는가?

1. 개발 모드인 경우 클라이언트에서 직접 제어가 가능하므로 QA 테스트 시에 용이하다.
2. 서버에서도 컨트롤이 가능하므로 좀 더 다양한 세그먼트를 구성, 분리 할 수 있다.
3. 스크립트를 사용하므로 Default 값을 적용, 변경할 때 운영 ↔️ 개발자 간에 직접적인 소통이 필요하지 않아 불필요한 커뮤니케이션 비용을 줄일 수 있다.
4. 스크립트를 사용하므로 개발자가 직접 값을 옮기는 과정에서 발생할 수 있는 휴먼 에러가 발생하지 않는다.

글을 읽으면서 '단순히 A/B 테스트, 세그먼트 분리 적용에서만 사용하면 되지 왜 이렇게 복잡하게 써? 🤔' 라는 생각이 들었을 수도 있을 것 같습니다.

하지만 실제로는 구조를 잘 잡아두기만 하면 오히려 Remote Config의 수정 등으로 인해 발생할 수 있는 추가적인 리소스가 필요 없어지기 때문에 오히려 추천드리고 싶은 방식이라 글로 작성하게 되었습니다.

## 글을 마치며..
저희가 하이퍼커넥트에 합류한지 어느덧 2년이 되어서 그 동안 느낀점들을 1탄, 2탄에 걸쳐서 적어보았는데요!<br>
글을 적으면서 문득 좋은 동료들과 함께 즐거운 마음으로 글로벌 서비스를 만들고 있다는 생각이 들었습니다 😄<br>
앞으로도 계속해서 좋은 동료들과 함께 하이퍼커넥트에서 많은 경험들을 겪어보면서 더욱 더 성장해 나가고 싶네요.<br>
글로 옮겨본 저희의 경험들이 도움이 되길 바라고 긴 글 읽어주셔서 감사합니다. 🙇‍
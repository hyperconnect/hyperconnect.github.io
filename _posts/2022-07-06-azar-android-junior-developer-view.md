---
layout: post
date: 2022-07-06
title: Junior 개발자의 글로벌 서비스 경험기 1탄
author: tay, mason
authors:
  - tay
  - mason
tags: android junior
excerpt: 아자르 Android팀의 주니어 개발자들의 글로벌 서비스 경험 중 '언어'와 '앱갤러리'에 대한 이야기를 소개합니다.
---

안녕하세요 👋
하이퍼커넥트 아자르 스튜디오 Android 팀의 Tay, Mason 입니다.

아자르는 **글로벌**을 대상으로 수 억명이 사용하는 동영상 채팅 앱입니다.

하이퍼커넥트에 주니어 개발자로 합류하여, 글로벌 대상 앱을 만들면서 어떤 것들을 배우고 느꼈는지와 함께 글로벌 서비스를 위해 처리해주어야할 것은 무엇인지 이야기해보고자 합니다.

## 문자열 길이에 따른 대응 작업
'글로벌 서비스' 하면 가장 먼저 떠오르는 대응해야할 부분은 어떤 것인가요?🤔 개인적으로.. 가장 먼저 떠오르는 것은 **언어**입니다.
실제로 최근에 개발을 하면서 같은 뜻을 가진 글자가 언어별로 다른 길이를 가지면서 발생했던 문제를 맞닥뜨린적이 있는데 어떤 일이 있었는지 소개하도록 하겠습니다.

### Toast 대응
아래는 아자르에서 상대방과 매치중 상대방으로 부터 친구 추가를 받은 화면입니다. 이 화면에서 어떠한 문제점이 있는지 보이시나요?

![toast_os12_kr]({{"/assets/2022-07-06-azar-android-junior-developer-view/toast_os12_kr.jpg" | absolute_url}}){: width="300px" }

맞습니다. 한국어에서는 문제가 없습니다 ! 😂

그렇다면 포루투갈어에서는 어떨까요?

![toast_os12_pt]({{"/assets/2022-07-06-azar-android-junior-developer-view/toast_os12_pt.jpg" | absolute_url}}){: width="300px" }

맞습니다. 토스트에 있는 문자열을 보시면 말줄임이 된 것을 보실 수 있습니다. (~~물론 저는 1개 국어도 제대로 못하기 때문에 포르투갈어로 말줄임이 되든 안되든 무슨 말인지는 모릅니다..!~~ 😂)

저희가 의도했던 토스트는 `enviou um pedido de amizade. Os pedidos de amizade expiram após 15 dias se não forem aceitos.`인데 [Android 12에서 토스트가 2줄 제한](https://developer.android.com/about/versions/12/behavior-changes-12#toast-redesign) 이 되면서 문구에서 중요한 **"15일"** 이라는 문자를 포함해서 굉장히 많은 문자들이 생략되어버렸습니다.

이를 해결하기 위한 방안으로 3가지가 떠올랐습니다.

1. 문자열을 최대한 줄여서 2줄 안에 보이도록 한다.
2. 에라 모르겠다. 구글이 정책을 바꾼 것이니 내 잘못 아니다. 그대로 둔다.
3. 스낵바로 노출한다.

전 세계의 사용자들이 즐겁게 사용할 수 있도록 하는 목표를 가지고 있는 Azar Android 팀에서는 어떤 방법을 선택했을까요?

바로 구글에서 권장하고 있는 **스낵바로 노출한다.** 입니다 !

> 관련한 내용은 [여기](https://developer.android.com/training/snackbar/#:~:text=Note%3A%20The%20Snackbar%20class%20supersedes%20Toast.%20While%20Toast%20is%20currently%20still%20supported%2C%20Snackbar%20is%20now%20the%20preferred%20way%20to%20display%20brief%2C%20transient%20messages%20to%20the%20user.)를 참고해주세요. :)

토스트와 스낵바는 사용성이 다르기 때문에 특정 규칙을 세우고 이를 토대로 토스트/스낵바로 분리해서 노출하도록 대응하였습니다.

> 아자르에서는 대략 아래와 같은 규칙을 기준으로 삼았습니다.<br>
> (이 규칙은 Azar Android 에서 세운 규칙이며 이는 언제든 변경될 수 있습니다.)
>
> 1. 액티비티를 닫으면서 노출하는 경우
> 2. 다른 다이얼로그/팝업이 덮고 있는 상태에서 노출하는 경우
> 3. 브로커 메시지/이벤트 버스 등 언제 노출될지 모르는 상태에서 노출하는 경우
> 4. 웹뷰 혹은 RN 화면으로 클라이언트의 제어를 벗어나는 상태에서 노출하는 경우
> 5. 반드시 떠야한다고 판단되는 경우 (ex. 네트워크 에러 상태, 로그인 실패 상태, 일부 개발 모드용 토스트 등..)
> 6. 위 사항 외에는 snackbar 사용

스낵바를 적용한 후에는 이와 같이 문자열의 길이에 상관 없이 잘 노출되는 것을 보실 수 있습니다.

|한국어 스낵바|포르투갈어 스낵바|
|---------|------------|
|![snackbar_os12_kr]({{"/assets/2022-07-06-azar-android-junior-developer-view/snackbar_os12_kr.jpg" | absolute_url}})|![snackbar_os12_kr]({{"/assets/2022-07-06-azar-android-junior-developer-view/snackbar_os12_pt.jpg" | absolute_url}})|

간단하게 언어별로 문자열 길이가 달라지면서 발생했던 Toast 노출 문제에 대해서 이야기했는데요. 다음으로는 TextView에서 발생할 수 있는 문제에 대해 이야기를 해보도록 하겠습니다.

### TextView 대응
다국어 테스트를 진행하다보면 앞서 설명드린 Toast 의 말줄임 문제와 비슷하게 TextView에서도 문자열의 길이에 따른 문제를 빈번하게 맞이하게 됩니다.

간단한 예시를 들어보겠습니다.

Tay는 디자이너에게 특정 Text에 대해 width는 100dp이고 textSize는 20dp 그리고 1줄로 보이게 해달라는 요구 사항을 받았습니다. 단, 해당 Text는 서버에서 내려주는 문자열입니다.

Tay는 디자이너가 요구한 대로 TextView를 만들었습니다. MVVM 구조에 맞춰서 data binding도 사용했습니다. 한국어로 설정해두고 테스트도 했는데 아주 잘 동작하는 것을 확인했습니다.

```xml
<androidx.appcompat.widget.AppCompatTextView
    android:layout_width="100dp"
    android:layout_height="wrap_content"
    android:maxLines="1"
    android:text="@{textFromServer}"
    android:textSize="20dp" />
```

위 TextView 에서 발생할 수 있는 문제는 무엇일까요?

- 아자르는 글로벌 서비스입니다. 서버에서 내려주는 text도 사용자의 언어에 맞는 언어로 변환하여 내려줍니다.
- 따라서, 서버로부터 받아온 `textFromServer`는 클라이언트 입장에서는 길이가 얼마가 되는 것인지 알 수 없습니다.

### 그렇다면 어떻게 해야할까요?

안드로이드는 다국어 처리를 굉장히 잘 지원해주고 있기 때문에  `AppCompatTextView` 의 `app:autoSizeMaxTextSize`, `app:autoSizeMinTextSize`, `app:autoSizeTextType`을 이용하면 간단하게 처리가 가능합니다.<br>
3개의 옵션을 지정해주면 해당 TextView의 크기가 가득 찼을 때 설정된 MaxTextSize에서 MinTextSize로 줄어들게 하면서 노출할 수 있습니다.

```xml
<androidx.appcompat.widget.AppCompatTextView
    android:layout_width="100dp"
    android:layout_height="wrap_content"
    android:maxLines="1"
    android:text="Hello World!"
    android:textSize="20dp"
    app:autoSizeMaxTextSize="20dp"
    app:autoSizeMinTextSize="10dp"
    app:autoSizeTextType="uniform" />

<androidx.appcompat.widget.AppCompatTextView
    android:layout_width="100dp"
    android:layout_height="wrap_content"
    android:maxLines="1"
    android:text="Hello Hyperconnect!"
    android:textSize="20dp"
    app:autoSizeMaxTextSize="20dp"
    app:autoSizeMinTextSize="10dp"
    app:autoSizeTextType="uniform" />
```

`autoSizeMaxTextSize`, `autoSizeMinTextSize`, `autoSizeTextType` 을 지정하고 나면 아래와 같이 문자열이 길어질 경우 textSize가 조절이 되는 것을 확인할 수 있습니다.

![text_autosize_sample]({{"/assets/2022-07-06-azar-android-junior-developer-view/text_autosize.jpg" | absolute_url}}){: width="300px" }

이러한 경험을 토대로 Azar 를 만들어가는 개발자, 디자이너, PM 등 구성원은 이와 같이 언어별로 문자열의 길이가 다르다는 것을 인지하고 간단한 텍스트를 노출할 때에도 auto sizing 처리가 필요하진 않은지, 필요하다면 어느 범위까지 축소시키며 노출할 것인지 등을 고민하고 있습니다.<br>
또한, 개발하면서 아자르가 지원하는 23개 모든 언어를 다 테스트할 필요까지는 없다고 하더라도, 가장 긴 러시아어와 RTL이 적용되는 아랍어로 바꿔서 보는 것이 팁이라면 팁이기도 합니다.


## 문자열 번역

국가별 string 대응은 글로벌 서비스의 기본 요건입니다. 아자르는 현재 23개 언어에 대해 번역을 지원하고 있는데요. 안드로이드 스튜디오에서 아래와 같이 국가별 리소스 디렉토리를 생성해서 대응이 가능합니다.

|---------|---------|
|![add_string_android]({{"/assets/2022-07-06-azar-android-junior-developer-view/add_string_android.png" | absolute_url}}){: width="500px" }|![add_string_result_android]({{"/assets/2022-07-06-azar-android-junior-developer-view/add_string_result_android.png" | absolute_url}}){: width="650px" }|

### 번역 프로세스

그렇다면 23개 언어에 대한 번역은 어떤 방식으로 진행해야 할까요?

1. text 번역 요청.
2. 국가별로 번역된 text 전달.
3. 개발자가 국가별 strings.xml에 하나씩 복붙.

🤦‍♂️

피처마다 국가별 strings.xml을 손수 업데이트 한다는 것은.. 실수할 여지도 많고 상당히 귀찮은 작업입니다.

아자르에서는 이를 간단히 관리하기 위해 crowdin이라는 툴과 파이썬 스크립트를 사용하여 다음의 프로세스로 처리하고 있습니다.

1. text 번역 요청.
2. crowdin에 번역된 text 등록.
3. crowdin에 등록된 text를 파이썬 스크립트를 이용해 다운로드 및 국가별 strings.xml 파일 생성 자동화.

아자르 Android팀은 아래와 같은 yaml 파일을 이용해 crowdin에 번역된 문자열을 읽어와, 국가별로 strings.xml을 생성하도록 해주고 있습니다.(자세한 가이드는 [여기](https://support.crowdin.com/cli-tool/)서 확인할 수 있습니다.)

```python
crowdin.yaml

files:
  -
    source: '/res/values/strings.xml'
    translation: '/res/%android_code%/strings.xml'
    languages_mapping:
      android_code:
        'ar': 'values-ar'
        'de': 'values-de'
        'en-US': 'values'
		...
```

툴과 스크립트로 23개 언어에 대한 string 대응이 간단해졌습니다. 대응해야 할 국가가 추가되는 경우 단순히 crowdin.yaml에 국가 코드만 추가해주면 됩니다!

다국어 처리를 고민하고 계신다면, crowdin과 파이썬 스크립트의 조합을 추천드립니다.

> crowdin은 plan 별로 번역 자동화, api 다양화 등 여러 기능을 제공합니다.<br>
> 다만 언제나 그렇듯 plan 별로 과금 형태가 다르다는 점에 주의하세요!
>
> plan 별 스펙은 [여기!](https://crowdin.com/pricing#crowdin-pricing-key-features) 를 참고해 주세요.

## 앱갤러리 오픈

### 앱갤러리란?
[앱갤러리](https://appgallery.huawei.com)는 매출액 세계 3위의 화웨이사가 만든 독자 앱 스토어입니다. (1위 구글 플레이스토어, 2위 애플 앱스토어)

### 무시할 수 없는 8%
아자르의 주요 마켓 쉐어 8% 를 차지하고 있는 화웨이 디바이스에는 대부분 플레이 스토어가 설치 되어 있지 않습니다.<br>
그래서 비공식 루트로 아자르 APK를 다운로드해 사용하는 비율이 높습니다.<br>
플레이스토어가 설치 되어 있지 않기 때문에 결제가 불가능하고 푸시 메시지를 받을 수 없어 마케팅에도 제약이 있습니다.

### MVP 버전(Minimum Viable Product, 최소 기능 제품)
최소한의 리소스 투입으로 플레이스토어 버전에서 MVP 버전을 만들기로 했고 앱갤러리 오픈시 필요한 필수 구현 목록을 작성했습니다.
- 가장 중요한 PG결제
- SNS 로그인
- 앱갤러리 Core SDK 연동
- HCM Push 연동
- Installreferrer 연동
- AppsFlyer 연동 (마케팅 효율화를 위한 설치 트래킹을 위해 개발)

### 뭔가 이상하다?
화웨이의 Installreferrer 를 연동하면서 뭔가 이상함을 느꼈습니다.
```java
import com.huawei.hms.ads.installreferrer.api.ReferrerDetails;
import com.huawei.hms.ads.installreferrer.api.InstallReferrerClient;
import com.huawei.hms.ads.installreferrer.api.InstallReferrerStateListener;
...
@Keep
public abstract class InstallReferrerClient {
    public InstallReferrerClient() {}

    public static InstallReferrerClient.Builder newBuilder(Context var0) {
        return new InstallReferrerClient.Builder(var0);
    }

    public abstract boolean isReady();
    public abstract void startConnection(InstallReferrerStateListener var1);
    public abstract void endConnection();
    public abstract ReferrerDetails getInstallReferrer() throws RemoteException, IOExeption;
...
@Retention(RetentionPolicy.SOURCE)
@Keep
public @interface InstallReferrerResponse {
    int SERVICE_DISCONNECTED = -1;
    int OK = 0;
    int SERVICE_UNAVAILABLE = 1;
    int FEATURE_NOT_SUPPORTED = 2;
    int DEVELOPER_ERROR = 3;
}
```
```java
import com.android.installreferrer.api.ReferrerDetails;
import com.android.installreferrer.api.InstallReferrerClient;
import com.android.installreferrer.api.InstallReferrerStateListener;
...
public abstract class InstallReferrerClient {
    public InstallReferrerClient() {}

    public static InstallReferrerClient.Builder newBuilder(Context var0) {
        InstallReferrerClient.Builder var1 = new InstallReferrerClient.Builder(var0);
        return var1;
    }

    public abstract boolean isReady();
    public abstract void startConnection(InstallReferrerStateListener var1);
    public abstract void endConnection();
    public abstract ReferrerDetails getInstallReferrer() throws RemoteException;
...
@Retention(RetentionPolicy.SOURCE)
public @interface InstallReferrerResponse {
    int SERVICE_DISCONNECTED = -1;
    int OK = 0;
    int SERVICE_UNAVAILABLE = 1;
    int FEATURE_NOT_SUPPORTED = 2;
    int DEVELOPER_ERROR = 3;
    int PERMISSION_ERROR = 4;
}
```
???<br>
복붙 아닙니다. (이상함을 느끼셨나요?)<br>
~~Package, Class, Enum, parameters까지 똑같..~~<br>
이미 같은 코드(?)로 한번 해봤던 터라 쉽게 연동할 수 있었습니다.<br>
또, [HMS Toolkit](https://developer.huawei.com/consumer/en/huawei-toolkit/) 이라는 plug-in을 제공하고 있어 Core SDK, HCM Push 등 편하게 연동하고 테스트할 수 있었습니다. (화웨이 감사합니다. 🙏🏿)

### 드디어 오픈!
1달이라는 시간 동안 최소한의 리소스 투자를 목표로 했지만 개발하다 보니 생각한 것 보다 준비해야 할 것들이 많았습니다.<br>
앱갤러리 콘솔 설정, 구글-페이스북 로그인 이슈, SNS 공유하기 이슈 등등..<br>
이런저런 우여곡절들이 많았지만, 2022년 4월 1일! 앱갤러리 6개국에 Azar Android를 오픈했습니다.

오픈한지 한 달이 조금 더 지났고 사용자들의 반응이 꾸준히 이어지고 있습니다. 이제 본격적으로 마케팅을 진행하면 사용자들이 더 빠르게 늘어날 것입니다.

## 글을 마치며..
글로벌 서비스에서 가장 가시적으로 느낄 수 있는 '언어' 와 어쩌면 조금은 생소할 수 있는 '앱갤러리' 에 대해서 이야기 해보았는데요 !<br>
국내에서만 서비스 하는 앱이였다면 고민해보지 못했을 부분들에 자극을 주었던 경험들이라 굉장히 값지고 흥미로웠던 것 같습니다.<br>

1탄에 이어서 2탄에서는 네트워크가 느린 국가를 위한 대응 경험기와 이미지 최적화, 그리고 다양한 문화권에 속한 사용자들을 위해 다양한 형태로 기능을 제공하는 것에 대한 이야기를 가볍게(!) 다루어 보도록 하겠습니다. 🥳

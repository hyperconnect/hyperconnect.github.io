---
layout: post
date: 2020-07-28
title: Dagger Hilt로 안드로이드 의존성 주입 시작하기
author: dove
tags: android dagger hilt di
excerpt: Dagger Hilt에 대해 알아보고 안드로이드 프로젝트에 적용하는 방법을 소개합니다.
last_modified_at: 2020-07-28
---

<img alt="hakuna logo" align="right" width="12%" src="/assets/2020-07-14-android-dagger-hilt/hakuna.png" />
안녕하세요,<br>
하이퍼커넥트 하쿠나 팀에서 하쿠나 라이브(Hakuna Live)를 개발하고 있는 Dove입니다!<br>
이번 포스팅에서는 안드로이드 프로젝트에서 Dagger-Hilt를 사용하여 DI 환경을 구축하는 방법을 소개하고자 합니다.<br>

### Dependency Injection in Andorid

의존성 주입(Dependency Injection)은 최근 Android 개발 환경에 있어서 가장 주목받고 있는 디자인 패턴 중 하나입니다. 각종 컴포넌트 간 의존성이 상당히 강한 Android Framework에서 클래스 간 의존도를 낮춘다는 것은, 단순히 인스턴스의 생성을 클래스 외부로 위임하는 것 이상의 효과와 의미를 부여하기 때문입니다.

인스턴스를 클래스 외부에서 주입하기 위해서는 인스턴스에 대한 전반적인 생명주기(생성부터 소멸되기까지)의 관리가 필요합니다.<br>
프로젝트의 규모가 커질수록 의존성 인스턴스들을 manual 하게 관리하는 것은 생각보다 많은 리소스가 요구되는데, 이를 전반적으로 관리해주는 것이 대표적으로 Google에서 밀어주고 있는 오픈소스 라이브러리 Dagger2 입니다. Dagger2는 자체적으로 Android와 크게 상관관계가 없지만 Android 환경에서 많은 인기를 끌었고, 이를 인지한 Google은 Android 환경에서 사용할 경우 자연스럽게 늘어나는 보일러 플레이트를 줄여주는 Dagger-Android도 함께 지원해주고 있습니다.

그러나 Dagger와 Dagger-Android는 annotation processing, 각 annotation에 대한 역할, module & component 간의 관계, scope 개념 등 라이브러리에 대한 많은 이해를 필요로 하므로 처음 접하시는 분들에게는 러닝 커브가 높은 편이고, 프로젝트 상황에 따라 초기 DI 환경을 구축하는데 요구되는 비용이 오히려 manual 한 DI 환경을 구축하는 데 드는 비용보다 훨씬 커질 수도 있습니다. 이러한 여러 가지 모종의 이유로 Kotlin의 언어적 특성을 활용하여 상대적으로 학습하기 쉽고, 사용이 용이한 오픈소스 라이브러리 Koin 또한 많은 인기를 얻고 있습니다.

Koin은 사용이 간결하지만 엄밀하게 의존성 주입(Dependency Injection) 개념보다는 Kotlin의 DSL을 활용한 Service Locator Pattern에 가깝고, 결과적으로 프로젝트의 규모가 커질수록 사전(컴파일 타임)에 많은 일을 처리하는 Dagger보다는 런타임 퍼포먼스가 떨어질 수 있습니다. 그래서 많은 안드로이드 개발자분들이 Dagger와 Koin을 비교한 피드백을 끊임없이 제시해왔는데, 기존 Dagger 사용자들의 의견을 수렴한 Google은 기존의 Dagger-Android 보다 초기 구축 비용을 훨씬 절감시킬 수 있고 Android Framework에서 더 강력함을 발휘 할 수 있는 Dagger Hilt를 발표하였습니다. :tada:

### New weapon: 🗡 Dagger Hilt

Hilt를 프로젝트에 적용하기에 앞서 간략하게 무엇인지, 어떠한 장점이 있는지 알아보고자 합니다.<br>
Dagger Hilt는 2020년 6월 Google에서 오피셜하게 발표한 Android 전용 DI 라이브러리입니다. Hilt는 Dagger2를 기반으로 Android Framework에서 표준적으로 사용되는 DI component와 scope를 기본적으로 제공하여, 초기 DI 환경 구축 비용을 크게 절감시키는 것이 가장 큰 목적입니다. 따라서 기존에 불가피하게 작성해야 했던 보일러 플레이트를 대량 줄이고 프로젝트의 전반적인 readability를 향상함으로써, 유지보수 면에서도 큰 이득을 취할 수 있습니다. 그뿐만 아니라, Google에서 전격적으로 지원하는 Jetpack의 ViewModel에 대한 의존성 주입도 별도의 큰 비용 없이 구현할 수 있습니다. 아직은 alpha 초기 버전이라 real project에서 사용됨에 따라 다양한 이슈들이 발견되고 있지만, 앞으로의 발전이 기대되는 DI 라이브러리입니다.

<img alt="gradle logo" align="right" width="120" src="/assets/2020-07-14-android-dagger-hilt/gradle.png" />

### Gradle Setup

Hilt를 프로젝트에 적용하기 위해서는 아래의 셋업 과정이 필수적으로 요구됩니다.<br>
먼저, 아래의 코드를 project-level의 `build.gradle` 파일에 추가합니다.

```groovy
classpath 'com.google.dagger:hilt-android-gradle-plugin:2.28-alpha'
```

다음으로, app-level의  `build.gradle` 파일 상단에 아래의 plugin을 추가합니다.

```groovy
apply plugin: 'kotlin-kapt'
apply plugin: 'dagger.hilt.android.plugin'
```

마지막으로, app-level의 `build.gradle` 파일 하단에 아래의 의존성을 추가합니다.

```groovy
implementation "com.google.dagger:hilt-android:2.28.1-alpha"
kapt "com.google.dagger:hilt-android-compiler:2.28.1-alpha"
```

이렇게 기본적인 그레이들 셋업을 마쳤습니다! <br>
다음은 Hilt를 안드로이드 프로젝트에서 본격적으로 활용하는 방법을 예시와 함께 알아보도록 하겠습니다.

### Hilt Application

Dagger Hilt에서는 `@HiltAndroidApp` 어노테이션을 사용하여 컴파일 타임 시 표준 컴포넌트 빌딩에 필요한 클래스들을 초기화합니다. 따라서 Hilt 셋업을 위해서 필수적으로 요구되는 과정입니다. 아래는 `Application` class를 상속받고 있는 `HakunaApplication` 이라는 클래스에 `@HiltAndroidApp` 를 추가한 예시입니다.

```kotlin
@HiltAndroidApp
class HakunaApplication : Application()
```

### Component hierachy

기존의 Dagger2는 개발자가 직접 필요한 component들을 작성하고 상속 관계를 정의했다면, Hilt에서는 Android 환경에서 표준적으로 사용되는 component들을 기본적으로 제공하고 있습니다. 또한 Hilt 내부적으로 제공하는 component들의 전반적인 라이프 사이클 또한 자동으로 관리해주기 때문에 사용자가 초기 DI 환경을 구축하는데 드는 비용을 최소화하고 있습니다. 다음은 Hilt에서 제공하는 표준 component hierarchy 입니다.

<img width="1400" alt="hilt components" src="/assets/2020-07-14-android-dagger-hilt/hilt-component.png" />

Hilt에서 표준적으로 제공하는 Component, 관련 Scope, 생성 및 파괴 시점은 아래와 같습니다.

|         Compoent          |          Scope          |       Created at       |      Destroyed at       |
| :-----------------------: | :---------------------: | :--------------------: | :---------------------: |
|   ApplicationComponent    |       @Singleton        | Application#onCreate() | Application#onDestroy() |
| ActivityRetainedComponent | @ActivityRetainedScoped |  Activity#onCreate()   |  Activity#onDestroy()   |
|     ActivityComponent     |     @ActivityScoped     |  Activity#onCreate()   |  Activity#onDestroy()   |
|     FragmentComponent     |     @FragmentScoped     |  Fragment#onAttach()   |  Fragment#onDestroy()   |
|       ViewComponent       |       @ViewScoped       |      View#super()      |     View destroyed      |
| ViewWithFragmentComponent |       @ViewScoped       |      View#super()      |     View destroyed      |
|     ServiceComponent      |     @ServiceScoped      |   Service#onCreate()   |   Service#onDestroy()   |

각 component 들은 생성 시점부터 파괴되기 이전까지 member injection이 가능합니다. 각 컴포넌트의 자신만의 lifetime을 갖습니다.

- ApplicationComponent - Application 전체의 생명주기를 lifetime으로 갖습니다. Application이 생성되는(onCreate) 시점에 함께 생성되고, Application이 파괴되는(onDestroy) 시점에 함께 파괴됩니다.
- ActivityRetainedComponent - `ApplicationComponent`의 하위 컴포넌트로써, Activity의 생명주기를 lifetime으로 갖습니다. 다만, Activity의 configuration change(디바이스 화면전환 등) 시에는 파괴되지 않고 유지됩니다.
- ActivityComponent - `ActivityRetainedComponen`의 하위 컴포넌트로써, Activity의 생명주기를 lifetime으로 갖습니다. Activity가 생성되는(onCreate) 시점에 함께 생성되고, Activity가 파괴되는(onDestroy) 시점에 함께 파괴됩니다.
- FragmentComponent - `ActivityComponent`의 하위 컴포넌트로써, Fragment의 생명주기를 lifetime으로 갖습니다. Fragment가 Activity에 붙는순간(onAttach) 시점에 함께 함께 생성되고, Fragment가 파괴되는(onDestroy) 시점에 함께 파괴됩니다.
- ViewComponent - `ActivityComponent`의 하위 컴포넌트로써, View의 생명주기를 lifetime으로 갖습니다. View가 생성되는 시점에 함께 생성되고, 파괴되는 시점에 함께 파괴됩니다.
- ViewWithFragmentComponent - `FragmentComponent`의 하위 컴포넌트로써, Fragment의 view 생명주기를 lifetime으로 갖습니다. View가 생성되는 시점에 함께 생성되고, 파괴되는 시점에 함께 파괴됩니다.
- ServiceComponent - `ApplicationComponent`의 하위 컴포넌트로써, Service의 생명주기를 lifetime으로 갖습니다. Service가 생성되는(onCreate) 시점에 함께 생성되고, Service가 파괴되는(onDestroy) 시점에 함께 파괴됩니다.

위와 같은 표준 component/scope들을 Hilt에서는 제공하고 있으며, 새로운 component를 정의하고 싶다면 `@DefineComponent` 어노테이션을 사용하여 사용자 정의가 가능합니다. 아래는 `LoggedUserScope`라는 사용자 scope를 정의하고, 해당 scope를 사용하여 `UserComponent`라는 새로운 component를 만든 예시입니다.

```kotlin
@Scope
@MustBeDocumented
@Retention(value = AnnotationRetention.RUNTIME)
annotation class LoggedUserScope

@LoggedUserScope
@DefineComponent(parent = ApplicationComponent::class)
interface UserComponent {

    // Builder to create instances of UserComponent
    @DefineComponent.Builder
    interface Builder {
        fun setUser(@BindsInstance user: User): UserComponent.Builder
        fun build(): UserComponent
    }
}
```

`@DefineComponent` 어노테이션에서 예상할 수 있듯이, 사용자 정의되는 component들은 반드시 표준 컴포넌트 중 하나를 부모 컴포넌트로써 상속받아야 합니다. 

![hilt custom component]({{"/assets/2020-07-14-android-dagger-hilt/hilt-custom-component.png"}})

사용자 component는 반드시 leaf component로써 표준 component에 추가될 수 있으며, 2개의 layer에 침범하는 형태의 사용자 정의는 불가능합니다. (ApplicationComponent의 subcomponent이면서 동시에 ActivityRetainedComponent의 parent component인 형태는 불가능)

### Hilt Modules

기존의 Dagger2에서는 새로운 module을 생성하면, 사용자가 정의한 component에 해당 module 클래스를 직접 include 해주는 방법이었습니다.
반면, Hilt는 표준적으로 제공하는 component 들이 이미 존재하기 때문에 `@InstallIn` 어노테이션을 사용하여 표준 component에 module들을  install 할 수 있습니다. Hilt에서 제공하는 기본적인 규칙은 모든 module에 `@InstallIn` 어노테이션을 사용하여 어떤 component에 install 할지 반드시 정해주어야 합니다. 아래 예시는 `FooModule` 이라는 module을 `ApplicationComponent`에 install하고, `ApplicationComponent`에서 제공해주는 `Application` class를 내부적으로 활용하고 있습니다.

```kotlin
@Module
@InstallIn(ApplicationComponent::class)
object class FooModule {
  // @InstallIn(ApplicationComponent.class) module providers have access to
  // the Application binding.
  @Provides
  fun provideBar(app: Application): Bar {...}
}
```

만약 하나의 module을 다중의 component에 install 하고 싶다면 아래와 같이 여러 개의 component를 install 할 수 있습니다.

```kotlin
@InstallIn({ViewComponent.class, ViewWithFragmentComponent.class})
```

이처럼 다중 component에 하나의 module을 install 하는 데는 세 가지 규칙이 있습니다.

- Provider는 다중 component가 모두 동일한 scope에 속해있을 경우에만 scope를 지정할 수 있습니다. 위의 예시와 같이 `ViewComponent`와 `ViewWithFragmentComponent`는  동일한 `ViewScoped`에 속해있기 때문에, provider에게 동일한 `ViewScoped`를 지정할 수 있습니다.
- Provider는 다중 component가 서로 간 요소에게 접근이 가능한 경우에만 주입이 가능합니다. 가령 `ViewComponent`와 `ViewWithFragmentComponent`는 서로 간의 요소에 접근이 가능하기 때문에 View에게 주입이 가능하지만,  `FragmentComponent` 와 `ServiceComponent` 는 `Fragment` 또는 `Service`에게 주입이 불가능합니다.
- 부모 component와 자식 compoent에 동시에 install 될 수 없으며, 자식 component는 부모 component의 module에 대한 접근 할 수 있습니다.

### AndroidEntryPoint

기존의 Dagger2에서는 직접 의존성을 주입해줄 대상을 전부 dependency graph에 지정해주었다면, Hilt에서는 객체를 주입할 대상에게 `@AndroidEntryPoint` 어노테이션을 추가하는 것만으로도 member injection을 수행할 수 있습니다. `@AndroidEntryPoint`을 추가할 수 있는 Android component는 아래와 같습니다.

- Activity
- Fragment
- View
- Service
- BroadcastReceiver

아래는 MainActivity에 `Bar` 객체를 주입하는 간단한 예시입니다.

```kotlin
@AndroidEntryPoint
class MyActivity : MyBaseActivity() {
  // Bindings in ApplicationComponent or ActivityComponent
  @Inject lateinit var bar: Bar

  override fun onCreate(savedInstanceState: Bundle?) {
    // Injection happens in super.onCreate().
    super.onCreate()

    // Do something with bar ...
  }
}
```

### EntryPoint

Hilt의 또 다른 장점은 Dagger에 의해 관리되는 의존성 객체를 injection이 아닌 `EntryPoint`를 통해서 얻을 수 있습니다. Module과 유사하게 `InstallIn` 어노테이션을 사용하여 install 하려는 component를 지정하고, `@EntryPoint` 어노테이션을 추가합니다. 아래의 예시는 `Retrofit` 객체 획득을 위한 EntryPoint interface 작성 예시입니다.

```kotlin
@EntryPoint
@InstallIn(ApplicationComponent::class)
interface RetrofitInterface {

    fun getRetrofit(): Retrofit
}
```

아래는 `MainActivity`에서 `Retrofit` 객체를 injection이 아닌 `EntryPoint`를 통해 얻어오는 예시입니다.

```kotlin
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)

    val retrofit = EntryPoints.get(applicationContext, RetrofitInterface::class.java).getRetrofit()
    
    // ... //
}
```

Hilt에서 제시하는 EntryPoint에 대한 개념은 Dagger를 활용한 의존성 주입이 어려운 경우에 대한 대안으로 보입니다. 가령 DI가 사용되고 있지 않은 상황에서 DI 환경을 구축할 때 객체 간 의존성이 서로 얽히고설켜 있다면, 많은 양의 객체를 리팩토링해야만 DI를 올바르게 사용할 수 있을 것입니다. 하지만 EntryPoint를 사용한다면, 당장에 DI 적용이 불가능한 객체에 대하여 EntryPoint를 활용하여 의존성 객체를 획득하게 해놓고, 후일에 조금씩 마이그레이션 하는 전략도 고려해볼 수 있을 것입니다.

### Jetpack ViewModel

Hilt는 기본적으로 Jetpack에서 제공하는 ViewModel에 대한 의존성 주입을 제공하기 때문에, Jetpack의 ViewModel을 사용하시는 분들께는 좋은 소식입니다. ViewModel Injection을 위해서 app-level의 `build.gradle` 파일 하단에 아래의 의존성을 추가합니다.

```groovy
implementation "androidx.hilt:hilt-common:1.0.0-alpha01"
implementation "androidx.hilt:hilt-lifecycle-viewmodel:1.0.0-alpha01"
kapt "androidx.hilt:hilt-compiler:1.0.0-alpha01"
```

다음은 Hilt에서 ViewModel Injection이 어떻게 이루어지는지 살펴보도록 하겠습니다.

### ViewModel Injection

Jetpack에서 소개된 ViewModel은 Android SDK 내부적으로 ViewModel에 대한 lifecycle을 관리하고 있습니다. 따라서 ViewModel의 생성 또한 Jetpack에서 제공하는 `ViewModelFactory` 를 통해서 이루어져야 합니다. 기존에는 각자 ViewModel 환경에 맞는 `ViewModelFactory`를 따로 작성하였거나, Dagger-Android 유저들은 ViewModel의 constructor injection을 위해 글로벌한 `ViewModelFactory`를 작성하여 사용하였습니다. Hilt에서는 이러한 보일러 플레이트를 줄이기 위한 `ViewModelFactory`가 이미 내부에 정의되어있고, `ActivityComponent`와 `FragmentComponent`에 자동으로 install 됩니다. 아래의 `@ViewModelInject` 어노테이션을 사용하여 constructor injection을 수행한 예시입니다.

```kotlin
class HakunaViewModel @ViewModelInject constructor(
  private val bar: Bar
) : ViewModel() {
  // ... //
}
```

다음은 생성된 `HakunaViewModel`을 MainActivity에서 사용하는 예시입니다.

```kotlin
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
  
  private val viewModel by viewModels<HakunaViewModel>()

  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    // ... //
}
```

ViewModel에서 `SavedStateHandle`를 주입받으려면 아래와 같이 `@Assisted` 어노테이션이 사용됩니다.

```kotlin
class HakunaViewModel @ViewModelInject constructor(
  private val bar: Bar,
  @Assisted private val savedStateHandle: SavedStateHandle
) : ViewModel() {
  // ... //
}
```

ViewModel Injection 과정에서도 알 수 있듯이, Hilt가 DI 환경을 구축하는 데 드는 비용을 줄이기 위해 노력했다는 것이 느껴집니다.

### Conclusion

이번 포스팅에서는 Dagger-Hilt를 사용하여 의존성을 관리 및 주입하는 방법에 대하여 간단하게 알아보았습니다. Hilt라는 이름에 걸맞게 더 강력하고 깔끔한 DI 환경을 제공하고 있습니다. 또한 초기 셋업 비용을 최대한 절감시키고 진입장벽을 낮추고자 Google 엔지니어분들께서 많은 노력을 하셨다는 것이 느껴집니다. 아직은 alpha 버전이라 향후 어떻게 변화할지는 모르지만, 기존의 Jetpack과의 호환성 지원 등 앞으로의 발전이 점점 기대됩니다. DI 도입에 대하여 고민하고 계신 분들이나 Hilt에 관심을 두고 계신 분들께 도움이 되기를 바라며 글을 마무리하겠습니다!

### References

- [Exploring Dagger-Hilt and what’s main differences from Dagger-Android](https://proandroiddev.com/exploring-dagger-hilt-and-whats-main-differences-with-dagger-android-c8c54cd92f18)
- [Dependency injection with Hilt](https://developer.android.com/training/dependency-injection/hilt-android)
- [Hilt — Adding components to the hierarchy](https://medium.com/androiddevelopers/hilt-adding-components-to-the-hierarchy-96f207d6d92d)

---
layout: post
date: 2025-06-12
title: 1:1 비디오 채팅 서비스는 E2E 회귀 테스트를 어떻게 자동화할까?
authors:
  - nick.y
  - liam.o
tags: testing qa testautomation
excerpt: 1:1 비디오 채팅이 핵심기능인 아자르에서 End to End 회귀 테스트를 자동화하기 위해 고민했던 내용들을 소개합니다.
last_modified_at: 2025-06-12
---

안녕하세요? 하이퍼커넥트에서 Software Development Engineer in Test 팀(이하 SDET팀) 에서 근무중인 Nick.Y, Liam.O 입니다.

많은 서비스에서는 매 버전 업데이트를 할 때마다 기존 기능에 문제가 없는지 반복적으로 검사해야 합니다. 이것을 회귀 테스트(_Regression Test_) 라고 하는데요, 아자르도 예외 없이 버전마다 QA 팀에서 수행 중입니다.

저희 SDET팀에서는 반복적으로 수행되는 회귀 테스트 케이스에 대해 Pytest와 Appium을 이용하여 자동화하는 작업을 하고 있는데요, 다른 서비스에서는 경험하기 어려운 아자르의 특별한 기능을 테스트하기 위해 많이 고민했습니다.

이번 포스트에서는 테스트를 자동화할 때 겪은 어려움과 그 해결 방법, 그리고 자동화를 통해 얻는 이점 등을 소개하고자 합니다.

---

## 아자르의 자동 회귀 테스트 구성

![videochat]({{ "/assets/2025-06-12-how-to-automate-e2e-test-on-1on1-video-chat-app/1.png" | absolute_url }}){: width="550px" .center-image }

**1:1 비디오 채팅** 이라는 아자르의 특별한 기능은 테스트 자동화 초기 단계에서 가장 큰 허들이었습니다. 팀 내부에서 열심히 토론한 결과, 일반적인 형태의 테스트 자동화로는 구현이 어렵다는 결론에 이르러, 테스트 구성을 크게 **Non-interaction** 과 **Interaction** 이라는 2개의 형태로 나누기로 했습니다.

![automated_test]({{ "/assets/2025-06-12-how-to-automate-e2e-test-on-1on1-video-chat-app/2.png" | absolute_url }}){: width="550px" .center-image }

이 구조는 실행하고자 하는 테스트가 다른 유저와의 상호작용(interaction)이 없는지, 또는 비디오 콜, 메시지, 매칭 등 다른 유저와의 상호작용을 수행해야 하는 테스트인지에 따라 구분했습니다. 이는 다시 하나의 코드 베이스에서 `driver` 생성 전략을 구분하게 되었습니다.

**Non-interaction** 테스트의 경우 일반적인 UI 자동 테스트와 동일합니다. 물론 Non-interaction 테스트에서도 소개해 드릴 만한 부분이 정말 많지만, 이번 포스트에서는 **Interaction** 테스트를 소개해 드리고자 합니다.

## 그러면 1:1 Interaction을 어떻게 자동화할 수 있을까?

그러면 다른 유저와의 1:1 인터랙션을 어떻게 자동화할 수 있을까요? 바로 하나의 테스트에서 2개의 `driver`를 생성해서 조작하면 됩니다.

![automated_test]({{ "/assets/2025-06-12-how-to-automate-e2e-test-on-1on1-video-chat-app/3.jpg" | absolute_url }}){: width="330px" .center-image }

그러나 `driver` 를 2개 생성해서 테스트를 **제대로** 수행한다는 것은 그리 간단한 문제는 아니었습니다.

---

## Interaction 테스트를 자동화하면서 했던 고민들

### 실행 단말기 구성

1:1 인터랙션을 한다고 해도 단순히 Android 단말기끼리, iOS 단말기끼리 인터랙션을 수행할 수는 없었습니다. iOS에서 Android로 비디오 채팅을 실행했을 때, 테스트 케이스의 확인 관점에 따라 그 반대의 경우 등 크로스 플랫폼의 경우를 확인해야 했습니다. 따라서 기본적으로는 아래 4가지 조건으로 테스트를 실행할 수 있어야 했습니다.

|주로 테스트하는 플랫폼|테스트를 도와주는 상대 플랫폼|
|---|---|
|Android|Android|
|Android|iOS|
|iOS|Android|
|iOS|iOS|

다만 때에 따라 특정 플랫폼에서 지원하지 않는 기능이 있거나, 테스트 케이스를 분석했을 때 테스트 시간을 단축하고자 굳이 크로스 플랫폼까지 확인할 필요가 없는 때도 있어 조합을 선택적으로 실행할 수도 있어야 했습니다. 또한 위 조건에 더하여, 하나의 테스트에 대해 모든 실행 가능한 조합별 병렬 실행할 수 있어야 했습니다.

이러한 조건으로 인해 하나의 테스트 케이스에서 여러 플랫폼의 `driver`를 생성하는 것은 단일 플랫폼만 생성해서 단말기를 조작할 때와는 다른 접근이 필요했습니다. 

### 원하는 테스트 상대와의 매칭

아자르의 1:1 비디오 채팅은 기본적으로 무작위(랜덤) 상대를 만나게 되어 있습니다. 그러나 이로 인해 인터랙션 테스트 케이스들의 병렬 실행 시도 시, 시나리오상 만나야 하는 상대와 만날 수 없는 문제가 발생했습니다.

예를 들어 A 테스트와 B 테스트가 동시에 실행될 때, A 테스트에서는 a 유저와 b 유저가, B 테스트에서는 c 유저와 d 유저가 매칭되어야 합니다. 그러나 병렬 실행 시 A 테스트의 a가 B 테스트의 c와 매칭되거나, b 유저가 d 유저와 매칭되는 등 의도치 않은 매칭이 발생할 수 있습니다. 또한 테스트 실행 중 매칭 기능을 이용해 테스트하고자 하는 사내 다른 하이퍼 커넥터들의 테스트 계정과도 매칭될 가능성이 있었습니다.

![as-is-matching_pool]({{ "/assets/2025-06-12-how-to-automate-e2e-test-on-1on1-video-chat-app/4.png" | absolute_url }}){: width="550px" .center-image }

이 문제로 인해 테스트 자동화 초기에는 interaction 테스트의 병렬 실행이 불가능했고, 전체 테스트 실행에 10시간 이상이 소요되었습니다.

### 각각의 테스트 당 테스트 실행 시간 고려

대부분의 테스트는 기본적으로 A의 액션에 대한 UI/데이터 변화를 B에서 확인합니다. 즉, 테스트 시나리오상 상대 유저의 액션에 서로 의존적인 경우가 있습니다. 그러나 그렇다고 모든 테스트 스텝을 순차적으로만 작성하면 상대 액션에 의존하지 않아도 될 부분까지 기다리게 되어, 결국 각 테스트 케이스당 테스트 실행 시간이 늘어나게 됩니다.

![as-is-execution_time]({{ "/assets/2025-06-12-how-to-automate-e2e-test-on-1on1-video-chat-app/6.png" | absolute_url }}){: width="770px" .center-image }

따라서 테스트 스텝 내에서도 상대 액션에 의존하지 않아도 되는 스텝은 동시에 실행 가능해야 했습니다.

### 다른 플랫폼, 동일한 테스트 코드

테스트 케이스를 작성하다 보면 같은 기능이지만 플랫폼별 특성으로 인해 기능의 동작 방식이 다른 경우가 종종 있습니다. 게다가 아자르는 약 10년 넘게 서비스 중이다 보니 기능 중에는 개발 시기에 따라서도 종종 플랫폼별로 UI가 조금씩 다른 경우가 있었습니다.

이때, 하나의 테스트 코드에 대해 여러 플랫폼에서 동일하게 실행할 수 있으면서도 테스트 코드를 어떻게 간결하고 유지보수성 높게 작성해야 할지도 고민해야 했습니다.

---

## 해결 방법들

### `pytest` hook과 command line 명령어를 통해 parameter를 그룹화
병렬 실행 자체는 `pytest-xdist` 플러그인을 이용하면 간단하게 할 수 있지만, 플랫폼 조합별 `driver` 생성, 특정 조합에서의 테스트 실행 생략과 같은 처리를 하기 위해서는 일반적인 parameterization로는 어려웠습니다.

여기서 저희는 `pytest`의 `pytest_addoption` hook을 이용해 테스트를 실행해야 할 플랫폼 조합별로 그룹을 지정하는 사용자 정의 커맨드라인 명령어를 추가로 정의한 후, `pytest_generate_tests` hook에서 특정 그룹이 입력되면 해당 그룹의 플랫폼 조합으로 파라미터를 생성하도록 했습니다.

```python
def pytest_generate_tests(metafunc):
    selected_params = []

    if "platforms" in metafunc.fixturenames:
        # 실행해야할 테스트들 혹은 fixture들에서 "platforms" fixture를 호출하려고 할 때.
        # 이 hook 내부에서 platforms 파라미터가 정의됩니다.
        params = [
            ("android", "android"),
            ("android", "ios"),
            ("ios", "android"),
            ("ios", "ios"),
        ]

        # 커맨드라인 옵션에서 파라미터 그룹을 가져옵니다.
        param_group = metafunc.config.getoption("param_group")

        if param_group:
            match param_group:
                # group1 = ("android", "android")
                case "group1":
                    selected_params = [params[0]]
                # group2 = ("android", "ios")
                case "group2":
                    selected_params = [params[1]]
                # group3 = ("ios", "android")
                case "group3":
                    selected_params = [params[2]]
                # group4 = ("ios", "ios")
                case "group4":
                    selected_params = [params[3]]
                case _:
                    # param_group이 입력되지않는다면 모든 파라미터 사용
                    selected_params = params
        .
        .
        .


```

여기서 생성되는 조합 값을 통해 정해진 플랫폼에 해당하는 `driver` 2개를 동시에 생성합니다.

```python
@pytest.fixture(scope="function")
def dual_drivers(request, platforms):

    _logger.info(f"create driver for {platforms}")

    driver1 = generate_driver(
        platform=platforms[0],
        is_interaction=True
    )
    driver2 = generate_driver(
        platform=platforms[1],
        is_interaction=True
    )

    yield driver1, driver2
    
    .
    .
    .

```

또한 특정 케이스에서 특정 플랫폼 조합일 때는 테스트 실행을 하지 않도록 하는 스킵 기능을 fixture로 만들어 대응했습니다.

```python
@pytest.fixture(scope="function")
def skip_android_android(platforms):
    """
    platforms = ("android", "android") 일 때 테스트를 스킵합니다.
    """
    if platforms == ("android", "android"):
        pytest.skip("Skipping test for (android, android) based on condition")


@pytest.fixture(scope="function")
def skip_android_ios(platforms):
    """
    platforms = ("android", "ios") 일 때 테스트를 스킵합니다.
    """
    if platforms == ("android", "ios"):
        pytest.skip("Skipping test for (android, ios) based on condition")

.
.
.

```

### 개발팀의 협조로 matching segment 생성

이 문제는 저희 팀에서 해결할 수 있는 문제가 아니었고, 서버 개발팀에 요청해야 했습니다. 개발팀에서는 바쁜 와중에도 감사하게 특정 군(_segment_)에 속해 있는 유저들끼리만 매칭될 수 있는 기능을 제공해 주셨습니다.

이를 이용하여 저희 팀에서는 미리 테스트용 플랫폼별 segment를 생성해 놓은 다음, 테스트 전처리 과정에서 테스트 계정을 생성한 후 테스트로 매칭되어야 하는 메인 계정, 서브 계정에 대해 세그먼트를 할당해 주었습니다.

```python
@pytest.fixture(scope="function")
def create_account(request):

     def _create_account(
        email=None,
        birth_year=2000,
        birth_month=1,
        birth_day=1,
        gender="MALE",
    ):

    account_info = create_new_account(
            email=email,
            birth_year=birth_year,
            birth_month=birth_month,
            birth_day=birth_day,
            gender=gender
        )

    # param_group이 없는 경우라면 기본값을 반환합니다.
    param_group = request.config.getoption("param_group")
    # match 테스트는 매치태그 세그먼트에 할당 해 준 이후 계정 정보를 반환합니다.
    setup_segment_match_tag_group(
        request, account_info["userId"], param_group
    )

    .
    .
    .

```

이 설정을 통해 테스트 병렬 실행 시에, 서로 다른 테스트 시나리오 상의 유저가 만나서 테스트를 실패하거나 하는 경우는 막을 수 있게 되었습니다.

![to-be-matching_pool]({{ "/assets/2025-06-12-how-to-automate-e2e-test-on-1on1-video-chat-app/5.png" | absolute_url }}){: width="550px" .center-image }

### 테스트 케이스 내부에서 `ThreadPoolExecutor` 를 사용한 테스트 스텝의 동시 실행

예를 들어 A 테스트에서 a 유저와 b 유저가 매칭하기 전, 로그인 후 접속까지는 서로의 액션에 의존 관계가 없어 동시에 처리할 수 있습니다. 혹은 매칭 중 서로가 메시지를 입력하여 각자의 화면에 상대방 메시지가 나와야 할 때에도 순차적으로 실행할 필요 없이 동시에 실행해도 됩니다. 이처럼 테스트 케이스 내부에서 `driver` 간 의존 관계가 없는 조작을 식별한 다음, `concurrent.futures`의 `ThreadPoolExecutor`를 이용해 임의의 동작을 concurrent하게 실행 가능한 fixture로 작성했습니다.

```python
from concurrent.futures import as_completed, ThreadPoolExecutor

@pytest.fixture(scope="function")
def concurrent_method():
    
    def _concurrent_method(
        method: Callable[[], None], peer_method: Callable[[], None]
    ) -> None:
        
        # 1:1 interaction, 즉 driver를 최대 2개 사용하므로 max_worker를 2로 지정
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(method), executor.submit(peer_method)]
            for future in as_completed(futures):
                future.result()

    return _concurrent_method

```

![automated_test]({{ "/assets/2025-06-12-how-to-automate-e2e-test-on-1on1-video-chat-app/7.png" | absolute_url }}){: width="770px" .center-image }

이를 통해 테스트 케이스당 실행 시간을 약 **1~2분** 정도 단축할 수 있었으며, 전체 테스트 스위트의 병렬 실행을 통해 기존 순차 실행 대비 **최대 6시간 단축** 할 수 있었습니다.

### interface형태를 이용한 테스트 주도 개발

아자르 테스트 자동화 작업은 Page Object Model을 이용해 구성하고 있습니다. 서비스 화면을 하나의 `Page`로 인식하고 모델링하는 방법인데요, 이때 플랫폼별 동작 방식을 통일시키기 위해 인터페이스(interface)를 사용하게 되었습니다.

이후 테스트 코드에서 페이지 객체를 만들 때 각 page의 interface 타입으로 타입 선언을 해 주고, 객체 생성 시 `driver`만 주입하면 각 플랫폼 구현에 맞춰 동작할 수 있도록 구현했습니다. 이를 통해 테스트 코드를 먼저 작성한 후에 해당 시나리오에 맞춰 플랫폼별 동작 코드를 작성하게 되었습니다.

```python
class TestInMatch

    @pytest.fixture()
    def setup_page_object(self, dual_drivers):
        """
        페이지 객체를 생성하는 테스트 클래스 내 fixture
        """
        self.main_driver, self.peer_driver = dual_drivers

        self.main_mirror_page: Union[BasePage, MirrorPageInterface] = (
            PageFactory.get_page(self.main_driver, PageName.MIRROR_PAGE)
        )
        self.peer_mirror_page: Union[BasePage, MirrorPageInterface] = (
            PageFactory.get_page(self.peer_driver, PageName.MIRROR_PAGE)
        )

        .
        .
        .

```
---

## 결과

위 내용을 조합하여 아래와 같은 테스트 케이스 형태를 얻을 수 있었습니다.

아래 케이스는 2명의 유저를 각각 `main` 과 `peer` 로 명명하고 테스트를 수행합니다.

```python
class TestInMatch
    .
    .
    .

    @pytest.mark.p1
    def test_in_match_example(
        self,
        skip_android_ios,               # (android, ios) 조합인 경우 테스트 스킵
        skip_ios_android,               # (ios, android) 조합인 경우 테스트 스킵
        setup_page_object,              # 페이지 객체 생성
        create_account,                 # 계정 생성
        setup_email_login,              # 이메일 로그인 동작 fixture
        concurrent_method,              # 병렬 실행 fixture
        setup_segment_test_purpose_on,  # 테스트 전처리용 fixture
    ):

        user_info = create_account()
        peer_info = create_account()
        setup_segment_test_purpose_on(user_id=user_info["userId"])
        setup_email_login(
            email=user_info["email"],
            password=user_info["password"],
            peer_email=peer_info["email"],
            peer_password=peer_info["password"],
        )

        def step_main():
            self.main_mirror_page.click_btn_purpose_match()
            self.main_mirror_page.click_label_how_was_your_day()

        def step_peer():
            self.peer_mirror_page.click_label_start_video_chat()

        concurrent_method(step_main, step_peer)

        def assert_main():
            with assume:
                assert self.main_find_new_friends_page.is_my_preview_screen_visible()
            with assume:
                assert (
                    self.main_find_new_friends_page.get_txt_label_header_find_new_friends()
                    == "오늘 하루 어땠어요?"
                )
            with assume:
                assert (
                    self.main_find_new_friends_page.get_txt_label_desc_find_new_friends()
                    == "같은 토픽을 선택한 사람을 만나면 알려드릴게요."
                )

        def assert_peer():
            with assume:
                assert self.peer_find_new_friends_page.is_my_preview_screen_visible()
            with assume:
                assert self.peer_find_new_friends_page.is_image_loading_visible()
            with assume:
                assert (
                    self.peer_find_new_friends_page.get_txt_label_header_find_new_friends()
                    == "찾는 중"
                )

        concurrent_method(assert_main, assert_peer)
```

위 방안들을 통해

- 실행해야 할 플랫폼 조합을 병렬 실행
- 특정 플랫폼 조합만 선택하여 테스트 실행 가능
- 테스트를 실행하지 않아야 할 플랫폼 조합에서는 테스트 스킵 가능
- segment 기능을 활용하여 병렬 실행 중인 테스트 간의 매칭 간섭을 방지
- 불필요한 순차 스텝을 비동기 병렬 실행하여 테스트 실행 시간 단축
- 특정 플랫폼에 의존적이지 않으면서도 플랫폼별로 동일한 테스트 코드 실행

과 같은, 겪고 있었던 문제점들에 대해 해결 및 개선을 할 수 있었습니다.

---

## Interaction 테스트 자동화를 통해 얻은 운영 효과

현재 저희가 구축한 interaction 자동 테스트는 **308개의 테스트 케이스**를 **4개의 플랫폼 조합** (Android-Android, Android-iOS, iOS-Android, iOS-iOS)에서 수행합니다. (Non-interaction 테스트케이스 제외)

만약 이 모든 테스트를 사람이 직접 수동으로 수행한다면 어떨까요?

- **테스트 케이스 수**: 308개 × 4개 조합 = 1,232개 테스트
- **테스트 케이스당 소요 시간**: 전처리 과정 포함 약 **5분** 으로 가정
- **총 소요 시간**: 약 6,160분 (약 102시간)
- **인력 환산**: 약 **13MD(Man-Day)** (플랫폼 조합수 대로 테스트 담당자가 나눠서 수행한다고 해도 약 **3MD** 필요)

이 13MD 분량의 테스트 업무를 자동화를 통해 **약 7시간**으로 단축할 수 있었습니다. 더 나아가 이 테스트들은 **야간에 무인으로 실행**되기 때문에, QA 팀은 업무 시간에 신규 기능에 대한 탐색적 테스트등에 시간을 집중할 수 있게 되었습니다.

결과적으로 테스트 자동화를 통해:
- **시간 효율성**: 약 95% 시간 단축 (102시간 → 7시간)
- **인력 효율성**: 13MD의 반복 업무를 자동화
- **품질 향상**: 일관된 테스트 수행으로 휴먼 에러 방지

를 얻을 수 있게 되었습니다.

---

## 앞으로 해야할 과제들

**1:1 비디오 채팅** 이라는 흔치 않은 기능에 대해 저희 팀이 어떻게 대처하고 있는지 말씀드렸습니다. `driver`를 여러 개 사용하며 인터랙션을 수행하는 테스트 케이스에 대한 테스트 자동화 레퍼런스는 여러 테스트 커뮤니티를 찾아봐도 잘 나오지 않았고, 위에 말씀드린 제약 사항들이 있어서 팀원들과 열심히 브레인스토밍하며 앞으로 나아가고 있습니다.

그러나 아직도 많은 과제가 남아 있습니다.

- 아자르 하위 버전과의 매칭 호환 확인
- 테스트 실행시간 단축
- 이미지, 음성 검증 개선
- AI를 활용한 테스트 검증 로직 개선

등등.... 아직 갈 길이 멀지만, 오늘도 열심히 테스트 코드를 유지 보수해 가며 회귀 버그를 찾아내고 있습니다. 앞으로도 많은 관심과 응원 부탁드립니다.

감사합니다.



## Reference
- [https://docs.pytest.org/en/stable/index.html](https://docs.pytest.org/en/stable/index.html)
- [https://docs.python.org/ko/3.11/library/concurrent.futures.html](https://docs.python.org/ko/3.11/library/concurrent.futures.html)


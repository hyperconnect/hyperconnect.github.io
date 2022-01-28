---
layout: post
date: 2022-01-28
title: 멈춰! 버그 멈춰! E2E 테스트로 버그 멈추기 Feat. Playwright
author: jace
tags: web testing
excerpt: Playwright로 E2E 테스트를 도입한 경험을 공유합니다.
last_modified_at: 2022-01-28
---

안녕하세요👋  Epic Studio, CPaaS Web Unit의 Jace 입니다. ()
저희 팀은 Hyperconnect의 축적된 여러 기술들을 이용해서 실시간 Audio/Video Call SDK를 개발하는 일을 하고 있습니다.  
SDK에서 버그가 발생하면 제품을 사용하는 모든 서비스에 영향을 미치기 때문에, 안정적인 SDK를 제공하는 것을 중요한 목표로 생각하고 있어요.  
항상 버그가 없는 완벽한 코드를 짤 수 있다면 좋겠지만, ([~~제프 딘이 아니라면~~](https://medium.com/@Dev_Bono/%EC%A0%9C%ED%94%84-%EB%94%98%EC%9D%98-%EC%A7%84%EC%8B%A4-3fbb4e0e1cf5)) 불가능한 일입니다. 그 때문에 많은 개발팀에서 테스트 코드를 작성하고 있는데요. 저희 팀도 마찬가지로 새로운 기능을 구현하면서 코드 베이스가 점점 커졌고, 그만큼 버그가 발생할 확률도 높아졌습니다.  

이번 글에서는 테스트를 도입하게된 배경과 **실시간 Audio/Video Call SDK**라는 도메인에서 어떻게 E2E 테스트를 구축했는지. 그리고 그때 사용한 Playwright에 대해서 간략히 소개합니다.

# 1. 멈춰! 버그 멈춰! ✋
> ~~서울의 한 오피스. 버그 두개가 개발자에서 시비를 겁니다. 버그의 괴롭힘 강도가 세지자, 피해 개발자가 멈추라고 소리칩니다. 멈춰!~~

코드베이스가 커질 수록 버그가 많아지는 건 자연스럽긴 하지만, 버그로 인해, 스프린트. 저희 팀에서 주로 겪었던 문제는 사이드 이펙트와 크로스 브라우징 문제였어요. 테스트 코드로 이 두 가지를 개선하는 것을 목표로 삼았습니다.

## 사이드 이펙트

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/01-side-effect.gif" width="200px" alt="사이드이펙트 GIF" />
</center>

그림 1. 사이드 이펙트. (이 개발자는 사이드 이펙트를 뚫고 버그를 모두 고칠 수 있을까요). [출처](https://medium.com/swlh/gold-plating-software-products-7bffe427b215)
{: style="text-align: center; font-style: italic; color: gray;"}

변경한 코드가 예상치 못한 부분에서 문제를 일으킬 수 있는데, 코드베이스가 커지면 이런 문제는 더 자주 발생하고, 예측하기도 더 어렵습니다. 때문에 QA에서는, **“기존 기능들이 문제없이 동작하는지”**, **“예전에 있었던 이슈가 다시 발생하지는 않는지”**를 확인하는 회귀 테스트(Regression Test)를 주기적으로 진행하게됩니다.
이 단계에서 발견된 버그는 개발자에게 리포트되고 수정 후에 다시 QA를 거칩니다.

사실, QA 과정 에서라도 버그가 찾아지면 다행이지만, 버그가 QA 과정에서 발견되는 것과 개발 과정에서 발견되는 것은 시간과 비용이 많은 차이가 납니다. 그래서 발견될 수 있는 문제라면, 개발과정에서 발견하고 싶었어요.

**개발 과정에서 버그 발생**
> 개발 → Test Failed → 수정 → QA → 배포

- 버그의 원인이 좁혀져서 디버깅하기 쉬움

**QA 과정에서 버그 발생**
> 개발 → QA → 버그 리포트 → 수정 → QA → 배포

- 버그의 원인을 찾기 비교적 어려움
- QA 리소스가 더 소모됨
- 배포 시점이 늦어짐

## 크로스 브라우징 이슈

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/02-browsers.png" width="60%" alt="브라우저들" />
</center>

그림 2. 브라우저들. [출처](https://playwright.dev/)
{: style="text-align: center; font-style: italic; color: gray;"}

WebRTC와 Media를 다루는 프로젝트의 특성상, 다른 프로젝트 보다 더 많은 크로스 브라우징 이슈를 겪었습니다. 대부분의 이런 이슈들은 SDK 코드의 문제가 아니라, 브라우저들간의 다른 구현이 원인이라서 완전히 테스트에 의존할 수 밖에 없습니다.

Hyperconnect Audio/Video Call SDK는 `1:1 Call`과 `Group Call` 두 가지 모드를 지원하는데, 이 두가지 모두를 테스트 해야 합니다. 그러면, `(두가지 모드) 2 * 브라우저 수` 만큼 테스트 하게됩니다. Chrome, Safari, Firefox 만 테스트해도 6번 해야되는 거죠. (실제로 테스트 되는 브라우저는 더 많습니다. 모바일 브라우저 등.)  
이런 테스트를 코드 변경할 때 마다 하기엔 너무 힘들었어요. 심호흡 한번 하고 테스트를 하거나, 불안한 마음을 가지고 (문제가 없길 바라면서 🙏) 커밋 해야했습니다.
이런 문제를 해결하려면, 테스트를 미리 작성하고 그게 여러 브라우저에서 돌도록 테스트 환경을 구성해야 했습니다.

# 2. E2E로 회귀 테스트를 자동화 하자

정리해보면, 목표는 발견할 수 있는 **문제를 미리 발견**하고 **크로스 브라우징 이슈/테스트**를 개선하는 것 입니다.
이걸 **E2E로 회귀 테스트를 자동화**하는 방법으로 해결하고자 했습니다. 회귀 테스트 케이스를 모두 통과했다면 사이드 이펙트가 없는거고, 그걸 여러 브라우저에서 자동으로 해보면 되니까요.

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/03-regression-test-case.png" alt="회귀 테스트 케이스" />
</center>

그림 3. 회귀 테스트 케이스.
{: style="text-align: center; font-style: italic; color: gray;"}

여기서 말하는 E2E 테스트는 정확히는 SDK **테스트 앱**을 테스트 하는 것 입니다. SDK에 새로운 기능을 개발할 때, 해당 기능을 (QA와 개발자가)테스트 해볼 수 있도록 테스트 앱을 함께 만들고 있고, QA 테스트 케이스도 테스트 앱을 기준으로 작성됩니다.
이름 그대로 테스트를 위해 만든 앱이라서, E2E 테스트하기에 무척 적합했습니다. 먼저 복잡한 UI/UX가 없어서, Element Selector가 매우 단순하고, UI가 변경될 일이 잘 없어서 테스트가 깨질 가능성도 낮습니다.

## E2E 테스트 프레임워크

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/04-test-app.png" alt="테스트앱" />
</center>

그림 4. Web SDK 테스트 앱을 두개 띄움. 첫 번째 참여자 = Alice, 두 번째 참여자 = Bob
Bob과 Alice가 Audio/Video Call을 한다.
{: style="text-align: center; font-style: italic; color: gray;"}

이미 제목에서 스포 했지만, E2E 테스트는 Playwright를 사용해서 구축했습니다. E2E 프레임워크는 두 가지 조건을 만족해야 했습니다.
첫 번째는 Chrome, Firefox, Safari 크로스 브라우징 테스트가 가능해야 했습니다. 특히, Safari에서 많은 이슈가 생겨서, Safari는 필수였습니다.
두 번째는 여러 탭이나 윈도우를 사용하는 시나리오 구현이 가능해야 했습니다. 예를 들어 아래 테스트 케이스를 구현할 수 있어야 합니다.

> **Summary**: Remote Audio Volume Indication 테스트<br/>
>
**Given**: Room에 2명(Alice, Bob) Join한 상태  
**When**: Alice가 `localAudio`를 켜고, 말을 한다  
**Then**: Bob은 `REMOTE_AUDIO_VOLUME_CHANGED` 이벤트를 받고, 그 값이 0 보다 크다


이걸 E2E 테스트로 구현한다면, 프레임워크는 각각 아래 처럼 동작할 수 있어야 합니다.

**Given**: 브라우저 탭을 두개 띄움  
**When**: 첫 번째 탭을 조작  
**Then**: 두 번째 탭의 값을 확인

Playwright는 크로스 브라우징도 지원하고, 위 같은 케이스도 쉽게 작성할 수 있었습니다. 이제 Playwright에 대해 소개해 볼게요.

# 3. Playwright

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/05-playwright.png" alt="테스트앱" />
</center>

그림 5. Playwright [출처](https://playwright.dev/)
{: style="text-align: center; font-style: italic; color: gray;"}

Playwright는 MS에서 만든 오픈소스 웹 테스트, 자동화 라이브러리 입니다. 하나의 API로 Chromium, Firefox, WebKit까지 테스트 할 수 있습니다. 
([Next 버전](https://playwright.dev/docs/next/api/class-android)에서는 ADB를 이용한 Android Chrome/WebView도 지원하는 걸로 보입니다)

사실, Playwright 자체는 E2E 테스트 프레임워크가 아닙니다. Puppeteer처럼 브라우저를 컨트롤할 수 있는 API를 제공하는 프로그램이에요. 그래서 테스트를 하려면, Playwright에서 만든 [@playwright/test](https://github.com/microsoft/playwright/tree/main/packages/playwright-test)를 같이 사용해야 합니다.
[Puppeteer 팀에 MS로 가서 만든게 Playwright](https://www.infoq.com/news/2020/01/playwright-browser-automation/)라고 하는데, Puppeteer와 비교해서는 조금 더 테스트에 특화된 것 같습니다. 크로스 브라우징 테스트가 가능해 졌고, [@playwright/test](https://github.com/microsoft/playwright/tree/main/packages/playwright-test)같은 자체적인 Test runner도 제공하니까요. Puppeteer로 E2E 테스트를 하려면 Jest, Mocha, Chai 같은 Third-party를 붙여야 합니다.

이제 Playwright로 테스트 코드를 어떻게 작성할 수 있는지 알아봅시다. [문서가 정말 잘되어 있어서](https://playwright.dev/docs/intro), 자세한 기능이나 API에 대한 설명은 하지 않았습니다. 테스트 케이스를 어떻게 Playwright 코드로 옮겼는지를 중점으로 봐주시면 좋을 것 같습니다.

## 환경구성
설치가 감동적으로 간단했습니다.
Selenium 기반의 테스트 환경을 구축하려면, 브라우저 설치하고 버전에 맞는 드라이버를 설치하고, path를 설정하는 과정이 필요한데, Playwright는 두 줄이면 됩니다.

```bash
# 테스팅 라이브러리 설치
$ npm i -D @playwright/test

# 브라우저 설치
$ npx playwright install
```

설치 후에 Config 파일을 작성합니다. 어느 브라우저에서 테스트를 할건지 여기서 설정합니다.

`playwright.config.ts`

```typescript
import { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  timeout: 60 * 1000 * 3,
  use: {
    headless: true,
    ignoreHTTPSErrors: true,
  },
  projects: [
    {
      name: 'Desktop Firefox',
      use: { browserName: 'firefox' },
    },
    {
      name: 'Desktop Safari',
      use: { browserName: 'webkit' },
    },
    {
      name: 'Desktop Chrome',
      use: { browserName: 'chromium' },
    },
  ],
  testDir: 'src',
  testMatch: '*.test.ts',
  worker: 1,
};
```


## 테스트 코드: Hello world
(지금 여기) Hyperconnect 기술블로그 를 대상으로 몇가지 테스트를 작성해봅시다.
아래 네 가지 케이스를 E2E로 작성해 봤어요. 마지막 네 번째 케이스는 일부러 실패하는 케이스를 넣었습니다. 

1. document title이 올바르다
2. footer의 copyright가 올바르다
3. 채용정보 버튼을 누르면, Career 페이지로 이동한다
4. 배경을 100번 클릭하면, dark theme으로 바뀐다. (100번 클릭해도 dark theme 안됩니다)

`tech-blog.test.ts`
```typescript
import { expect, Page, test } from '@playwright/test';

// describe는 테스트를 묶는 단위
test.describe('하이퍼커넥트 기술블로그 테스트', () => {
  let page: Page;

  // beforeAll hook은 최초 딱 한번 실행. initialize 작업등을 수행
  test.beforeAll(async ({ browser, contextOptions }) => {
    const browserContext = await browser.newContext(contextOptions);
    // 페이지 생성
    page = await browserContext.newPage();

    // 기술블로그 링크로 이동
    await page.goto('https://hyperconnect.github.io/');
  });



  test('1. document title이 올바르다', async () => {
    // document.title이 올바른지 확인
    await expect(page).toHaveTitle('Hyperconnect Tech Blog | 하이퍼커넥트의 기술블로그입니다.');
  });



  test('2. footer의 copyright가 올바르다', async () => {
    // footer element를 가져옴
    const copyrightFooter = await page.locator('body > footer > div > div');

    // 올바른 copyright를 계산
    const currentYear = new Date().getFullYear();
    const validCopyright = `© 2013-${currentYear} Hyperconnect Inc.`;

    // footer의 text가 올바른 copyright인지 확인
    await expect(copyrightFooter).toHaveText(validCopyright);
  });



  test('3. 채용정보 버튼을 누르면, Career 페이지로 이동한다', async () => {
    // 채용정보(Career) 버튼을 클릭
    await page.click('body > header > div > nav > div > a:nth-child(3)');

    // 채용 페이지로 이동했는지 확인
    await expect(page).toHaveURL('https://career.hyperconnect.com/');

    console.log('채용 많은 관심 부탁드립니다 🙏');
    console.log('Epic CPaaS Web 팀도 채용 중 입니다 🙌');
    console.log('채용은 여기서: https://career.hyperconnect.com/');
  });



  // 일부러 추가한 실패하는 케이스
  test('4. 배경을 100번 클릭하면, dark theme으로 바뀐다', async () => {
    // 다시 기술블로그 페이지로 이동
    await page.goBack();

    // 배경을 100번 클릭
    for (let i = 0; i < 100; i++) {
      await page.click('body');
    }

    const body = page.locator('body');

    // background가 검정인지 확인 (dark theme 인지 확인)
    await expect(body).toHaveCSS('background-color', 'black');
  });
});
```

테스트 코드를 작성한 뒤, `npx playwright test` 커맨드로 실행하면, 작성한 테스트 코드가 실행됩니다.

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/06-test-result-1.png" alt="테스트 결과 1" />
</center>
<br/>
<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/06-test-result-2.png" alt="테스트 결과 2" />
</center>
<br/>
<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/06-test-result-3.png" alt="테스트 결과 3" />
</center>

그림 6. tech-blog.test.ts 실행 결과
{: style="text-align: center; font-style: italic; color: gray;"}

작성한 테스트 케이스 4개 * 브라우저 3개 = 12개의 테스트가 실행되었습니다. 그 중 9개 성공했고, 일부러 실패하도록 작성한 케이스 3개가 실패했습니다. 테스트가 실패하는 경우 어떤 케이스의 어떤 Assertion 구문이 왜 실패했는지 보여줍니다. 
실패한 4. 배경을 100번 클릭하면, dark theme으로 바뀐다 케이스는 background-color 가
Expected: `black` 이지만,
Received: `rgb(253, 253, 253)` 이라서 실패했다고 친절하게 알려주고 있습니다.
(100번 클릭해도 dark theme 안되니까요)

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/06-test-result-4.png" alt="테스트 결과 4" />
</center>


## 테스트 코드: Real World
이번에는 실제 SDK의 Given, When, Then 형식의 테스트 케이스와 그걸 어떻게 Playwright로 옮겼는지 보여드릴게요. multi-page 시나리오를 어떻게 처리했지 (Alice와 Bob이 어떻게 상호작용)를 위주로 봐주시면 됩니다.

`beforeAll` 부분입니다. 여기에서, Alice Page와 Bob Page을 초기화 합니다.
```typescript
let browserContext: BrowserContext;
let pages: [Page, Page];

test.beforeAll(async ({ browser, contextOptions }) => {
  browserContext = await browser.newContext(contextOptions);

  // 제일 먼저, 브라우저 탭 두개를 생성한다
  pages = await Promise.all([
    browserContext.newPage(), // Alice
    browserContext.newPage(), // Bob
  ]);
 
  // User token 생성등의 initialize 작업
  await control.readyPages({ pages });
});
```

`beforeAll`에서 각각의 page 초기화가 완료되고 나면, 아래 테스트 케이스들이 돌기 시작합니다.

<br/>
> **Summary**: `local-joined` 이벤트 테스트
>
**Given**: -  
**When**: Alice와 Bob이 room에 join 한다  
**Then**: Alice와 Bob이 `local-joined` 이벤트를 받는다


```typescript
test('join시 local-joined 이벤트를 받는다', async () => {
    // Alice와 Bob이 순차적으로 room에 join한다
    await pages.reduce((promise, page) => promise.then(async () => {
      await control.joinRoom(page, roomId!);
    }), Promise.resolve());

    // Alice와 Bob이 모두 local-joined 이벤트를 받는다
    await Promise.all(pages.map((page) => retryWhenNotExpected(async () => {
      const eventLogs = page.locator('#log-container');
      await expect(eventLogs).toHaveText(new RegExp(EventName.LOCAL_JOINED));
    })));
  });
```


<br/>
> **Summary**: Remote Video 출력 테스트
>
**Given**: Room에 2명(Alice, Bob) Join한 상태  
**When**: Alice가 `enableVideoCapturer`, `enableLocalVideo` 를 한다  
**Then**: Bob이 Alice의 비디오를 볼 수 있다

```typescript
test('Remote Video가 표시된다', async () => {
    // Alice가 enableVideoCapturer, enableLocalVideo 를 한다
    await control.enableVideoCapturer(pages[0]);
    await control.enableLocalCapturer(pages[0]);

    // Bob이 Alice의 비디오를 볼 수 있다
    await retryWhenNotExpected(async () => {
      await pages[1].waitForSelector('.remote-video');
      const remoteVideos = pages[1].locator('.remote-video');
      await expect(remoteVideos.first()).toHaveJSProperty('paused', false);
    });
  });
```

<br/>
> **Summary**: `remote-user-left` 이벤트 테스트
>
**Given**: Room에 2명(Alice, Bob) Join한 상태  
**When**: Alice가 room에서 leave 한다  
**Then**: Bob은 `remote-user-left` 이벤트를 받는다

```typescript
test('상대방이 나갈경우 remote-user-left 이벤트를 받는다', async () => {
    // Alice가 room에서 leave 한다
    await control.leaveRoom(pages[0]);

    // Bob은 remote-user-left 이벤트를 받는다
    await retryWhenNotExpected(async () => {
      const eventLogs = pages[1].locator('#log-container');
      await expect(eventLogs).toHaveText(new RegExp(EventName.REMOTE_LEFT));
    });
  });
```

이렇게, BrowserContext를 사용해서 새로운 페이지(탭)을 생성할 수 있고, 각각의 페이지를 사용해서 그냥 일반적인 비동기 코드를 짜듯이 간단하게 multi-page 시나리오를 테스트 할 수 있습니다.

# 4. getUserMedia Mocking 하기
<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/07-camera-permission.png" alt="Playwright WebKit 권한 팝업" />
</center>

그림 7. WebKit 카메라 권한 요청 팝업
{: style="text-align: center; font-style: italic; color: gray;"}

Playwright에서 WebKit과 Firefox는 [카메라와 마이크 권한을 가져오지 못하는 이슈](https://github.com/microsoft/playwright/issues/7635)가 있었습니다. 이 문제를 해결하기 위해 카메라와 마이크를 Mocking 했는데, 그 방법을 간단히 소개드릴게요.
 
Playwright는 `context.grantPermissions(['camera', 'microphone']);` 으로 권한을 가져오는데, Webkit과 Firefox에서는 `Unknown permission: microphone` 에러가 발생했습니다.
위 이슈 때문에, Playwright 말고 [NightWatch](https://nightwatchjs.org/)나 [TestCafe](https://testcafe.io/)등 다른 E2E 프레임워크도 써봤는데, 같은 문제가 있었어요.
결국 다시 Playwright로 돌아와서 문제를 해결할 workaround를 고민해 봤습니다.


- CI 환경에서는 카메라와 마이크가 없다
- (어찌 됐든) Video와 Audio가 상대방에게 전달되서, 테스트 케이스를 통과하기만 하면 된다

이런 근거를 가지고, 카메라/마이크를 사용하는 부분을 Mocking 해보기로 했습니다.
카메라와 마이크에 접근하는 `navigator.mediaDevices.getUserMedia`를 overwrite 해서 카메라와 마이크 권한 없이도, Video / Audio Stream을 제공한다는 아이디어 입니다. (아래 코드 참고)

```typescript
// 기존 내장 getUserMedia 함수 overwrite
navigator.mediaDevices.getUserMedia = (constraints?: MediaStreamConstraints) => {
  const tracks: MediaStreamTrack[] = [];
  if (constraints?.audio) {
    // TODO: Implement audio track mocking
    const audioTrack = getMockAudioStreamTrack();
    tracks.push(audioTrack);
  }

  if (constraints?.video) {
    // TODO: Implement video track mocking
    const videoTrack = getMockVideoStreamTrack();
    tracks.push(videoTrack);
  }

  const stream = new MediaStream(tracks);
  return Promise.resolve(stream);
};
```

<br/>
우선 결과를 미리 공유 드릴게요. overwrite한 `getUserMedia` 으로 동작하는 테스트앱 영상입니다. Video는 4*4 픽셀마다 랜덤한 색상을 가지도록 구현했고, Audio는 (반짝 반짝 작은별) 노래를 계속 연주하도록 구현했습니다.

<center>
  <video src="/assets/2022-01-28-e2e-test-with-playwright/08-mock-stream.mp4" alt="Mocking Stream 영상" controls />
</center>

Mocking한 Video / Audio Track
{: style="text-align: center; font-style: italic; color: gray;"}


## Video Track Mocking
Video Track은 canvas로 구현했습니다. `canvas.captureStram()` 을 사용하면 video track이 포함된 Stream을 얻을 수 있고 Canvas를 업데이트 할때 마다, 해당 Stream에 반영 됩니다.
0.5초 마다, 4*4 크기의 사각형이 랜덤한 색상을 가지도록 구현했어요.

```typescript
export function getMockVideoStreamTrack(width: number = 100, height: number = 100): MediaStreamTrack {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext('2d');

  setInterval(() => {
    if (context) {
      context.clearRect(0, 0, width, height);

      const imageData = context.createImageData(width, height);
      const pixels = imageData.data;
      const numPixels = imageData.width * imageData.height;

      for (let i = 0; i < numPixels; i += 1) {
        pixels[i * 4] = Math.floor(Math.random() * 255); // R
        pixels[i * 4 + 1] = Math.floor(Math.random() * 255); // G
        pixels[i * 4 + 2] = Math.floor(Math.random() * 255); // B
        pixels[i * 4 + 3] = 255; // Alpha
      }

      context.putImageData(imageData, 0, 0);
    }
  }, 500);

  const stream = canvas.captureStream();
  const videoTrack = stream.getVideoTracks()[0];
  return videoTrack;
}
```

## Audio Track Mocking
Audio Track은 [Audio API](https://developer.mozilla.org/ko/docs/Web/API/Web_Audio_API)를 사용해서 구현했어요. `createMediaStreamDestination()` 으로 Stream을 생성하고, Oscillator를 이용해서 Stream에 Audio가 발생하도록 구현하면 됩니다. 저는 “작은별”을 계속 연주하도록 했습니다. 주파수 별로, 계이름을 매핑해두고, 계이름으로 악보 Array를 만들어서 재생하도록 했어요. 코드로 음악 연주했던 재밌는 경험이었습니다.

```typescript
export function getMockAudioStreamTrack(): MediaStreamTrack {
  const context = new AudioContext();
  const destination = context.createMediaStreamDestination();

  const gain = context.createGain();
  gain.gain.value = 0;
  gain.connect(destination);

  const osc = context.createOscillator();
  osc.connect(gain);
  osc.start();

  let nextMusicNoteIndex = 0;

  setInterval(() => {
    const { currentTime } = context;
    osc.frequency.value = littleStarNotes[nextMusicNoteIndex];
    gain.gain.setValueAtTime(0.5, currentTime);
    gain.gain.exponentialRampToValueAtTime(
      0.00001, currentTime + 0.5,
    );

    if (nextMusicNoteIndex >= littleStarNotes.length - 1) {
      nextMusicNoteIndex = 0;
    } else {
      nextMusicNoteIndex += 1;
    }
  }, 1000);

  const audioTrack = destination.stream.getAudioTracks()[0];
  return audioTrack;
}

// 계이름 : 주파수 매핑
const NOTES = {
  C: 1047,
  D: 1175,
  E: 1319,
  F: 1397,
  G: 1568,
  A: 1760,
};

// 작은별 악보
const littleStarNotes = [
  NOTES.C,
  NOTES.C,
  NOTES.G,
  NOTES.G,
  ...
```

## getUserMedia overwrite
이제 카메라/마이크 없이 Video/Audio Stream을 얻을 수 있도록 `getMockVideoStreamTrack`, `getMockAudioStreamTrack`을 구현했으니, `getUserMedia`를 overwrite하면 됩니다. `HCE_USE_MOCK_STREAM` 환경 변수가 `true`인 경우만, overwrite 하도록 했고, CI에서는 `HCE_USE_MOCK_STREAM=true`로 환경변수를 설정하고 있습니다.

`getUserMedia` 를 overwrite하면,  `enumerateDevices` 도 같이 overwrite 해줘야 합니다. `enumerateDevices` 는 현재 카메라/마이크 목록을 반환하는 함수입니다. 때문에, `enumerateDevices` 에서 mocking으로 생성한 audioinput, videoinput을 반환하도록 overwrite 했습니다.

```typescript
// E2E 테스트에서 실제 카메라/마이크 대신 Mock Stream을 사용하기 위한 처리
if (process.env.HCE_USE_MOCK_STREAM) {
  let enumerateDevices: MediaDeviceInfo[] = [];
  navigator.mediaDevices.getUserMedia = (constraints?: MediaStreamConstraints) => {
    enumerateDevices = [];
    const tracks: MediaStreamTrack[] = [];
    if (constraints?.audio) {
      const audioTrack = getMockAudioStreamTrack();
      tracks.push(audioTrack);
      enumerateDevices.push({
        label: audioTrack.label,
        kind: 'audioinput',
        groupId: '1',
        deviceId: '1',
        toJSON: () => '',
      });
    }
    if (constraints?.video) {
      const videoTrack = getMockVideoStreamTrack();
      tracks.push(videoTrack);
      enumerateDevices.push({
        label: videoTrack.label,
        kind: 'videoinput',
        groupId: '2',
        deviceId: '2',
        toJSON: () => '',
      });
    }

    const stream = new MediaStream(tracks);
    return Promise.resolve(stream);
  };
  navigator.mediaDevices.enumerateDevices = async () => enumerateDevices;
}
```

여기까지 하고 나면, 브라우저가 카메라/마이크 권한을 요청하지 않고, 이미 권한을 허용 해둔 것 처럼 동작합니다 🙌. 덕분에 WebKit, Firefox 뿐만 아니라, CI 환경에서도 카메라/마이크 문제없이 테스트 케이스가 통과하게 되었습니다.


# 5. 마치며

<center>
  <img src="/assets/2022-01-28-e2e-test-with-playwright/09-test-conversation.png" width="80%" alt="테스트 관련 슬랙 쓰레드" />
</center>

그림 8. E2E 테스트가 실패했을 때
{: style="text-align: center; font-style: italic; color: gray;"}

지금까지, E2E 테스트를 도입해서 버그를 멈추려고 노력했던 과정에 대해 다루어 보았습니다. E2E나 Playwright 도입을 고려중이신 분들께 도움이 됐으면 좋겠습니다. (~~E2E 테스트 도입하면서 버그한테 열심히 멈추라고 하니까 조금 멈췄습니다~~)

지금은 Github Actions 사용해서 PR을 올리면, E2E 테스트가 자동으로 돕니다. 테스트에 실패하면 Merge 할 수 없도록 정책을 유지하고 있고, 덕분에 버그와 배포할 때 불안한 마음이 줄어들었습니다.

몇가지 한계나 개선할 점이 있기는 합니다.
1. 모든 테스트 케이스를 자동화 할 수 는 없음 (OS나 하드웨어 관련된 부분)- 
    - 네트워크 연결을 끊기 / 다시 연결하기
    - 새로운 Audio Input Device 연결하기
    - 연결했던 Audio Input Device 제거하기
2. 모바일 테스트, 버전별 브라우저 테스트도 가능하면 좋을 것 같음
    - 이 부분은 [BrowserStack에 Playwright](https://www.browserstack.com/docs/automate/playwright)를 연동하는 방법을 생각하고 있습니다


마지막으로 저희가 채용 중 이라는 소식을 전하면서 글을 마칩니다.  
🙌 [채용공고 바로가기](https://career.hyperconnect.com/jobs/) 🙌

## Reference
[https://medium.com/@Dev_Bono/제프-딘의-진실-3fbb4e0e1cf5](https://medium.com/@Dev_Bono/%EC%A0%9C%ED%94%84-%EB%94%98%EC%9D%98-%EC%A7%84%EC%8B%A4-3fbb4e0e1cf5)

[https://github.com/microsoft/playwright](https://github.com/microsoft/playwright)

[https://playwright.dev/docs/next/api/class-android](https://playwright.dev/docs/next/api/class-android)

[https://www.infoq.com/news/2020/01/playwright-browser-automation/](https://www.infoq.com/news/2020/01/playwright-browser-automation/)

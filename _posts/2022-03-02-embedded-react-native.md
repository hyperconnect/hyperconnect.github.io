---
layout: post
date: 2022-03-02
title: 제목은 React Native 도입이라고 하겠습니다. 근데 이제 Hakuna 앱에 곁들여진
author: easton
tags: react-native iOS android
excerpt: Hakuna 앱에 React Native를 임베딩한 경험을 소개합니다.
last_modified_at: 2022-02-21
---

안녕하세요 🙌🏻 
Hakuna Studio, Web Dev Team 의 Easton (신동리) 입니다.
저희 팀은 Hakuna 앱에 포함되는 Webview 화면 개발, Hakuna 앱의 웹 버전인 웹 클라이언트 개발, 어드민 개발 등
웹 기술을 활용하여 Hakuna Studio에서 발생하는 다양한 문제를 풀어내고 있습니다.

Hakuna는 기본적으로 앱이지만 일부 화면에 한해서는 빠른 배포를 위해 Webview로 구성되어 있는데요. 이번에 저희 팀에서 **일부 Webview 화면을 React Native로 전환하는 PoC(Proof of Concept)** 를 진행했습니다.

이번 글에서 React Native로 전환하게 된 배경과 그 과정에서 어떠한 고민들이 이루어졌는지 소개해 드리겠습니다.

# 왜 React Native를 도입해야 하는가 ? 🧐

**1. 사용성 개선 ✨**

Webview는 네트워크를 통해서 서버를 거쳐 로딩하기 때문에 페이지가 로드될 때 발생하는 로딩 시간을 피할 수 없습니다. 

반면, React Native는 [CodePush](https://docs.microsoft.com/ko-kr/appcenter/distribution/codepush/) 를 사용하여 미리 다운로드 받은 화면을 보여주기 때문에 번들을 갱신할 때를 제외하고는 별도의 로딩 시간이 필요하지 않습니다.

또한, React Native 코드는 자바스크립트로 작성되지만 브릿지 역할만 할 뿐 네이티브 코드로 렌더링되기 때문에 Webview보다 좀 더 네이티브에 가까운 경험을 제공할 수 있습니다. (가끔 Android 에서 보이는 UI와 iOS 에서 보이는 UI가 일관되지 않게 보이는 경우가 존재하긴 합니다...😇)

<ul style="display: flex; justify-content: space-between; list-style: none; margin: 0 auto; padding: 0; max-width: 640px;">
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-embedded-react-native/webview-level-page.gif" style="width: 220px; height: 480px;" alt="webview" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">Webview</p>
    </li> 
    <li style="display: flex; flex-direction: column;">
        <img src="/assets/2022-03-02-embedded-react-native/react-native-level-page.gif" style="width: 220px; height: 480px;" alt="react-native" />
        <p style="font-weight: bold; margin-top: 8px; text-align: center;">React Native</p>
    </li>
</ul>

**2. CodePush 📲**

![CodePush](/assets/2022-03-02-embedded-react-native/codepush.png)
그림 1. CodePush [출처](https://www.google.com/url?sa=i&url=https%3A%2F%2Fmedium.com%2Fhumanscape-tech%2Freact-native-code-push%25EB%25A1%259C-%25EB%25B0%25B0%25ED%258F%25AC%25ED%2595%2598%25EA%25B8%25B0-26b320d87f8&psig=AOvVaw16_oGTmN4_t2wHZLLVeL0z&ust=1645144012484000&source=images&cd=vfe&ved=0CAsQjRxqFwoTCJCis5e9hfYCFQAAAAAdAAAAABAJ)
{: style="text-align: center; font-style: italic; color: gray;"}

[CodePush](https://docs.microsoft.com/ko-kr/appcenter/distribution/codepush/)란 Microsoft 에서 만든 오픈 소스로써 앱 스토어 배포 없이 사용자의 디바이스에 직접 배포할 수 있도록 해주는 App Center Cloud Service 입니다.

React Native에서 코드는 두 부분으로 나뉘는데요.

- Native Binary
- **Javascript Bundle**

Javascript Bundle을 갱신할 때 CodePush를 통하여 실시간으로 업데이트가 가능하다는 장점이 있습니다.
> 네이티브 영역의 코드가 변경되어야 하면 앱 스토어 배포가 필요합니다 !

# Flutter vs React Native

![flutter-vs-rn](/assets/2022-03-02-embedded-react-native/flutter-vs-rn.png)
그림 3. Flutter vs React-native [출처](https://blog.wishket.com/wp-content/uploads/2021/10/02.png)
{: style="text-align: center; font-style: italic; color: gray;"}

그렇다면 'React Native 말고 [Flutter](https://flutter.dev/?gclid=Cj0KCQiAmKiQBhClARIsAKtSj-ledj8b020tow7v_YSyuJpPsi3tfAtHzIZtofZ6srAzVfFianJvwLAaAtJcEALw_wcB&gclsrc=aw.ds) 라는 다른 선택지도 있지 않나요?' 라고 물으실 수도 있을 것 같습니다.

Flutter 대신 React Native를 선택한 이유는 두 가지가 있습니다.

**1. 상대적으로 낮은 러닝 커브(Learning Curve)**
 
저희는 이미 웹 프론트엔드 개발을 할 때 주로 [React](https://reactjs.org/) 라이브러리를 사용하기 때문에 React Native 를 학습하기 위한 비용이 현저하게 낮았습니다.

**2. 아자르, 매트릭스 등 사내 타 스튜디오에 운영되고 있는 React Native 프로젝트들을 참고할 수 있다.**

아자르, 매트릭스 등 사내 타 스튜디오에 운영되고 있는 React Native 프로젝트가 존재합니다.

특히, 아자르의 경우 2020년부터 아자르 앱의 일부 화면이 React Native를 임베딩하는 형태로 개발이 되어있었기 때문에 

이번 PoC 를 시작할 때 아자르의 사례 (특히, [안드로이드에 React Native 임베딩 후기](https://hyperconnect.github.io/2020/07/08/android-react-native-embed.html))를 통해 많은 도움을 받을 수 있었습니다. 
(2022년인 지금도 네이티브 앱에 React Native를 임베딩하는 사례는 흔치 않았습니다...😵)

# 프로젝트 초기 환경

React Native 커뮤니티에서 많은 개발자들은 **React Native CLI** 또는 **Expo CLI** 중 하나를 선택하게 됩니다.

저희는 새로운 React Native 프로젝트를 **React Native CLI** 를 통하여 생성하였는데요. 

React Native CLI 를 사용하면 Java / Object-C 로 작성된 기본 모듈을 추가할 수 있다는 강력한 기능이 있기 때문에 

Android 및 iOS 플랫폼 모두에서 애플리케이션을 완벽하게 제어할 수 있다는 점 때문이었습니다.

#### 정적 타입 체커

React Native에 기본적인 정적 타입 체커로 [Flow](https://flow.org/) 가 적용되어 있지만, Flow 의 커뮤니티는 Typescript 에 비해 워낙 작기 때문에 Flow 대신 Typescript 를 도입했습니다.

React Native에서도 Typescript 와 Flow 모두를 지원하는데요.

아래의 명령어를 통하여 별도의 설정 없이 Typescript 템플릿으로 프로젝트를 시작할 수 있습니다.

```
npx react-native init hakuna-react-native --template react-native-template-typescript
```

#### JWT(Json Web Token) 핸들링

네이티브 앱에 임베딩된 React Native 화면이기 때문에 API 요청을 하기 위해서는 먼저 네이티브 앱으로부터 **활성 토큰을 전달**받아 처리해야 했습니다.

**1. 네이티브 앱으로부터 활성 토큰을 가져오는 부분**

저희는 보통 HTTP client 로 많이 사용하시는 [axios](https://axios-http.com/) 를 사용하고 있습니다. 

네이티브 앱에서 React Native로 화면 전환 시, 활성 토큰을 prop 으로 전달받아 [axios instance](https://axios-http.com/docs/instance) 헤더에 추가해주었습니다.

```tsx
const axiosInstance = axios.create({
  baseURL: API_URL,
});

const setDefaultAuthTokenHeader = (token: string | null): void => {
  axiosInstance.defaults.headers.common = {
    Authorization: token ? `Bearer ${token}` : '',
  };
};

const codePushOptions: CodePushOptions = {
  checkFrequency: codePush.CheckFrequency.ON_APP_RESUME,
  installMode: Platform.select({
    ios: codePush.InstallMode.ON_NEXT_RESUME,
    default: codePush.InstallMode.ON_NEXT_RESTART,
  }),
};

type AppProps = {
  user: {
    token: string;
  };
};

const withAppRegister = (Comp: ComponentType<AppProps>): ComponentType<AppProps> => {
  const App: ComponentType<AppProps> = ({ user: { token } }) => { // 네이티브 앱으로부터 전달받은 활성 토큰
    useEffect(() => {
      token && setDefaultAuthTokenHeader(token);
    }, [token]);

    return <Comp {...props} />;
  };

  return codePush(codePushOptions)(App);
};
```

다음으로는, 일정 시간이 지나 토큰이 만료되었을 때에 토큰 갱신에 대한 처리가 필요했습니다.

axios 의 [interceptor](https://axios-http.com/docs/interceptors) 를 활용하였는데요. interceptor 는 Promise 가 `then` 이나 `catch` 로 처리되기 전에 요청이나 응답을 가로챌 수 있습니다.

`catch` 로 처리되기 전에 응답을 가로채어 HTTP 상태 코드가 `403` 일 경우 앱으로부터 갱신된 토큰을 가져와 헤더 토큰을 교체해주었습니다.

**2. 만료된 토큰을 갱신하는 부분**

```tsx
const onResponseError = async (error: AxiosError<APIErrorResponse<ErrorCode>>): Promise<HTTPError> => {
  const status = error.response?.status; // HTTP 상태 코드
  const code = error.response?.data.code; // 에러 코드
  const message = getErrorMessage(status, code, error); // HTTP 상태 코드 & 에러 코드를 받아 에러 메시지를 가져오는 부분

  if (status === 403) {
      setDefaultAuthTokenHeader(refreshToken); // 토큰 갱신
  }
  throw new HTTPError(status, code, message);
};

// On Response
axiosInstance.interceptors.response.use(onResponseSuccess, onResponseError);
```

#### API 요청 상태 관리 (feat. react-query)

저희는 API 요청 상태 관리를 위해 [React Query](https://react-query.tanstack.com/) 를 사용하였습니다.

React Query 를 사용하면 아래와 같이 API 요청 상태 관리를 Hook 으로 표현할 수 있습니다.

```tsx
  const { data, isLoading, isError, isIdle } = useQuery(queryKeys.GET_LEVEL_STATUS, getLevelStatus, options);
```

React Query 는 현재 ReactDOM 에서만 지원되는 `devtools` 를 제외하고 React Native와 바로 동작할 수 있게 설계되어 있습니다.
따라서, 팀에서 관리하는 **Webview, Webclient 등 다른 서비스와 API 요청 상태를 관리하기 위해 만든 커스텀 Hook 을 쉽게 공유하고 재사용 할 수 있다는 장점이 있었습니다.**

#### 컴포넌트 스타일링

컴포넌트 스타일링을 위하여 [tailwind-rn](https://github.com/vadimdemedes/tailwind-rn) 을 도입했습니다. tailwind는 Utility-First 컨셉을 가진 CSS 프레임워크 입니다.
tailwind-rn 은 tailwind의 React Native 버전이라고 보시면 되는데요. tailwind-rn 을 도입한 이유는 아래와 같습니다.

**1. 일관된 디자인 제공 및 쉬운 커스텀**

색상이나 간격, 폰트 등 Utility Class 를 사용하므로 일관된 디자인으로 구현하기가 수월해집니다. 또한 스타일 수정도 용이하기 때문에 디자인 시스템이나 다크 모드 구현도 간편합니다.

```javascript
// tailwind.config.js 예시
module.exports = {
  theme: {
    screens: {
      sm: '480px',
      md: '768px',
      lg: '976px',
      xl: '1440px',
    },
    colors: {
      'blue': '#1fb6ff',
      'purple': '#7e5bef',
      'pink': '#ff49db',
      'orange': '#ff7849',
      'green': '#13ce66',
      'yellow': '#ffc82c',
      'gray-dark': '#273444',
      'gray': '#8492a6',
      'gray-light': '#d3dce6',
    },
    fontFamily: {
      sans: ['Graphik', 'sans-serif'],
      serif: ['Merriweather', 'serif'],
    },
    extend: {
      spacing: {
        '128': '32rem',
        '144': '36rem',
      },
      borderRadius: {
        '4xl': '2rem',
      }
    }
  }
}
```

**2. 유지보수성 향상**

React Native에서 컴포넌트 스타일링을 하기 위해서 보통 [StyleSheet](https://reactnative.dev/docs/stylesheet)를 사용합니다. 

1. 컴포넌트 파일에 `StyleSheet` 를 정의하거나 스타일을 정의한다.
2. 아래처럼 컴포넌트마다 별도의 스타일 정의 파일(`styles.ts`)을 추가한다.

일반적으로 위 두가지 방법 중 하나를 택하게 되는데요.
2번의 경우 컴포넌트가 늘어날 때마다 늘어나는 파일의 개수는 2배가 되는 것을 뜻하기 때문에 관리의 복잡성이 늘어날 수밖에 없습니다.
반면에, tailwind를 사용할 경우 클래스 명으로 스타일을 정의하기 때문에 관리의 용이함이 생기게 됩니다.

```
Modal
├── index.tsx
└── styles.ts
Button
├── index.tsx
└── styles.ts
Breadcrumbs
├── index.tsx
└── styles.ts
Header
├── index.tsx
└── styles.ts
Footer
├── index.tsx
└── styles.ts
...
...
...
```




#### 빌드 & 배포

배포는 두 가지로 구분됩니다. 

**1. 네이티브 앱이 빌드할 때 포함되는 초기 번들 및 디펜던시를 가져오는 과정 (Artifact Upload)** 

**2. 두 번째는 네이티브 변경이 필요하지 않을 때, 사용자 디바이스에 직접 배포되는 과정 (CodePush)**

이 두 과정 모두 Github Actions 사용해서 자동으로 돌아가게끔 구성되어 있습니다.

#### Artifact Upload

React Native에 네이티브와 의존성이 필요한 모듈이 추가될 때는 앱 스토어 배포가 불가피합니다. 따라서, 네이티브 앱이 빌드할 때 React Native의 의존성과 번들 파일을 업로드 할 임의의 저장소가 필요했는데요.

저희는 네이티브 쪽에서 다른 피쳐에서 사용하고 있는 [Nexus Repository](https://nexus3.evilraza.com/)에 업로드 하도록 설정해두었고, Github Actions 사용해서 Tag 생성 시 자동으로 진행되게끔 구성하였습니다.

#### CodePush

먼저 [appcenter cli](https://docs.microsoft.com/ko-kr/appcenter/cli/) 을 통해서 배포 환경 (Staging / Production)을 추가해 주어야 했습니다.

```
$ appcenter codepush deployment add -a hyperconnect/Hakuna-Android-Embeded-React-Native Staging // staging
$ appcenter codepush deployment add -a hyperconnect/Hakuna-Android-Embeded-React-Native Production // production
```

그리고 나서는 Github Actions를 사용해서 `develop`, `master` 브랜치에 머지 될 때 자동으로 appcenter 내에 Staging / Production으로 번들이 업로드 되도록 설정해 주었습니다.

CodePush로 번들을 업로드하는 명령어는 아래와 같습니다.

```
$ appcenter codepush release-react -a hyperconnect/Hakuna-Android-Embeded-React-Native -d Production
```

# 마치며

지금까지 Hakuna 앱에 React Native를 도입하는 PoC 과정에 대해 설명드렸습니다. 혹시라도 기 존재하는 네이티브 앱에 React Native 임베딩을 고려하고 계신 분들에게 작게나마 도움이 됐으면 좋겠습니다. 😌

앞으로 

- 기존 Webview로 개발된 화면의 사용성 개선
- 변경될 여지가 많은 네이티브 화면을 React Native로 전환
- 네이티브 모듈이 필요한 신규 피쳐 개발

등등 React Native를 활용하여 시도해 볼 일들이 많은데요. 이번 PoC 로 Hakuna 앱을 다채롭게 만들 기술적인 선택지가 추가되었다고 믿습니다. (제발...)

끝으로, 관련 작업을 진행하면서 많은 도움을 주신 Hakuna Android / Hakuna iOS / Hakuna Web 팀 분들께 감사하다는 말씀 전하고 글을 마치겠습니다.

## Reference

- [https://reactnative.dev/docs/integration-with-existing-apps](https://reactnative.dev/docs/integration-with-existing-apps)
- [https://reactnative.dev/docs/typescript](https://reactnative.dev/docs/typescript)
- [https://github.com/vadimdemedes/tailwind-rn](https://github.com/vadimdemedes/tailwind-rn)
- [https://reactnative.dev/docs/native-modules-intro](https://reactnative.dev/docs/native-modules-intro)
- [https://hyperconnect.github.io/2020/07/08/android-react-native-embed.html](https://hyperconnect.github.io/2020/07/08/android-react-native-embed.html)

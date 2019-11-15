---
layout: post
date: 2019-10-25
title: 앱내 Webview 개발기
author: hannah
tags: webview react django webpack next.js react-native
excerpt: Azar Webview를 리팩토링하며 배운 점
last_modified_at: 2019-10-25
---

아자르에서는 빠르고 유연한 배포가 필요한 일부 기능에 대해 웹뷰를 활용하고 있습니다. 현재 서버는 Django Rest Framework, 프론트는 Next.js를 사용하여 개발하고 있습니다. 지금의 아키텍쳐로 정착하기 전까지 크게 3번의 변화를 거쳤는데요, 아키텍쳐를 변경하면서 배우고 느낀 점을 공유하고자 합니다.

## 1. Django + React (As Django Template)

처음에는 Django 템플릿 안에 리액트 번들을 삽입하는 방식을 사용했습니다. 번들된 js, css 파일은 Django의 static 파일로 서빙했습니다. 웹뷰의 프론트엔드가 복잡하지 않았고 서버의 역할이 중요했기 때문에 템플릿 개발을 편하게 하기 위해서 리액트를 채택한 경우입니다. 디렉토리 구조는 다음과 같습니다.

```bash
.
├── item_inventory
│   ├── static
│   │   ├── src
│   │   │   └── index.tsx
│   │   └── webpack.config.js
│   └── templates
│       └── index.html
└── static
    └── js
```

아래와 같이 웹팩 설정을 하고 번들된 js를 `item_inventory/templates/index.html` 에 주입했습니다.

```javascript
// webpack.config.js
module.exports = {
  entry: './item_inventory/static/src/index.tsx',
  output: {
    filename: 'js/main.js',
    path: path.resolve(__dirname, 'item_inventory'),
  },
};
```

```html
<!-- templates/item_inventory/index.html -->
<script type="text/javascript" src="{% static 'item_inventory/js/main.js' %}">
```

이러한 방식의 문제점은 webpack에서 Hot Module Relaod(HMR) 설정을 하더라도 결국 Django에서 서빙하는 html 파일을 보면서 개발을 해야하기 때문에 변경사항을 반영할 때 새로고침을 해주어야 한다는 점입니다.

### 캐싱

캐싱을 위해선 빌드 시마다 file name hash를 생성하는데, webpack의 file name hash를 사용할 수 없었습니다. Django 템플릿 안의 script src는 빌드마다 동적으로 바꿀 수 없기 때문입니다. Django만이 알고있는 file hash를 생성하고 url reverse 로 접근 가능하도록 하기 위해서 Django의 [`ManifestFilesMixin`](https://docs.djangoproject.com/en/2.2/ref/contrib/staticfiles/#manifestfilesmixin)과 [`WhiteNoise`](http://whitenoise.evans.io/en/stable/) 미들웨어를 사용했습니다.

프론트엔드가 plain html 수준으로 정말 간단하다면 이 방식을 사용할 수도 있지만 추천하지 않습니다.

### 배포 및 로깅

배포는 ssh로 직접 서버에 들어가서 `git pull`을 받고 `gunicorn`을 재시작 했습니다. 프로덕션에서는 서버 2대를 사용했기 때문에 터미널에서 두 대를 켜놓고 동시에 배포를 하는 진기한 방식을 쓰기도 했습니다. 나중에 `pyinvoke`를 사용해서 remote terminal에 command 를 실행하는 스크립트를 추가하긴 했지만 여전히 ssh에서 직접 배포한다는 점은 동일했습니다. 에러가 날 경우 로그도 서버에 쌓인 로그를 날짜별로 열어 보면서 확인해야했고 로그가 쌓여서 서버 용량 부족 사태가 벌어지기도 했습니다.

## 2. Django `static` 폴더로 Frontend 서빙

새로운 페이지들이 생기면서 각 Django views에 의존하는 템플릿은 더이상 사용하기 어려워졌습니다. 각 app의 템플릿 하위에 리액트가 있었기 때문에 app 간 component 재사용이 불가능했기 때문입니다.

그래서 Django 템플릿을 버리고 프론트엔드 코드를 모두 `webview/` 폴더에 모았습니다. webview에서 webpack 빌드를 하면 번들 결과물이 각 앱의 하위의 `static` 폴더에 생성되고, `collectstatic`을 하면 Django의 static에 모아지는 방식입니다.

```bash
.
├── appA
│   └── static  // after build
├── appB
│   └── static  // after build
├── webview
│   ├── src
│   │   ├── pages
│   │   └── components
│   └── webpack.config.js
└── static  // after collectstatic
```

```javascript
// webpack.config.js
module.exports = (projectName) => {
  return {
    entry: `./src/pages/${projectName}/index.tsx`,
    output: {
      filename: 'js/[name].js',
      path: resolveApp(`${projectName}/static/${projectName}`),
    },
  };
};
```

프론트엔드 코드를 한곳에 모으긴 했지만 여전히 Django에 의존적이어서 다음과 같은 문제가 있었습니다.

- HMR이 되지 않아 개발할 때 변경 사항을 바로 확인하기 번거로우며,
- static 파일을 Django 에서 서빙하기 때문에 webpack hashing이 불가능했습니다.

## 3. 서버 사이드 렌더링 (Next.js + Express)

2번 방법에서는 프론트엔드 코드를 Django가 static 파일로써 서빙했기 때문에 성능이 좋지 않을 뿐만 아니라, 프론트엔드에서 데이터를 렌더링하기 위해서 불필요한 request round trip을 거쳐야했습니다.

![Before - 리팩토링 하기 전 모습]({{"/assets/2019-10-25-webview-history/before.png"}})

그래서 다음으로 정착한 방법은 서버 사이드 렌더링(Next.js)입니다. Django로부터 프론트를 완전히 분리하고 네이티브 클라이언트에서 프론트엔드로 요청을 보내도록 했습니다. 프론트엔드의 Express 서버에서 header 등의 정보를 받아서 처리하고 Next.js 를 통해서 서버사이드 렌더링을 구현했습니다. static 파일 서빙, 포트 포워딩을 위해서 `nginx`를 사용했습니다. Django는 DRF 로 리팩토링하고 순수하게 REST API 로만 사용했습니다.

```bash
.
├── azarwebviewserver
├── backend
├── frontend
│   ├── components
│   ├── pages   // next.js
│   ├── server  // express
│   └── static
└── docker
    ├── backend
    ├── frontend
    └── nginx
```

![After - Next.js 로 리팩토링 후]({{"/assets/2019-10-25-webview-history/before.png"}})

### 네이티브 클라이언트와 통신 방식 (Custom Header)

프론트엔드 서버를 따로 둔 이유는 클라이언트와 통신 방식을 http request로 변경했기 때문입니다. JWT, 유저 정보 등 데이터는 custom header 를 통해 전달받아서 express에서 헤더를 읽고 처리했습니다. 기존에는 클라이언트가 JavaScript object를 `window`에 주입하면 웹뷰에서 해당 object에 접근하여 함수를 호출하는 방식으로 locale이나 platform 같은 정보를 받아 왔습니다. 하지만 이 방식은 로그를 남기기 쉽지 않아 troubleshooting이 어렵고 네이티브에 의존적이어서 디버깅도 번거로웠습니다.

프론트엔드에 서버를 두고 custom header를 통해 request 정보를 받아오니 크게 2가지 장점이 있었습니다.

1. 모든 request의 header 에 담기는 유의미한 정보를 로그로 남길 수 있음. troubleshooting 도 훨씬 쉬워짐
2. request 자체에 정보가 들어오기 때문에, window 객체가 준비되지 않았을 때 요청을 하는 등 버그 위험 줄임

### Server-side Rendering

초기 렌더 시간을 단축하고 프론트엔드 단의 Express 서버를 활용하기 위해 서버사이드 렌더링을 하기로 결정했습니다. [Next.js](https://nextjs.org/)를 채택한 이유는 다음과 같습니다.

1. 체계적인 문서와 활발한 커뮤니티
2. TypeScript 공식 지원
3. Custom Express 서버 구축 용이
4. 파일 시스템 기반 라우팅과 zero-config 지향

아키텍쳐를 고민할 때 아래의 자료를 참고했습니다.

- [Demystifying server-side rendering in React](https://medium.freecodecamp.org/demystifying-reacts-server-side-render-de335d408fe4)
- [왜 React와 서버 사이드 렌더링인가?](https://subicura.com/2016/06/20/server-side-rendering-with-react.html)

이후에도 [다양한 최적화](https://hyperconnect.github.io/2019/07/29/Optimize-webview-bundle-size-1.html)를 통해 응답시간을 1/3 정도로 단축하였습니다.

### Logging

GCP Stackdriver를 통해 위의 모든 request들에 대한 로그를 수집하고 있습니다. 기존에는 재현하기 어려운 버그는 원인을 찾기 쉽지 않고, 클라이언트의 로그에 의존해야 했으나 웹뷰를 통하는 모든 request에 대해 로그를 남기면서 에러가 발생한 맥락과 유저 정보를 파악하기 훨씬 수월해졌습니다. 이외에도 아래처럼 로그를 다양하게 활용하고 있습니다.

1. 각 페이지 및 API 응답 상태코드 모니터링
2. 응답 latency 모니터링 및 퍼포먼스 체크
3. Sentry에 보고되는 에러의 맥락 파악

Stackdriver 에서는 로그를 한눈에 볼 수 있는 대시보드 기능도 제공합니다. 대시보드를 통해 배포 직후 비정상적인 에러가 나타나진 않는지 확인할 수 있습니다. 각 request마다 고유한 `requestId`를 부여해서 로그를 검색하면 유저가 어떤 API 를 요청했는지 정확히 찾아낼 수 있어서 troubleshooting 방식도 개선되었습니다.

![로그 대시보드]({{"/assets/2019-10-25-webview-history/dashboard.png"}})

### 배포

배포 방식도 Docker 를 사용하도록 크게 변경되었습니다. backend(python), frontend(node), nginx 의 도커 이미지를 각각 빌드하고 AWS ECR을 저장소로 사용하였습니다. 등록된 이미지로부터 ECS를 사용하여 컨테이너 오케스트레이션을 구성하였고 CodeDeploy로 자동화를 구축함으로써 더욱 유연하고 간편한 배포 프로세스를 마련하였습니다. 또한 CloudWatch로 메모리와 CPU 사용 현황을 확인합니다.

## 4. React Native

아직 개발 중이지만 3번까지 개발된 웹뷰 중 일부를 React Native로 리팩토링 하고 있습니다. 네이티브 수준의 사용자 경험을 제공함과 동시에 스토어 리뷰를 거치지 않고 빠르게 배포하기 위함입니다.

## 마무리

크게 3번의 리팩토링을 거치면서 배운 것은 1. 아무리 작은 피쳐라도 확장성 고려하기 2. request 에 대해선 최대한 많은 정보를 로그로 남기기 입니다. 지난 방식들을 되돌아보는 것이 부끄럽긴 하지만 누군가에게 도움이 되길 바랍니다.

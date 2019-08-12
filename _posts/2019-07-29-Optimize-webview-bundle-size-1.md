---
layout: post
title: JavaScript Bundle Size 최적화 (1/2)
date: 2019-07-29
author: hoofer
published: true
excerpt: React와 Node로 구성된 웹뷰에서 Bundle Size를 줄여 성능 개선을 노려봅시다
tags: javascript typescript node react nextjs optimization
---

Azar는 기본적으로 앱이지만 일부 화면의 경우 동적 대응을 하기 위해 웹뷰로 구성되어있습니다. 해당 웹뷰는 React로 제작되어있으며 [Next.js](https://nextjs.org/)를 사용하여 SSR을 구현하고 있습니다.  
동적 대응 가능한 화면에 대한 중요도가 점점 커지면서 웹뷰의 중요성도 높아지고 있기 때문에 웹뷰의 성능 개선이 주요 KPI로 설정되었습니다. 이를 위해 웹뷰 성능을 높이기 위하여 JS Bundle Size를 줄였던 경험기를 본 포스팅에서 공유하려고 합니다.

#### 개선 방법 요약

1. [국제화 package `react-intl` → `react-i18next` 으로 변경](#react-intl--react-i18next-로-대체)
2. [Translation 파일 불러오는 방식 변경](#translations-json-code-splitting)
3. Static 파일 불러오는 방식 변경

이번 포스팅(1/2)에서는 1, 2번 과정에 대해서 정리하고 다음 포스팅(2/2)에서 3번과 함께 본격적으로 성능 측정 결과를 공유할 계획입니다.

## 문제 인식

![최적화 작업을 시작하기 전 bundle 파일 분석 결과]({{"/assets/2019-07-29-Optimize-webview-bundle-size/bundle-analyzer-origin.png"}})

최적화 작업을 시작하기 전 bundle 파일 분석 결과

> 개선점을 파악하기 위하여 `webpack-bundle-analyzer` 를 사용

위 그림 중 `commons.{hash}.js` 는 모든 페이지에 들어가는 공통 js 모듈입니다. 보는 것과 같이 **static assets**들, 번역파일인 **translations**, node_module 중 **react-intl**가 큰 부피를 차지하고 있음을 알 수 있습니다.

## react-intl → react-i18next 로 대체

[react i18next vs react intl \| npm trends](https://www.npmtrends.com/react-i18next-vs-react-intl)

위의 트렌드를 보면 `react-intl` 이 더 많이 사용되지만 **빌드 후 사이즈가 더 작고**(13.7KB vs 5.1KB) **문서화가 잘되어있어서** `react-i18next` 로 대체하기로 결정하였습니다.  
동시에 불필요하게 `node_modules/react-intl/locale-data` 를 모두 로딩하던 부분도 개선되는 것을 기대하였습니다.

**결과**

![react-intl 제거 및 react-i18n 적용 후]({{"/assets/2019-07-29-Optimize-webview-bundle-size/bundle-analyzer-2.png"}})

react-intl 제거 및 react-i18n 적용 후

리팩토링 과정에서 `translations` 가 `_app.js` 로 옮겨지게 되었습니다. `_app.js` 역시 모든 페이지에 공통으로 들어가는 컴포넌트이기 때문에 큰 개선효과는 볼 수 없었으나,
`common` + `_app` js 사이즈는 733.28KB → 601.38KB로 18% 가량 감소한 것을 확인할 수 있었습니다.

## Translations json code splitting

**문제점**

본 웹뷰는 locale을 동적으로 변경할 필요가 없는 서비스입니다. 하지만 설령 동적으로 locale이 변경되는 서비스라고 하더라도 모든 언어의 번역 파일을 한번에 불러오는 것은 낭비를 초래할 수 있습니다.
```js
const translations = require(`./messages/${locale}/strings.json`)
```

기존에는 번역 파일을 위와 같이 불러오고 있었는데, Webpack Document [https://webpack.js.org/guides/dependency-management/](https://webpack.js.org/guides/dependency-management/) 에 따르면 위와같이 코드를 작성했을 경우 해당 context에 있을 수 있는 모든 파일을 불러오게 됩니다.  
즉, 앞의 사진들 처럼 `translations/messages` 아래에 있는 모든 언어를 한꺼번에 bundle로 만들게 됩니다.

**개선 방법**
```js
const translations = await import(`./messages/${locale}/strings.json`)
```

[https://webpack.js.org/guides/code-splitting/#dynamic-imports](https://webpack.js.org/guides/code-splitting/#dynamic-imports) 에서 소개하는 **dynamic import**를 적용하였습니다.

위와 같이 작성할 경우 import가 async function으로 사용되며 런타임에 필요한 모듈이 비동기적으로 import 됩니다. 결과적으로 번역 파일들은 빌드타임에 합쳐지지 않고 분리되어 있다가 Javascript가 실행되는 런타임에 필요한 언어만 불러와지게 됩니다.   
`require` 문은 sync하게 작동하는 반면 `dynamic import` 는 async하게 작동하므로 translation 기능을 초기화하는 로직을 새로 만들어야할 필요가 있었습니다.  
SSR 상황에서도 위와 같이 사용할 수 있었던 이유는, SSR 단계에서 랜더링 하기 전에 사용할 파일 이름(`./messages/${locale}/strings.json`)을 알 수 있었기 때문입니다. SSR 초기화 함수에서 참조할 수 있는 request header 값에 locale이 포함되어 있기 때문이 이를 이용하여 async하게 translation json 파일을 불러올 때 까지 기다릴 수 있게 하였습니다.

**결과**

![공통 모듈에 있던 translations 파일들이 모두 분리되어 필요할 때에만 사용될 준비가 되었다]({{"/assets/2019-07-29-Optimize-webview-bundle-size/bundle-analyzer-3.png"}})

공통 모듈에 있던 translations 파일들이 모두 분리되어 필요할 때에만 사용될 준비가 된것을 볼 수 있습니다.

![translation 최적화 전]({{"/assets/2019-07-29-Optimize-webview-bundle-size/iteminventory_old-0bb5eb4d-8927-49bc-8fb2-278ca28a79bc.png"}})

translation 최적화 전

![translation 최적화 후]({{"/assets/2019-07-29-Optimize-webview-bundle-size/iteminventroy_after_translations_opt-826d95f2-f808-4870-9217-5bd9cd55b4b0.png"}})

translation 최적화 후

translation 파일을 code spliting 한 후에 꽤 많은 양의 파일 사이즈가 감소되었습니다. 가장 많이 사용되는 페이지인 아이템 인벤토리 페이지의 경우 gzip 기준 리소스 파일이 1.1 MB → 757KB 로 약 32% 감소한 것을 확인할 수 있었습니다.

## 마무리

- Javascript를 개발하면서 적절한 패키지를 선택할 때는 패키지의 다운로드 수나 깃 저장소의 Star 뿐 아니라, 문서화 정도, 빌드 사이즈 등을 종합적으로 고려하는 습관이 필요함을 알 수 있었습니다.
- 번역파일과 같이 크기가 크고 갯수도 많은 파일같은 경우 dynamic import 등을 활용하여 번들사이즈를 작게 유지할 수 있도록 필히 신경써야합니다.

## References

* [https://nextjs.org/](https://nextjs.org/)
* [https://www.npmtrends.com/react-i18next-vs-react-intl](https://www.npmtrends.com/react-i18next-vs-react-intl)
* [https://webpack.js.org/guides/dependency-management/](https://webpack.js.org/guides/dependency-management/)
* [https://webpack.js.org/guides/code-splitting/#dynamic-imports](https://webpack.js.org/guides/code-splitting/#dynamic-imports)
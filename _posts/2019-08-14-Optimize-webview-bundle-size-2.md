---
layout: post
title: JavaScript Bundle Size 최적화 (2/2)
date: 2019-08-14
author: hoofer
published: true
excerpt: React와 Node로 구성된 웹뷰에서 Bundle Size를 줄여 성능 개선을 노려봅시다
tags: javascript typescript node react nextjs optimization
---

[저번 포스팅](/2019/07/29/Optimize-webview-bundle-size-1.html)에서는 Azar의 웹뷰 환경에서 2가지 방법을 이용하여 JS Bundle Size를 최적화 했던 방법을 소개하였습니다.  
이어서 추가적인 최적화 방법을 공유하고 성능 측정 결과를 공유하도록 하겠습니다. 

#### 개선 방법 요약

1. [국제화 package `react-intl` → `react-i18next` 으로 변경](/2019/07/29/Optimize-webview-bundle-size-1.html#react-intl--react-i18next-로-대체)
2. [Translation 파일 불러오는 방식 변경](/2019/07/29/Optimize-webview-bundle-size-1.html#translations-json-code-splitting)
3. [Static 파일 불러오는 방식 변경](#static-파일-불러오는-방식-변경)

이번 포스팅(2/2)에서는 3번 과정에 대해 설명합니다.

## Static 파일 불러오는 방식 변경

**문제점**

![Translation 최적화 후]({{"/assets/2019-07-29-Optimize-webview-bundle-size/bundle-analyzer-3.png"}})

저번 포스팅의 마지막 Bundle 파일 분석 결과를 보면 여전히 commons 파일이 큰 부피를 차지하고 있음을 볼 수 있습니다.  
원인은 대부분의 static asset들이 base64 encoding 형태로 변환 되면서 동시에 아래와 같은 형태로 사용하고 있었기 때문에 해당 디렉토리 아래에 있던 모든 파일을 번들링하게 되었기 때문입니다. ([Translation 파일 불러오는 방식 변경](/2019/07/29/Optimize-webview-bundle-size-1.html#translations-json-code-splitting) 참고)  
```js
require(`./static/${imgPath}.png`)
```

**개선 방법**

`next-optimizaed-images`는 이미지 파일과 같은 static assets들을 nextjs 에서 사용할 수 있게 해주면서, 파일 이름에 hash를 붙여주고 **일정 크기 이하의 이미지는 base64 encoding 하도록** 만들어주는 등의 기능을 제공합니다.   
이 플러그인에서 base64 encoding 기능은 [url-loader](https://www.npmjs.com/package/url-loader)를 통해서 이루어집니다. `url-loader`는 webpack 환경에서 이미지를 사용하기 위한 loader로 많이 사용되고 있으며 옵션에서`inlineImageLimit` 값을 조정하여 어느정도 크기의 이미지까지 base64 encoding 시킬지 지정할 수 있습니다.

Azar 웹뷰의 대부분의 이미지는 작은 크기이기 때문에 위와 같은 설정 하에서 많은 이미지가 한꺼번에 코드로 바뀌며 번들링 된 것입니다.
서비스 상황에 맞춰서 `inlineImageLimit` 값을 `-1`로 설정해 base64 encoding을 사용하지 않도록 조치하였습니다.

여기서 생각해볼 수 있는 점이 두가지 있습니다.  
첫째, 이전 포스팅처럼 dynamic import를 사용하지 않은 이유는? `url-loader` 처럼 base64 encoding을 시키는 특수한 상황이 아니라면, 어느 webpack 이미지 loader를 사용하던 이미지 파일은 code spliting이 필요하지 않기 때문입니다.  
둘째, base64 encoding의 장점(네트워크 요청 없이 이미지 사용)을 살리기 위해 dynamic import를 사용할 수도 있지 않았을까? 이전 포스팅에서 dynamic import를 사용할 수 있었던 이유는 SSR 환경에서도 어떤 파일이 사용될지 파악할 수 있기 때문이었으나, 이미지파일의 경우 랜더링 되기 전까지는 어떤 파일이 사용될지 파악하기 어려워 사용하지 않았습니다.

**결과**

![static 이미지들을 base64 encoding 하지 않게 설정한 후]({{"/assets/2019-07-29-Optimize-webview-bundle-size/bundle-analyzer-4.png"}})

static 이미지들을 base64 encoding 하지 않게 설정한 후 static 파일들까지 분리되면서 공통 모듈의 부피가 많이 줄어든 것을 확인할 수 있었습니다.

Translations 최적화 후 상황과 비교해보면 gzip 기준 한 페이지의 리소스 파일이 757KB → 369KB 로 약 52% 감소하였음을 확인할 수 있었습니다.
맨 처음 최적화하기 전 기준으로는 1.1MB → 369KB 로 약 66% 감소하였습니다. 즉, 절반 이상 리소스 파일 사이즈를 줄이는데 성공하였습니다.

base64 encoding으로 이미지 파일이 들어가있을 경우 네트워크 요청 없이 이미지를 보여줄 수 있으니 이를 제거하면 로딩 속도에 악영향을 끼칠 수 있다고 생각할 수 있으나, 실제 유저에게 불필요한 리소스 사이즈를 줄이고 이미지 캐싱을 사용해 더 나은 경험을 제공할 수 있을 것으로 생각됩니다.

## 성능 측정 결과 정리

성능 개선 측정은 [Calibre](https://calibreapp.com/)를 사용하였습니다. Azar Webview 중 가장 많이 사용되는 아이템 인밴토리 페이지를 측정하였으며 Singapore, Frankfurt, Mumbai 세개 나라에서의 결과를 정리하였습니다.  
정리한 지표는 First Meaningful paint, Time to interactive, Speed index 세가지 입니다.

![성능개선 지표]({{"/assets/2019-07-29-Optimize-webview-bundle-size/optimize-index.png"}})

**First Meaningful Paint**

![First Meaningful Paint]({{"/assets/2019-07-29-Optimize-webview-bundle-size/optimize-first-meaningful-paint.jpg"}})

**Time to interactive**

![Time to interactive]({{"/assets/2019-07-29-Optimize-webview-bundle-size/optimize-time-to-interactive.jpg"}})

**Speed index**

![Speed index]({{"/assets/2019-07-29-Optimize-webview-bundle-size/optimize-speed-index.jpg"}})

> Galaxy S5, Slow 3G 의 Before Opt 부분 측정값이 없는 이유는 최적화 전에는 timeout(>=20s)으로 Calibre로 측정되지 않았기 때문입니다

## 마무리

- 번들사이즈를 최적화를 통해서 콜드스타트 상황에서의 성능을 꽤 개선할 수 있다는 것을 알 수 있었습니다. 인터넷 속도가 느린 국가까지 서비스를 제공하는 글로벌 웹서비스를 만들게 된다면 고려해보아야하는 요소입니다.
- **최적화 옵션**이 때로는 성능을 더 악화시키는 결과를 초래할 수 있으니 반드시 기능의 로직을 이해하고 사용하도록합니다.

## 이전 글

[JavaScript Bundle Size 최적화 (1/2)](/2019/07/29/Optimize-webview-bundle-size-1.html)

## References

* [https://www.npmjs.com/package/next-optimized-images](https://www.npmjs.com/package/next-optimized-images)
* [https://www.npmjs.com/package/url-loader](https://www.npmjs.com/package/url-loader)

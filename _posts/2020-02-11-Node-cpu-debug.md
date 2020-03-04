---
layout: post
date: 2020-02-11
title: Node CPU 점유율 최적화 경험기
author: hoofer
tags: node nodejs cpu optimize profiling
excerpt: Node 어플리케이션에서 CPU를 최적화하는 방법을 소개합니다.
last_modified_at: 2020-02-11
---

SSR (Server Side Rendering), React 개발자라면 한 번쯤 들어보고 또 실제로 NextJS 등을 사용해서 만들어보셨을 거라 생각됩니다.
보통의 SPA로 개발하고 S3 등에 올려 Static file로 서빙하는 것과는 다르게 **서버에서 렌더링하기 때문에** 서버 자원을 고려할 수밖에 없게 됩니다.
본 포스팅에서는 아자르에서 사용하는 SSR 기반 웹뷰의 서버 인프라에서 CPU 점유율을 최적화한 경험을 공유하고자 합니다.

#### 다루는 내용

1. [프로파일링을 통한 CPU 점유율 문제점 찾기](#프로파일링을-통한-cpu-점유율-문제점-찾기)
2. [CPU 점유율 개선하기](#cpu-점유율-개선하기)
3. [개선 결과](#개선-결과)

#### 문제 인식

![계속 증가하는 CPU 점유율]({{"/assets/2020-02-11-Node-cpu-debug/cpuV0.png"}})

위 그래프에서 알 수 있듯이, 저희 웹뷰 서버에는 이유를 알 수 없으나 CPU 점유율이 지속적으로 증가하는 고질적인 문제가 있었습니다.
메모리 사용량은 증가하지 않으나 CPU 점유율만 상승하는 기이한 형태를 보였습니다.


## 프로파일링을 통한 CPU 점유율 문제점 찾기

#### Node Profiling

Node에는 다행히 프로파일링을 위한 도구가 내장되어있습니다. V8 기반의 프로파일러를 사용할 수 있으며 다음과 같이 `--prof` 옵션으로 손쉽게 프로파일링을 시작할 수 있습니다.

```shell
$ node --prof index.js
```
위 상태로 node application(이 경우에는 SSR 서버)을 실행할 경우 디렉토리에 `isolate-xxx-v8.log` 와 같은 이름으로 프로파일링 로그가 생성됩니다.
~~하지만 파일을 열어봐도 알아볼 수 없습니다.~~

#### Stress test

프로파일링을 할 수 있는 방법을 알았으니, 다음 단계는 실제 서버 동작을 재현해야합니다. SSR 서버를 띄운 상태로 실제 유저들이 접속하는 것 처럼 벤치마킹을 합니다.
벤치마킹 툴로는 **[아파치 웹서버 성능검사 도구](https://httpd.apache.org/docs/2.4/ko/programs/ab.html)** 를 사용합니다. 간단한 http 통신을 벤치마킹하기에는 매우 좋은 툴입니다.

```shell
& ab -k -c 50 -n 10000 "http://localhost:3000"
```

위와 같이 `http://localhost:3000`에 프로파일링하는 서버를 띄워놓고 동시에 **50명씩** 총 **10000명**의 유저 접속을 벤치마킹 해보았습니다.
벤치마킹이 끝나면 초당 서빙 가능 횟수 같은 대략적인 성능도 확인할 수 있습니다.

#### Visualize CPU Usage

이제 프로파일링 로그에 벤치마킹된 결과가 쌓여있을 겁니다. 이 데이터를 유용하게 만들려면 적절한 시각화가 필요합니다. 이러한 프로파일링 자료에는 **Sunburst Graph**나 **Flame Graph**를 주로 사용합니다.
![flame-and-sunburst-graph]({{"/assets/2020-02-11-Node-cpu-debug/graph-example.png"}})
Sunburst graph 같은 경우에는 가운데 원에서 부터 바깥 호로 뻗어나가며, Flame graph의 경우에는 넓은 부분에서 좁은 부분으로 뻗어나가며 CPU를 사용량이 많은 곳을 추적해나갈 수 있습니다.  
> [flame graph example](http://www.brendangregg.com/FlameGraphs/cpu-mysql-updated.svg)

우리의 프로파일링 정보를 시각화하기 위해서는 mapbox의 **flamebearer** Node tool을 사용합니다.
간단하게 프로파일링 로그를 Flame graph로 만들 수 있으며 다음과 같은 방법으로 사용할 수 있습니다. (Node 8.5 이상 필요)

```shell
$ npm install -g flamebearer # flamebearer 설치
$ node --prof-process --preprocess -j isolate*.log | flamebearer # 프로파일링 로그로 Flame graph 생성
```

Flame graph을 확인할 수 있는 html 파일이 다음과 같이 생성됩니다.

![flame-v0]({{"/assets/2020-02-11-Node-cpu-debug/flameV0.png"}})

아자르 웹뷰의 경우 Flame graph를 추적해보니 국제화(i18n) 기능을 수행하는 [i18next](https://www.i18next.com/) 클래스를 initialize 하는 코드를 실행할 때 부하가 크다는 것을 확인할 수 있었습니다.
위 사진의 초록색 부분이 i18next 관련된 실행을 하이라이트한 것이며 전체에서 대부분의 CPU 사용을 차지하는 것을 알 수 있었습니다.

## CPU 점유율 개선하기

문제가 되었던 i18next 클래스의 initialize를 개선하기에 앞서, 기존에 사용하던 방식을 간단하게 살펴보자면 아래와 같습니다.

```typescript
export const initializeI18next = (locale: string, translation: Translation) => {
  i18next.use(initReactI18next).init({
    lng: locale,
    resources: {
      [locale]: {
        translation,
      },
    },
  });
  return i18next;
};
```
SSR을 사용하며, 20개 이상의 언어를 지원하는 아자르 웹뷰의 특성상 각 리퀘스트마다 필요한 언어만을 initialize 해야 할 필요가 있었습니다.
때문에 i18next 클래스를 initialize 하는 함수를 만들어 각 리퀘스트가 들어올 때 마다 실행되게 하였습니다.  


위와 같은 사용 패턴으로 인하여 각 request 마다 불필요한 initialization 이 반복되며 부하를 발생시키고 있었음을 확인하였습니다.
이를 개선하기 위해 initialize 부분을 global scope 에 배치하여 프로세스가 구동할 때 한 번만 실행되게 하였습니다.
기존의 기능은 그대로 유지하기 위해 initialize 된 instance를 재활용하도록 개편하였습니다.

```typescript
i18next.use(initReactI18next).init({
  lng: locale,
  resources: {
    [locale]: {
      translation,
    },
  },
});

export const initializeI18next = (locale: string, translation: Translation) => {
  if (isServer) {
    const serverI18next = i18next.cloneInstance(); // Concurrency를 위해 instance clone
    serverI18next.addResourceBundle(locale, 'translation', translation);
    serverI18next.changeLanguage(locale);
    return serverI18next;
  }
  i18next.addResourceBundle(locale, 'translation', translation);
  i18next.changeLanguage(locale);
  return i18next;
};
```

## 개선 결과

i18n 기능을 개선 후 똑같은 방법과 조건으로 실험하여 아래와 같은 Flame graph를 얻어낼 수 있었습니다.

![flame-v1]({{"/assets/2020-02-11-Node-cpu-debug/flameV1.png"}})

똑같이 i18next 관련된 실행을 하이라이트 하였을 때 상당 부분 줄어든 것을 확인할 수 있었습니다.


또한 개선된 버전을 실 서버에 배포 후에는 아래와 같은 메트릭의 변화가 있었습니다.

![cpu-change]({{"/assets/2020-02-11-Node-cpu-debug/cpuChange.png"}})

~~옆자리 동료: 서버 죽은거 아냐??~~

## 마무리

- 노드의 내장 프로파일링을 통해 노드 어플리케이션의 CPU 사용량을 visualize 할 수 있었습니다.
- 리퀘스트마다 부하가 많이 걸리는 코드 라인을 줄여서 서버 자원을 아낄 수 있었습니다.
- 문제를 해결하긴 하였지만 그렇다고 시간이 지날수록 CPU 사용량이 늘어나는 것을 설명하지는 못했습니다.

원인 규명을 위해 시간 순으로 CPU 점유율의 변화 등을 살펴볼 수는 있겠지만, 문제 자체가 해결된 시점에서 해당 부분은 향후 과제로 넘기기로 했습니다. 나중에 해당 원인을 규명하게 되면 별도의 블로그 글이 되지 않을까 싶네요.

## Reference

* [https://nodejs.org/uk/docs/guides/simple-profiling/](https://nodejs.org/uk/docs/guides/simple-profiling/)
* [https://httpd.apache.org/docs/2.4/ko/programs/ab.html](https://httpd.apache.org/docs/2.4/ko/programs/ab.html)
* [https://github.com/mapbox/flamebearer](https://github.com/mapbox/flamebearer)
* [https://www.i18next.com/](https://www.i18next.com/)

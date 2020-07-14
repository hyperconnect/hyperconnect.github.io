---
layout: post
date: 2020-07-08
title: 안드로이드에 React Native 임베딩 후기
author: evan
tags: android rn
excerpt: 안드로이드에 React Native 를 임베딩을 해 본 후기입니다.
last_modified_at: 2020-07-08
---

아자르에는 `젬`이라는 화폐가 있고, 이 젬을 판매하는 `젬샵` 화면이 있습니다. 이 젬샵 화면은 여느 화면과 다를 바 없이 정해진 디자인의 네이티브 화면으로 구성되어 있었는데요. 어느 날 젬샵에 다음과 같은 요구사항이 생겼습니다.

> 젬샵의 디자인을 수시로 변경해가며 사용자 A/B 테스트를 하고 싶다!

하지만 이를 네이티브 코드로 구현하여 실험해 보기에는 아자르의 릴리즈 주기가 너무 길었습니다. 거의 3~4주에 한 번씩 릴리즈를 했었는데 A/B 테스트를 해보기에는 너무 긴 기간이었죠.

그래서 처음엔 이를 웹뷰로 재구성해 보려고 생각했었습니다. 아자르의 일부 화면이 이미 웹뷰로 되어있었기 때문에 자연스럽게 젬샵에도 웹뷰를 사용하려 했었으나, 곧이어 수익을 내는 화면의 로딩 시간이 오래 걸리면 안될 것 같다는 문제가 제기되었습니다. 그렇게 고민을 하다가 `React Native 를 써보면 어떨까?` 하는 아이디어가 나왔고 바로 이에 대한 검토를 시작했습니다.

### Feasibility check

React Native 를 통해 하이브리드 앱을 만드는 경우는 많이 있지만 네이티브 앱의 일부에만 React Native 를 적용시키는 것은 흔한 use case 가 아니어서, 이게 과연 가능한 일인지부터 조사하는 것이 우선이었습니다.

구글신에게 대강 물어보니 다음 링크를 어렵지 않게 찾을 수 있었습니다.

[Integration with Existing Apps](https://reactnative.dev/docs/integration-with-existing-apps)

제목에 대놓고 `기존 앱에 integration 하기` 라고 되어 있으니 가능하다고 판단하고 매뉴얼을 읽기 시작했습니다.

### 폴더 구조와의 싸움

매뉴얼을 읽기 시작한지 얼마 지나지 않아 다음과 같은 문구를 읽고 경악을 하고 말았습니다.

> To ensure a smooth experience, create a new folder for your integrated React Native project, then copy your existing Android project to an /android subfolder.

React Native 를 임베딩 하기 위해 기존 프로젝트를 폴더째 하위 폴더로 이동하라니.. 주객전도도 이런 주객전도가 없네요. 도저히 받아들이기 어려운 prerequisition 을 보고 잠시 망설였으나, 비즈니스에 필요한 부분이라 쉽게 포기할 수 없었기 때문에 `smooth experience` 를 포기한 채 시도를 해보기로 했습니다. 덕분에 모든 매뉴얼을 step by step 으로 그대로 따라하지 못하고 항상 행간을 읽어야만 했습니다.

### React Native 라이브러리 임베딩

React Native 를 사용하려면 가장 먼저 React Native 라이브러리를 dependency 에 추가하는 일부터 해야 할 것입니다. 그런데 이 React Native 라이브러리는 maven central 등의 repository 에 올라가 있는 것이 아니라, node.js 모듈로만 설치가 가능했습니다. 고민 끝에 node.js 모듈을 임시 폴더에 설치한 다음에 복사해오는 방법을 선택했습니다. `node_modules/react-native/android` 안의 내용들을 사내 maven repository 에 업로드 한 뒤에 `com.facebook.react:react-native` 아티팩트를 dependency 에 추가하여 해결하였습니다.

dependency 가 해결되어 야심차게 샘플 코드를 준비하고 실행을 해봤더니 크래쉬가 발생하였습니다. 크래쉬의 내용인 즉, React Native 를 실행하는 hermes 엔진이 없다는 것입니다. 당연히 native 라이브러리들이 React Native 라이브러리 안에 포함되어 있을 것이라 생각했는데 아니더군요. 이는 임시 폴더 안의 `node_modules/hermes-engine/android` 안에서 `hermes-debug.aar` 과 `hermes-release.aar` 파일을 프로젝트의 `libs` 폴더로 복사해오는 것으로 해결했습니다.

그 와중에 aar 안에 C++ 런타임이 포함되어 있어 빌드가 실패하는 수고로움을 또 겪었습니다. aar 안의 C++ 런타임을 제외하고 리패키징 하여 문제를 회피하였으나, 최신 버전에서는 `hermes-debug.aar` 과 `hermes-cppruntime-debug.aar` 등으로 분리 배포가 되어 더 이상 이러한 고생은 하지 않아도 된다고 합니다.

### 안드로이드와 React Native 간의 통신

다음 링크를 참조하여 안드로이드와 React Native 간의 통신 방법을 이해하고 구현하게 되었습니다.

[Native Modules](https://reactnative.dev/docs/native-modules-android)

[Communication between native and React Native](https://reactnative.dev/docs/communication-android)

### third-party 모듈 설치

React Native 가 실행하는 JavaScript 에서 여러 기능을 사용하려면 React Native third-party 모듈을 또 설치해줘야 합니다. 이들 역시 node.js 모듈로만 설치가 가능합니다. 아까 그 임시 폴더에 일단 설치한 뒤에 폴더 안의 안드로이드 프로젝트 파일들을 복사해오는 방법을 사용했습니다. 다만 build.gradle 파일은 의존성 문제로 그대로 사용할 수 없기 때문에 각각의 third-party 모듈마다 build.gradle 을 자신의 프로젝트에 맞게 수정해야 합니다.

### 결과

우여곡절 끝에 React Native 적용한 결과는 성공적이었습니다.

![React Native 로 구현된 젬샵]({{"/assets/2020-07-08-android-react-native-embed/rngemshop.png"}})

젬샵을 React Native 로 구현하는 데에 성공했고 클라이언트 배포 없이 온라인상의 JavaScript 변경 만으로 디자인 변경이 가능하게 되었습니다.

### 장점과 단점

React Native 를 실제 프로덕션 환경에 적용해보니 다음과 같은 장단점이 있었습니다.

#### 장점
* 클라이언트 재배포 없이 화면 디자인 및 비즈니스 로직 수정 가능
* 웹뷰보다 로딩 및 UI 반응 속도가 빠름
* 웹뷰에 비해 안드로이드와 JavaScript 간의 통신이 용이

#### 단점
* third-party 모듈 설치가 까다로우며, 새로운 모듈이 필요할 경우 클라이언트 재배포가 필요
* 앱 크기가 증가
* 여전히 native 에 비하면 느린 속도

### 마치며

앱에 부분적으로 React Native 를 적용하는 일은 검색해도 잘 나오지 않아 굉장히 challenging 한 일이었는데, 다행히도 성공적으로 끝났습니다. 덕분에 아자르에서는 기존에 웹뷰로 구성되어있던 화면도 React Native 로 재구성하려는 계획도 있습니다. 비록 간단한 후기이지만 추후에 동일한 작업을 하실지 모르는 분들께 조금이나마 도움이 되길 바라며 글을 맺습니다.
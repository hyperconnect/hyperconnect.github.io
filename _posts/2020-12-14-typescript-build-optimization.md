---
layout: post
title: CRA(create-react-app) + TypeScript 환경 빌드 퍼포먼스 최적화
date: 2020-12-14
author: hye
published: true
excerpt: CRA(create-react-app) + TypeScript 환경에서 빌드 로직을 개선하여 배포 속도를 8배 향상한 과정을 공유합니다.
tags: typescript optimization react
---

안녕하세요, Azar WebDev 팀의 Hye입니다. 저희 팀은 웹 기반 기술을 이용하여 Azar 서비스에 동적으로 빠른 대응을 제공하는 것을 목표로 하고 있습니다. 이번 문서에서는 어느 시점부터 배포 시간이 20분에 수렴해가면서 빠른 iteration을 지향하는 팀의 목표에 부합하지 않던 Azar 백오피스의 느린 배포 속도의 원인을 찾고 빌드 로직을 개선하여 빌드 퍼포먼스를 8배 이상 향상한 경험을 공유합니다.

Azar 백오피스의 프론트엔드는 [create-react-app](https://create-react-app.dev/)팀에서 제공하는 공식 템플릿인 [cra-template-typescript](https://www.npmjs.com/package/cra-template-typescript)를 바탕으로 스캐폴딩 되어 있습니다. 빌드 퍼포먼스를 향상한 작업 중 가장 큰 향상 폭을 냈던 작업은 해당 템플릿에서 제공하는 타입스크립트 빌드 프로세스와 관련이 있습니다. 이 작업 과정을 위주로 공유하고자 합니다.

![빌드 최적화 전과 후]({{"/assets/2020-12-14-typescript-build-optimization/01-before-after.png"}})

## Background

처음 이 문제를 해결하기 위해서 아래와 같은 작업을 적용하였습니다. 효과는 있었지만 배포 시간 단축은 미미했습니다.

#### 배포 파이프라인별 빌드 프로세스 분리
소스맵이 필요하지 않으며, internal에서 단기간 쓰이고 undeploy되는 배포 파이프라인에서는 런타임 에러 수집이 불필요하다고 판단되어 빌드 프로세스에서 소스맵 생성과 [Sentry](https://sentry.io/welcome/) 연결 과정을 제거하였습니다.

#### minimize 시 병렬 프로세스 수 증량
CRA 템플릿에서는 [Terser Plugin](https://webpack.js.org/plugins/terser-webpack-plugin/)을 통해서 minimize 및 optimization을 제공합니다. 이 작업을 병렬으로 수행하는 프로세스를 빌드머신의 CPU 코어 수 만큼 증량하였으며, 빌드 머신의 노드 타입을 한 단계 증가하여 4코어에서 8코어로 업그레이드하였습니다.

> CRA 템플릿에 built-in 되어있는 웹팩 설정들을 수정하고자 할 땐 eject를 지양하고 [customize-cra](https://github.com/arackaf/customize-cra) 라이브러리를 이용해 오버라이딩 함수를 작성하여 주입하였습니다.

이 외에 다양한 부분을 적용해보았지만 퍼포먼스가 크게 향상되지 않았습니다. 컴파일 시간 자체가 매우 오래 걸렸기 때문입니다. 문제를 파악하고 CRA에서 TypeScript를 빌드하는 과정을 분석해보았습니다.

## CRA에서 TypeScript를 빌드하는 과정

**Build process in create-react-app**

![CRA build process]({{"/assets/2020-12-14-typescript-build-optimization/02-cra-build-process.png"}})

CRA는 build 실행 시 위 그림과 같은 순서로 작업을 진행합니다. CRA에서 TypeScript를 빌드하는 과정을 알아보기 위해 CRA의 웹팩 설정 내용을 확인해보았습니다.

**Type Checking**

![type checking]({{"/assets/2020-12-14-typescript-build-optimization/03-ts-build-1.png"}})

먼저 CRA는 [fork-ts-checker-webpack-plugin](https://www.npmjs.com/package/fork-ts-checker-webpack-plugin)을 이용하여 type checking을 진행합니다.

```javascript
useTypeScript &&
        new ForkTsCheckerWebpackPlugin({
          typescript: resolve.sync('typescript', {
            basedir: paths.appNodeModules,
          }),
          async: isEnvDevelopment,
          useTypescriptIncrementalApi: true,
          checkSyntacticErrors: true,
          resolveModuleNameModule: process.versions.pnp
            ? `${__dirname}/pnpTs.js`
            : undefined,
          resolveTypeReferenceDirectiveModule: process.versions.pnp
            ? `${__dirname}/pnpTs.js`
            : undefined,
          tsconfig: paths.appTsConfig,
          reportFiles: [
            '**',
            '!**/__tests__/**',
            '!**/?(*.)(spec|test).*',
            '!**/src/setupProxy.*',
            '!**/src/setupTests.*',
          ],
          silent: true,
          // The formatter is invoked directly in WebpackDevServerUtils during development
          formatter: isEnvProduction ? typescriptFormatter : undefined,
        }),
```

**Transpile**

![transpile]({{"/assets/2020-12-14-typescript-build-optimization/04-ts-build-2.png"}})

Webpack을 통해 TypeScript를 transpile하는 대표적인 방법은 다음과 같습니다.

1. ts-loader를 통해 ES Next 스펙으로 transpile + babel-loader를 통해 transpile

2. ts-loader의 JSX to ES5 traspile 기능을 사용하여 babel-loader 없이 transpile

3. **babel-loader에 TypeScript가 포함된 babel preset을 사용하여 ts-loader 없이 transpile**

이 중 CRA는 3번째 방법을 사용하고 있습니다. TypeScript뿐만 아니라 Flux, JSX, ES Next를 지원하는 custom babel preset을 탑재하여 babel-loader를 통해 transpile 프로세스를 진행합니다.

babel-loader에서도 type checking을 진행하지만, 별도의 플러그인을 사용하여 type checking process를 진행하는 이유는 loader가 싱글 스레드를 지원하기 때문입니다. 빌드 속도를 높이기 위해 각 과정이 분리되어 있었습니다. CRA의 built in webpack 설정에는 이를 포함하여 많은 설정이 최적화되어 있습니다.

그러므로 CRA에서는 fork-ts-webpack-plugin을 통해 type checking을 진행하고, TypeScript를 지원하는 babel preset을 탑재하여 transpile을 진행하고 있습니다.

### 빌드를 느리게 만든 원인

> [speed-measure-webpack-plugin](https://github.com/stephencookdev/speed-measure-webpack-plugin) 

위 도구를 통해 웹팩의 플러그인 및 로더별 속도를 쉽게 확인할 수 있었습니다. 그 결과 TypeScript 빌드 시 type checking을 진행하였던 fork-ts-checker-webpack-plugin에서 매우 긴 시간을 소요하고 있음을 파악하게 되었습니다. 해당 플러그인을 disable 하는 오버라이딩 함수를 주입하고 빌드를 돌린 결과 15분을 웃돌던 빌드 시간이 2분대로 줄어들었습니다.

**결론적으로는 fork-ts-checker-webpack-plugin을 disable하고, tsc를 통해 type checking을 진행하도록 수정하여 빌드 퍼포먼스를 대폭 향상했습니다.**

## fork-ts-checker-webpack-plugin과 tsc의 incremental compile 로직 비교

같은 type checking인데 fork-ts-checker-webpack-plugin만 어느 순간부터 유난히 느려졌던 이유는 도구별로 incremental compile (증분 컴파일)을 수행하기 위한 로직이 다르기 때문이었습니다. incremental compile을 수행하기 위해선 매 빌드 시 새로 변경된 파일이 무엇인지, 어떤 파일과 종속성이 있는지 등을 파악하는 로직이 필요합니다. 도구별로 이를 파악하는 로직은 다음과 같습니다.

#### fork-ts-checker-webpack-plugin
매 빌드 시 새로 변경된 파일과 어떤 파일과 종속성이 있는지를 찾아내는 로직을 진행합니다. 패키지 별로 존재하는 *.d.ts 파일의 type checking도 진행하기 때문에 이 로직은 **프로젝트의 크기가 커질수록 소요시간도 급격히 증가하게 됩니다.**

fork-ts-checker-webpack-plugin은 tsc에서 제공하는 compile API 중 incremental api를 요청하여 증분 컴파일을 수행합니다. TypeScript는 [tree-sitter](https://tree-sitter.github.io/) 라이브러리에서 제공하는 incremental parser를 통해 이를 수행하고 있습니다. tree-sitter의 incremental parser는 state-matching을 통해 subtree를 재사용하는 트리 구조의 LR 파서로, t: new terminal symbols, s: modification sites in a tree, N: nodes일 때 O(t+slgN)의 시간복잡도를 가집니다.

아래 그래프는 tree-sitter의 incremental parser를 이용하였을 때, 아자르 백오피스의 프로젝트 크기별로 소요되는 incremental build 시간입니다.

![fork-ts-checker-webpack-plugin의 incremental compile 속도]({{"/assets/2020-12-14-typescript-build-optimization/05-graph.png"}}) <br />
> 그래프를 작성할 때 사용한 빌드머신은 배포용으로 사용하는 빌드머신과 성능의 차이가 있어 시간 값이 다르지만,<br>소요시간의 변화는 비례합니다.

#### tsc
반면 tsc는 빌드 시 .tsbuildinfo 파일을 생성합니다. 다음 빌드 시 해당 파일을 참고하여 incremental compile을 위한 정보 파악 로직을 최대한 줄일 수 있기 때문입니다.

이러한 방식의 차이는 프로젝트의 크기가 커짐과 함께 빌드 속도에 큰 차이를 만들어냅니다.

incremental compile 시 소모되는 시간은 **incremental compile을 위한 전처리 시간(A) + 변경된 파일만 compile 하는 시간(전체 파일을 compile 하는 시간(B) - 변경되지 않은 파일을 compile 하는 시간(C))**으로 이루어집니다. A가 C보다 작아야 최적화 시 속도 이득을 얻을 수 있습니다. 그러나 fork-ts-checker-webpack-plugin의 경우 매 빌드마다 A에서 incremental parsing 비용이 발생하여 소요되는 시간이 같고, 프로젝트의 크기가 커질수록 A에 소요되는 시간이 급격히 증가하면서 A가 C보다 커지기 때문에 빌드 시 최적화를 하지 않는 것보다 더 오랜 시간이 소모됩니다. Azar 백오피스의 프론트엔드 프로젝트가 사용하고 있는 create-react-app typescript 템플릿의 경우, fork-ts-checker-webpack-plugin을 통해 type checking 및 incremental compile을 하고 있었으나 프로젝트의 크기가 커짐에 따라 incremental parsing에 소요되는 시간이 급격히 증가하게 된 것이었습니다.

fork-ts-checker-webpack-plugin에서 tsc의 파일 캐싱 방식을 채택하지 못한 이유는 CRA에서 TypeScript compile시 noEmit 옵션을 활성화하였기 때문에 캐싱용 파일을 write 하지 못한 것으로 예상됩니다. TypeScript 4.0 버전부터는 noEmit과 incremental 옵션을 동시에 활성화할 수 있기 때문에 해당 플러그인의 incremental compile 로직 방식이 변경되길 기대합니다.

## 결론

* cra-template-typescript에 내장되어 있는 fork-ts-checker-webpack-plugin의 incremental compile 최적화는 프로젝트의 크기가 커짐에 따라 오히려 성능을 더 악화시키는 결과를 초래할 수 있음을 알게되었습니다. 
* incremental compile 로직이 파일 캐싱 기반인 도구를 통해 type checking을 진행하여 빌드 퍼포먼스를 개선하였습니다.

![결과]({{"/assets/2020-12-14-typescript-build-optimization/06-result.png"}}) <br />
> 빌드 로직 개선 결과 🚀

## References

* [create-react-app](https://create-react-app.dev/)
* [fork-ts-checker-webpack-plugin](https://www.npmjs.com/package/fork-ts-checker-webpack-plugin)
* [TypeScript - src/compiler/parser.ts](https://github.com/microsoft/TypeScript/blob/master/src/compiler/parser.ts)
* [customize-cra - src/customizers/webpack.js](https://github.com/arackaf/customize-cra/blob/master/src/customizers/webpack.js)
* [tree-sitter: a new parsing system for programming tools in GitHub Universe 2017](https://www.youtube.com/watch?v=a1rC79DHpmY)

---
layout: post
date: 2022-04-25
title: Tuist를 활용한 하쿠나 iOS 프로젝트 모듈화 적용하기
author: wick
tags: iOS module
excerpt: 하쿠나 iOS 프로젝트 모듈화를 진행했던 경험을 소개합니다.
---

안녕하세요 👋
하이퍼커넥트 하쿠나 스튜디오 iOS 팀의 wick(윤새결) 입니다.

이번 포스트에는 하쿠나 iOS팀에서 진행했던 iOS 프로젝트 모듈화 과정과 경험을 소개하려고 합니다. 이번 포스트에서의 주제는 다음과 같습니다. 

- Tuist소개
- 하쿠나 iOS 프로젝트 현황
- 모듈화 적용시 기대 효과 
- 1차 모듈화(모듈 정의)
- 2차 모듈화(모듈간 의존성 분리)
- 앞으로 계획과 마무리

# Tuist란?
![tuist]({{ "/assets/2022-04-25-ios-modularization/tuist.gif" }}){: .center-image }

Tuist는 XcodeGen과 더불어 Xcode 프로젝트 파일의 생성및 관리할 수 있는 도구 입니다. XcodeGen은 프로젝트 설정을 YML로 관리 하는 반면에 Tuist는 Swift 언어로 관리할 수 었어 iOS 개발자라면 어렵지 않게 프로젝트 설정을 할 수 있습니다. 

하쿠나 iOS팀에서는 신규 기능을 머지 할 때 Xcode 프로젝트 파일에서 충돌나는 고통을 줄여 보고자 Tuist를 도입해 사용하고 있습니다. 이번 모듈화 작업 역시 Tuist를 사용해 모듈 정의와 구성에 많은 도움을 받았고, Tuist의 버전업이 계속 되는 만큼 하쿠나 iOS 프로젝트에 필요한 기능이 추가된다면 적극적으로 도입해 볼 생각입니다. 

# 하쿠나 iOS 프로젝트 현황
모듈화를 진행 하기전 현재 하쿠나 iOS 프로젝트의 상태를 파악해야 했습니다. 왜냐하면 어떤 성격의 코드들과 파일들이 구성되어 있는지 확인해야지만 공통의 목적과 성격을 가진 파일을 분리 할 수 있기 때문입니다.
최종적으로 확인한 결과는 크게 5가지 입니다.

- Util
	- 유틸 클래스, Extension
- Resource
	- 이미지, 영상, 번역문자열
- API
	- API 메소드, 모델
- CommonUI 
	- 공통으로 사용하는 UI컴포넌트
- Feature
	- 앱 화면을 담당

모듈 측면에서 확인해보면 아래의 이미지와 같습니다.

![before_diagram]({{ "/assets/2022-04-25-ios-modularization/before_diagram.png" }}){: height="300px" .center-image }

하나의 **App** 모듈에 **Util**, **Resource**, **API**, **CommonUI**, **Feature**의 성격인 코드들이 모두 포함되어 있어 결합도가 높은 상황임을 알 수 있습니다.

![before_file]({{ "/assets/2022-04-25-ios-modularization/before_file.png" }}){: height="300px" .center-image }

파일배치 측면에서는 단순 형태 기준으로 파일들이 배치되어 있음을 확인 할 수 있었습니다. 그래서 평소 신규 기능 개발을 위해 파일을 어디에다 추가하면 좋을지 고민하는 시간이 종종 있었습니다. 🥲

팀 구성원이 점점 늘어 나고 프로젝트가 비대해 지면서 생산성 개선을 위해 모듈화에 대한 필요성을 더욱 느낄 수 있었습니다. 


# 모듈화 적용시 기대되는 효과
하쿠나 iOS팀에서는 모듈화를 통해 기대되는 효과와 목표를 크게 4가지로 잡았고 아래와 같습니다.

- 코드 안정성
	- 모듈간 결합도가 낮아지고 응집도가 높아지는 만큼 안정성이 높아지길 기대합니다.
	- 문제 발생시 분석이 수월해질 것으로 예상합니다.

- 개발 생산성
	- 모듈별 의존성이 낮아지면 고려해야 하는 범위가 낮아져 개발 속도가 향상됩니다.
	- 코드 리뷰시 관련 모듈만 검토가 가능해 리뷰어에게 편의가 높아질 것입니다.

- 빌드 속도
	- 자주 변경되지 않는 모듈의 빌드가 발생하지 않아 빌드 속도에도 작은 영향을 줄 것 입니다.

- 사용 목적에 맞는 코드 배치
	- 용도와 목적에 맞는 코드 배치로 이해하기 쉬운 프로젝트 구성이 될 것입니다.


# 1차 모듈화(모듈 정의)
모듈화 작업은 많은 파일과 설정이 변경되는 작업이므로 단계를 나누어 진행 했습니다. 1차 작업에서는 모듈을 정의하고 용도와 목적에 맞게 파일들을 각 모듈에 배치 시키는 작업을 주로 진행 했습니다.

## Tuist로 모듈 정의하기
Tuist에는 프로젝트 구성을 아래와 같이 할 수 있습니다. 타겟의 product타입, 소스, 리소스, 헤더파일, 의존성까지도 설정 가능해 아주 손쉽게 모듈을 구성 할 수 있습니다. 

```swift
import ProjectDescription

let project = Project(
    name: "MyApp",
    organizationName: "MyOrg",
    targets: [
        Target(
            name: "MyApp",
            platform: .iOS,
            product: .app, // or .framework
            bundleId: "io.tuist.MyApp",
            infoPlist: "Info.plist",
            sources: ["Sources/**"],
            resources: ["Resources/**"],
            headers: .headers(
                public: ["Sources/public/A/**", "Sources/public/B/**"],
                private: "Sources/private/**",
                project: ["Sources/project/A/**", "Sources/project/B/**"]
            ),
            dependencies: [
                /* Target dependencies can be defined here */
                /* .framework(path: "framework") */
            ]
        ),
        Target(
            name: "MyAppTests",
            platform: .iOS,
            product: .unitTests,
            bundleId: "io.tuist.MyAppTests",
            infoPlist: "Info.plist",
            sources: ["Tests/**"],
            dependencies: [
                .target(name: "MyApp")
            ]
        )
    ]
)
```
Tuist를 사용해서 4가지의 모듈을 정의 했습니다. 각 모듈에 포함되어야 하는 코드들의 성격, 기준을 아래와 같이 정의해 하나씩 하나씩 파일과 코드들을 배치하였습니다.

- Util
	- 공통적으로 사용하는 유틸클래스와 Cocoa Touch framework들을 Extension하는 파일
- CommonUI
	- 공통으로 사용하는 UI컴포넌트 (ex. Button, View...)
- API
	- 하쿠나 백엔드 API 메소드, 모델
- Resource
	- 디자인팀에서 받은 이미지 소스, 컬러, 번역 문구, 영상

## 1차 모듈작업 결과

![1phase_result]({{ "/assets/2022-04-25-ios-modularization/1phase_result.png" }}){: .center-image }

하나의 App 모듈에서 **Util**, **API**, **Resource**, **CommonUI**로 모듈로 분리가 되었지만, 모듈간 의존성이 남아 결합도가 남아 있는 상황입니다. 그래도 모듈을 정의하고 각 모듈에 맞는 파일, 코드들을 분리해 배치 했다는데 의미가 있었습니다. 

# 2차 모듈화 (모듈간 의존성 분리)
1차 작업에서는 모듈정의, 파일 배치를 중점적으로 수행 했습니다. 하지만 아직 모듈간 의존성이 남아 있어 독립적으로 모듈들을 따로 사용하기에는 어려운 상황 이였습니다. 그래서 2차 작업에서는 모듈간 의존성을 분리하고, 각 모듈내 에서 파일을 형태별로 구분하지 않고 유저스토리별로 구분하는 작업을 수행했습니다. 

## 모듈간 의존성 분리
모듈간 의존성 분리 작업은 API, CommonUI모듈에서 Util과 Resource를 의존하고 있는것을 분리하고자 했습니다. 하지만 Util모듈에 포함되는 코드들의경우 모든 모듈에서 사용하는 메소드들이 많았습니다. 그래서 **Util**을 의존하는 케이스는 유지하는것으로 결정해 작업을 수행습니다.
CommonUI의 경우 Resource의 이미지, 색상, 번역 문구들을 사용하고 있었습니다. 이 경우 UI컴포넌트를 이미지, 색상, 문구들을 포함하는 **Configuration**객체를 App모듈에서 넘겨주어 구성하게 했습니다. 
```swift
// Configuration 사용예시
// Configuration in CommonUI module
public struct ButtonConfiguration {
	let backgroundColor: UIColor
	let title: String
	...
}

//App Module
final class ViewController: UIViewController {
	let button: HakunaButton
	
	init() {
		let buttonConfig = ButtonConfiguration(BacgroundColor: .white, ...)
		button = HakunaButton(config: buttonConfig)
	}
}
```

API에서도 Resource를 사용하고 있었습니다. Hakuna 에서는 Swagger Codegen을 사용해 API메소드와 모델들을 자동으로 생성해서 사용하고 있어서 API 모듈에는 자동으로 생성되는 파일 관련 코드외에는 포함되지 않게 작업하였고 Resource를 사용하는 코드들은 App모듈에 Extension으로 정의하였습니다.

## 유저스토리별로 파일구분
유저 스토리별 파일 구분 작업은 주로 App, CommonUI모듈에서 작업 되었습니다. 
기존 App 모듈에서는 파일 구분을 단지 형태별로 구분지어 아래와 같이 사용하고 있었습니다. 

![App_file_before]({{ "/assets/2022-04-25-ios-modularization/App_file_before.png" }}){: .center-image }

이렇게 형태별로 사용하면서 프로젝트가 비대해지고 팀 구성원이 늘어나게 되면서 한 그룹에 많은 파일들이 배치되게 되면서 파일 찾기가 힘들어지고, 신규 기능 작업시 어디에 파일을 추가해야 좋을지 고민하는 시간이 늘어나게 되는 상황이였습니다.
그래서 파일들을 유저 스토리별로 구분지어 이런 어려움을 해결하고자 했습니다. 유저 스토리별로 파일 구분은 아래와 같이 진행 되었습니다.

![App_file_after]({{ "/assets/2022-04-25-ios-modularization/App_file_after.png" }}){: .center-image }

CommonUI의 경우 1차 작업시에는 파일 구분이 없어서 파일을 찾기가 힘들었었습니다. 그래서 UI컴포넌트 별로 구분하게 되었고 아래와 같이 진행 되었습니다.

![CommonUI_file_result]({{ "/assets/2022-04-25-ios-modularization/CommonUI_file_result.png" }}){: .center-image }

## 2차 모듈작업 결과

![2phase_result]({{ "/assets/2022-04-25-ios-modularization/2phase_result.png" }}){: .center-image }

모듈화 적용전 하나의 App모듈인 상황보다 많은 개선이 이루어졌습니다. 하지만 모듈화 작업은 아직 많이 남았다고 생각합니다. (화이팅 💪)
모듈내 파일들을 유저 스토리 별로 분리하고 나서는 파일을 찾거나 어떤 새로운 작업을 시작하려고 할때 망설임 없이 파일을 찾을 수 있고, 어디에 파일을 추가할지 명확하게 할 수 있어 만족감이 좋았습니다. 😀 유저 스토리별로 파일을 구분짓는 작업은 앞으로 진행하게될 유저스토리별로 빌드가 가능하게하는 목표에 초석이 될 것으로 생각합니다.😎

# 앞으로 계획과 마무리
지금까지 하쿠나 iOS 프로젝트 모듈화 작업의 1, 2단계 과정을 소개했습니다. 

기능개발만 하면서 느낄수 없던 프로젝트 구성의 중요성을 많이 느낀 작업들 이였습니다.

앞으로도 하쿠나 iOS팀에서는 개발 생산성을 위해 유저스토리별 테스트앱을 빌드할 수 있는 모듈을 구성하는 목표를 가지고 하나씩 하나씩 개선해 나가려고 합니다. 많은 응원 부탁드립니다.💪

다음 포스트에서 이후 작업들을 꼭 소개했으면 좋겠습니다.😀

지금까지 긴 글 읽어 주셔서 감사합니다.🙏

# Reference

- [Tuist](https://github.com/tuist/tuist)

- [Tuist Doc](https://docs.tuist.io/tutorial/get-started)

---
layout: post
date: 2022-01-17
title: React Native에서 iOS 빌드 퍼포먼스 최적화
author: matt.y
tags: react-native iOS pod optimization
excerpt: React Native에서 iOS 빌드 시 pod 캐시를 이용하여 빌드 최적화한 경험을 소개합니다.
last_modified_at: 2022-01-17
---

저희 팀은 React Native(이하 RN)로 프로덕트를 만들고 있습니다. RN이 멀티플랫폼 라이브러리이다 보니 iOS와 Android를 동시에 빌드하고 QA를 진행해야 하는 경우가 많았습니다.

그런데 Android가 빌드 시간이 약 1분 30초인데 반해, iOS는 약 7분 정도 소요됐습니다. 이에 따라 iOS 빌드 개선이 필요했고, 결론적으로 일부 iOS 빌드 캐시를 이용하여 빌드 속도를 약 4.5배 개선했습니다. 저희가 어떻게 문제를 해결했는지 소개해보겠습니다.

# 문제 파악

기존 빌드 시스템의 가장 큰 문제는 cocoapods라고 하는 iOS 의존성 매니저의 캐시를 이용하고 있지 않다는 것이었습니다. 저희가 빌드할 때 사용하는 머신은 ec2로 떠 있는 mac instance이고 항상 같은 머신을 사용하지만 빌드를 돌릴 때마다 머신에 있는 프로젝트 repo를 지웠다가 다시 clone하는 형태였습니다. 그러다 보니 cocoapods가 관리하는 package들을 pod라고 하는데 매번 지웠다가 다시 설치해야 했으므로 많은 시간이 소요되고 있었습니다.

# 캐시 저장

그래서 pod의 캐시를 적용을 시도했습니다. 저희는 iOS, android 를 동시에 빌드 스크립트를 실행하기 위해 [fastlane](https://fastlane.tools/)를 사용하고 있었습니다. Xcode는 default로 DerivedData라는 폴더에 빌드 캐시를 저장하고 있었고, fastlane에서 이 경로를 derived_data_path로 지정해줄 수 있었습니다.

```ruby
...
# gym은 fastlane에서 지원하는 빌드 메소드
gym(
 # ...나머지 속성들
 scheme: SCHEME,
 workspace: PROJECT_PATH + "/#{SCHEME}.xcworkspace",
 # ios_derived_data_path: 빌드 캐시를 저장할 경로
 derived_data_path: ios_derived_data_path,
 clean: true,
)
...
```

위와 같이 빌드 캐시를 특정 위치에 저장하고, 머신에 접속했더니 다음과 같은 경로에 pod 캐시가 저장되었음을 확인할 수 있었습니다.

```ruby
ios_derived_data_path + "/Build/Intermediates.noindex/ArchiveIntermediates/#{SCHEME}.Staging/BuildProductsPath/Staging-iphoneos"
```

- ec2 머신에 저장한 pod 캐시
![pod-cache]({{ "/assets/2022-01-17-rn-ios-build-optimization/pod-cache.png" | absolute_url }})

이제 빌드할 프로젝트의 pod가 pod 캐시에 존재한다면 캐시를 사용하고 아니라면 새로운 캐시를 생성하는 일만 남았습니다.

# 캐시 hit

github action을 쓰는 대부분의 경우 [actions/cache](https://github.com/marketplace/actions/cache)를 쓰면 지정된 키로 개발자가 지정한 경로에 캐시를 남기고 키가 맞지 않는다면 오래된 캐시는 지우고 새로운 캐시를 남깁니다.

하지만 저희의 경우 github enterprise를 사용하고 있어 위 플러그인을 사용할 수 없었습니다. 그래서 캐시를 직접 구현해야겠다고 생각했고, 캐시를 남기는 폴더명을 Podfile.lock의 hashsum 값으로 이용하기로 했습니다.

```ruby
cache_key = Digest::SHA256.file "#{PROJECT_PATH}/Podfile.lock"
# ec2에 저장할 path와 폴더 이름
ios_derived_data_path = File.absolute_path("../.local_derived_data/Staging-#{cache_key}")
cache_folder = ios_derived_data_path + "/Build/Intermediates.noindex/ArchiveIntermediates/#{SCHEME}.Staging/BuildProductsPath/Staging-iphoneos"
```

fastlane은 ruby를 사용하고 있기 때문에 위와 같이 Digest 모듈을 사용해 hash를 계산하였습니다. 그래서 Podfile.lock이 변경된 경우에는 cache_key 값이 달라지도록 설계했습니다.

```ruby
# 위 코드에서 구한 cache_folder 값 이용
if(File.exist?(cache_folder))
 gym(
 # ...나머지 속성들
 clean: false,
 project: XCODE_PROJECT,
 scheme: "#{SCHEME}.Staging",
 configuration: "Staging",
 xcargs: [
 # xcode가 pods를 찾지 못하는 경우 path를 제공
 "PODS_CONFIGURATION_BUILD_DIR=#{cache_folder}",
 "FRAMEWORK_SEARCH_PATHS='#{cache_folder} $(inherited)'",
 "LIBRARY_SEARCH_PATHS='#{cache_folder} $(inherited)'",
 "SWIFT_INCLUDE_PATHS=#{cache_folder}",
 "HEADER_SEARCH_PATHS='#{cache_folder} $(inherited)'"
 ].join(" "),
 )
else
 # cache hit 실패 시 기존 캐시 삭제
 FileUtils.rm_rf Dir.glob(File.absolute_path("../.local_derived_data/Staging-*"))
 gym(
 # ...나머지 속성들
 scheme: "#{SCHEME}.Staging",
 workspace: WORKSPACE,
 derived_data_path: ios_derived_data_path,
 clean: true,
 )
end
```

Podfile.lock이 달라져 기존의 캐시와 해시값이 다른 경우는 기존 캐시를 삭제했습니다. Podfile.lock이 변경되고 이전에 있던 파일과 같아질 확률은 극히 낮다고 생각했기 때문입니다.

캐시 hit에 성공한 경우 기존에 설치했던 workspace 내부의 파일들을 사용할 수 있기 때문에 xcode project 파일을 사용했고, 실패한 경우는 기존의 파일들을 사용할 수 없기 때문에 xcode workspace 파일을 사용했습니다.

또 위에서 캐시 파일에 Staging처럼 build config를 붙인 이유는 Staging은 QA팀에서 자주 확인하기 때문에 Podfile.lock이 자주 바뀔 수 있지만, Production은 자주 바뀌지 않기 때문에 캐시를 따로 남겼습니다.

# 개선 효과 및 회고

빌드 시간이 아래 사진처럼 7분 -> 1분 30초로 약 4.5배 개선되었습니다.

- 개선 이전 빌드 시간

![before-build-time]({{ "/assets/2022-01-17-rn-ios-build-optimization/before-build-time.png" | absolute_url }})

- 개선 이후 빌드 시간

![after-build-time]({{ "/assets/2022-01-17-rn-ios-build-optimization/after-build-time.png" | absolute_url }})

저희 팀 같은 경우 서비스를 오픈한지 얼마 되지 않아 Staging, Production을 배포해야 하는 경우가 많았습니다. 그때마다 오랜 시간을 허비하며 빌드를 했었고, 빼놓은 코드가 있다면 다시 오랜 시간을 반복해야 하는 문제점이 있었습니다. 이번 개선을 통해 더 잦은 배포를 할 수 있게 되었습니다.

# Reference

[1] [https://dev.to/retyui/react-native-how-speed-up-ios-build-4x-using-cache-pods-597c](https://dev.to/retyui/react-native-how-speed-up-ios-build-4x-using-cache-pods-597c)

[2] [https://ruby-doc.org/stdlib-2.5.1/libdoc/digest/rdoc/Digest.html](https://ruby-doc.org/stdlib-2.5.1/libdoc/digest/rdoc/Digest.html)

[3] [https://developer.apple.com/library/archive/featuredarticles/XcodeConcepts/Concept-Workspace.html](https://developer.apple.com/library/archive/featuredarticles/XcodeConcepts/Concept-Workspace.html)

[4] [https://vojtastavik.com/2018/09/02/what-is-inside-derived-data-xcode/](https://vojtastavik.com/2018/09/02/what-is-inside-derived-data-xcode/)

---
layout: post
date: 2020-08-13
title: WebRTC Library 다루기
author: terry.k
tags: webrtc
excerpt: WebRTC 모바일 라이브러리를 사용하는 것에 대해서 이야기 합니다.
last_modified_at: 2020-08-13
---

WebRTC는 웹 브라우저 상에서 실시간 커뮤니케이션을 가능하도록 설계된 API 및 스펙입니다.

구현체로는 Google Chrome 에 들어가는 libwebrtc가 있으며, 이 라이브러리에서 C++ 기반 API 및 모바일 (Android / iOS 등)에서 사용 가능한 API를 제공합니다.

libwebrtc는 Chrome 내의 다른 컴포넌트와 마찬가지로 Trunk Based 개발로 진행이 되고 있으며, 6주 단위의 Chrome Release 주기에 맞추어서 Branching 을 하고 안정화 한 후에 버전 이름을 붙이고 있습니다.

> 예를 들어, Chrome 80 (2020년 2월 4일 출시) 에 들어가는 libwebrtc 의 버전은 m80으로 부르고 있습니다.

Hyperconnect의 WebRTC Engine 팀에서는 libwebrtc 프로젝트의 릴리즈 브랜치를 Fork한 후에 수정해서 사용하고 있습니다.

릴리즈 브랜치를 사용하면 안정된 브랜치 상에서 작업할 수 있다는 장점이 있으나, 해당 버전의 Chrome이 안정화 된 이후에는 추가적인 업데이트가 이루어지지 않는다는 단점이 있습니다.

이를 극복하기 위해서 WebRTC Engine 팀에서는 최신 수정사항 중 유용한 사항을 Backport 해서 내부 저장소에 적용하고 있고, 이 과정을 소개해드리고자 합니다.

## WebRTC 릴리즈 브랜치

개발 환경 구성에 필요한 chromium depot_tools 을 설치하고, 팀에서 사용하는 WebRTC 소스 코드를 받아 컴파일하여 모바일 라이브러리 배포가 가능한 환경을 구축했습니다.

개별적으로 직접 원본 저장소에서 WebRTC 소스 코드를 받아 개발 환경을 구성하였다면, master branch 를 기준으로 최신 커밋이 반영되어 있을 것입니다.

안정된 릴리즈 브랜치로 이동해 작업하도록 해야 합니다.

리모트 브랜치 목록 보기 
`$ git branch -r `

브랜치 목록에서 안정된 릴리즈 브랜치를 선택하여 작업하시면 됩니다.
`$ git checkout -b {MY_WEBRTC_BRANCH}`

discuss-webrtc 포럼에서 브랜치 이름 변경에 대해 확인해보면, m80 부터는 브랜치 번호를 사용한다고 합니다.

> There is changes for the branch name after chromium m79, rather being refs/branch-heads/m$MILESTONE branches will now be refs/branch-heads/$BRANCH_NUMBER.
[https://groups.google.com/forum/#!topic/discuss-webrtc/JR7fsoEuqw0](https://groups.google.com/forum/#!topic/discuss-webrtc/JR7fsoEuqw0)

chromium dash에서 MILESTONE, BRANCH_NUMBER를 확인할 수 있습니다.
[https://chromiumdash.appspot.com/branches](https://chromiumdash.appspot.com/branches)

![chromiumdash-branches]({{"/assets/2020-08-13-webrtc-library/01-chromiumdash-branches.png"}})

### WebRTC 업데이트 확인

**Repository**
- Source code : [https://webrtc.googlesource.com/src](https://webrtc.googlesource.com/src)

**References**
- Mailing list : [http://groups.google.com/group/discuss-webrtc](http://groups.google.com/group/discuss-webrtc)
- Issue tracker : [https://bugs.webrtc.org](https://bugs.webrtc.org/)
- Release Notes : [https://webrtc.github.io/webrtc-org/release-notes](https://webrtc.github.io/webrtc-org/release-notes)


discuss-webrtc 포럼이나 Issue tracker 사이트를 통해 원하는 주제에 연관된 이슈를 직접 확인할 수 있으며, Release Notes에서 기능 개선, 버그 패치 등의 수정사항과 commit log 를 볼 수 있습니다.
새로운 릴리즈에서 필요한 개선사항이나 유용한 기능이 있으면 반영을 검토해보게 됩니다. 아래는 최근 릴리즈된 WebRTC M85 Release Notes 입니다.

![M85ReleaseNotes]({{"/assets/2020-08-13-webrtc-library/02-M85-Releasenotes.png"}})

Commit log for the branch: [https://webrtc.googlesource.com/src/+log/branch-heads/4183](https://webrtc.googlesource.com/src/+log/branch-heads/4183)

## WebRTC 변경사항 반영하기

m78 릴리즈 브랜치에서 작업 환경을 구축하고, m80 릴리즈 브랜치에서 Stats 관련 수정사항을 적용해보려고 합니다.

먼저 WebRTC M80 Release Notes 를 열고, Features and Bugfixes 에서 아래 항목을 확인했습니다.

![M80ReleaseNotes]({{"/assets/2020-08-13-webrtc-library/03-M80-Releasenotes.png"}})

- Type: Bug
- Issue: [11108](http://bugs.webrtc.org/11108)
- Description: Add totalInterFrameDelay to RTCInboundRTPStreamStats
- Component: Stats

Issue 링크를 눌러 아래와 같이 comment와 함께 이슈 내역을 확인할 수 있고,

![issue]({{"/assets/2020-08-13-webrtc-library/04-issue.png"}})

commit hash 값과 함께 코드 변경 내용을 확인할 수 있습니다.

![commit]({{"/assets/2020-08-13-webrtc-library/05-commit.png"}})

해당 commit hash 를 통해 선택적으로 원본 저장소로부터 작업 중인 내부 저장소에 적용할 수가 있습니다.

별다른 문제없이 내부 코드에 병합을 완료했다면 컴파일 및 테스트를 해야 합니다.

libwebrtc 프로젝트에서는 이미 모바일 라이브러리 생성을 위한 스크립트를 제공하고 있습니다.

* [안드로이드용 AAR 라이브러리를 생성하는 스크립트](https://source.chromium.org/chromium/chromium/src/+/master:third_party/webrtc/tools_webrtc/android/build_aar.py)

* [iOS용 빌드 스크립트](https://source.chromium.org/chromium/chromium/src/+/master:third_party/webrtc/tools_webrtc/ios/build_ios_libs.py)

수정한 코드를 WebRTC 프로젝트에 포함되어있는 예제인 [AppRTC Android](https://webrtc.googlesource.com/src/+/refs/heads/master/examples/androidapp) 에서 간단하게 확인해 보겠습니다.

> 만약 iOS 에서 테스트를 한다면, examples/objc/AppRTCMobile/ARDAppClient.m 파일의 setShouldGetStats 함수 내부에서 statisticsWithCompletionHandler 를 사용하도록 변경하시면 됩니다.

Stats 관련해서 PeerConnection 의 네트워크 상태, 미디어 품질에 대한 데이터를 수집하는 두 개의 통계 수집기가 있습니다.

PeerConnectionClient.java 파일의 getStats() 함수에서 Legacy Stat 을 사용하는 것을 Standard Stat으로 변경하여 표준화된 버전의 통계 API를 사용합니다. [Identifiers for WebRTC's Statistics API](https://w3c.github.io/webrtc-stats/)

```java
// examples/androidapp/src/org/appspot/apprtc/PeerConnectionClient.java

private void getStats() {
    if (peerConnection == null || isError) {
      return;
    }

    /*
     * Legacy Stat
     *
    boolean success = peerConnection.getStats(new StatsObserver() {
      @Override
      public void onComplete(final StatsReport[] reports) {
        events.onPeerConnectionStatsReady(reports);
      }
    }, null);
    if (!success) {
      Log.e(TAG, "getStats() returns false!");
    }
     */

    /*
     * Standard Stat
     */
    peerConnection.getStats(new RTCStatsCollectorCallback() {
      @Override
      public void onStatsDelivered(RTCStatsReport rtcStatsReport) {
        for (RTCStats value : rtcStatsReport.getStatsMap().values()) {
          Log.e(TAG, value.getType() + " : " + value.getMembers().toString());
        }
      }
    });
  }
```

안드로이드 스튜디오에서 빌드 및 실행하고 연결 테스트를 진행하면 수집된 통계 로그를 보게 됩니다.

RTCStats Type 을 보면 transport, candidate-pair, local-candidate, remote-candidate, track, inbound-rtp, outbound-rtp 등 로그 출력에 많은 항목이 보일 텐데 이 중에서 `inbound-rtp` 에서 적용 결과를 확인할 수 있었습니다.

```
07-07 15:27:45.735 27570 28448 D PCRTCClient: 
inbound-rtp : {
	ssrc=3665707108, 
	isRemote=false, 
	mediaType=video, 
	kind=video, 
	trackId=RTCMediaStreamTrack_receiver_3, 
	transportId=RTCTransport_0_1, 
	codecId=RTCCodec_0_Inbound_96, 
	firCount=0, 
	pliCount=0, 
	nackCount=0, 
	qpSum=7489, 
	packetsReceived=2862, 
	bytesReceived=2969921, 
	packetsLost=0, 
	lastPacketReceivedTimestamp=2928324.834, 
	fractionLost=0.0, 
	framesDecoded=464, 
	totalDecodeTime=4.953, 
	totalInterFrameDelay=15.478999999999996, 
	totalSquaredInterFrameDelay=0.5424270000000003
}
```

작업 결과로 totalInterFrameDelay, totalSquaredInterFrameDelay 필드가 추가된 값이 출력되고 있습니다.

### 마무리

WebRTC 라이브러리를 수정하고, 모바일 라이브러리로 빌드하여 적용하는 과정을 간략하게 살펴 보았습니다.

Hyperconnect 에서는 연결 속도 및 미디어 품질, 사용자 경험을 위해서 WebRTC Engine을 다양한 형태로 개선하고 있습니다.

C++을 능숙하게 다루시면서, 네트워킹과 멀티미디어를 이해하고 계시고, 모바일 플랫폼을 다룰 수 있는 분들을 환영합니다.

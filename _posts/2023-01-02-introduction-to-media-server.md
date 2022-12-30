---
layout: post
date: 2023-01-02
title: 글로벌 라이브 스트리밍을 지탱하는 하이퍼커넥트 미디어 서버 인프라를 소개합니다
author: simon.y
tags: media-server infra webrtc
excerpt: 하이퍼커넥트의 글로벌 라이브 스트리밍 플랫폼 서비스의 기반이 되는 미디어 서버 인프라를 구조적인 측면에서 소개합니다.
last_modified_at: 2023-01-02
---

안녕하세요, 하이퍼커넥트 Media Lab의 Media Server Team에서 Media Server Engineer로 일하고 있는 Simon.Y 입니다.\
2023년 새해에도 독자 여러분께 행복이 가득하기를 바랍니다.

많은 분들께서 알고 계시듯 하이퍼커넥트에서는 **[하쿠나 라이브(Hakuna Live)](https://hakuna.live/)**, **[아자르 라이브(Azar Live)](https://azarlive.com/), [엔터프라이즈(Enterprise)](https://hce.io/)** 등을 통해 WebRTC 기반 글로벌 라이브 스트리밍 플랫폼을 서비스하고 있습니다.

혹시 여러분께서는 하쿠나 라이브나 아자르 라이브에서의 대규모 실시간 스트리밍 서비스를 제공하는 서버가 어떻게 구성되어 있는지 생각해보신 적이 있나요?
일반적으로 HTTP 등의 비상태(stateless) 프로토콜은 일회성으로 요청을 처리하고 응답합니다.
그러나 WebRTC는 끊임없이 연결이 유지되어 요청을 처리하는 상태유지(stateful) 프로토콜입니다.
따라서 WebRTC를 이용하여 라이브의 시작부터 종료까지 미디어 스트리밍을 제공하는 서버는 확장성 측면에서 일반적인 시스템 구성과는 다른 전략이 필요합니다.

저희 Media Server Team은 “사람들이 제약 없이 모여서 소통할 수 있도록 안정적인 연결을 제공하고 미디어 품질을 높이기 위해 노력한다”는 미션 아래에서 대규모 실시간 스트리밍 서비스를 지원하는 WebRTC 기반 미디어 서버를 개발하고 안정적으로 서비스할 수 있도록 세계 각지에 있는 미디어 서버 인프라를 운영하고 있습니다.

지난 글([신입이 만든 코드는 서버를 부숴.. 미디어 서버 테스터 개발기](https://hyperconnect.github.io/2022/03/04/media-server-tester.html))에서는 미디어 서버에 대한 간략한 설명과 미디어 서버의 품질을 확보하기 위한 Media Server Team의 노력을 그렸습니다.
이번 글에서는 하이퍼커넥트의 라이브 스트리밍 서비스들을 지탱하고 있는 WebRTC 기반 미디어 서버 인프라를 좀 더 구체적으로 소개하고자 합니다.


# WebRTC 기술에 대한 이해

하이퍼커넥트의 미디어 서버 인프라를 소개하기에 앞서 WebRTC 기술을 간단하게 설명하고자 합니다.

WebRTC는 Web Real-Time Communication이라는 이름에서 볼 수 있듯이, 웹에서의 실시간 미디어(오디오, 비디오)와 데이터 통신을 위해 제안된 기술입니다.
특히 WebRTC는 사용자가 어떠한 네트워크 환경에 있더라도 최대 수백 밀리초(ms) 이내에 상호작용(interactive)이 일어날 수 있도록 설계되었습니다.
WebRTC는 모든 네트워크에서의 실시간 저지연성을 실현시키기 위해 RTP, ICE 기반 기술들을 구현하고 있습니다.
다만, 이 글에서는 WebRTC의 세부적인 기술에 대한 구체적인 설명은 생략하고 연결 방식을 위주로 개략적으로 설명하겠습니다.
WebRTC 기술을 조금 더 자세하게 알고 싶으신 분은 페이지 아래 참고자료의 RFC 메모[[1, 2, 3]](#참고자료)를 참조하시면 좋을 것 같습니다.


<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2023-01-02-introduction-to-media-server/01-peerconnection.png" | absolute_url}}' alt='그림 1. Alice와 Bob은 시그널링 서버를 통해 세션정보를 교환하여 맺은 PeerConnection으로 서로 연결되어 있다.'>
  <figcaption>그림 1. Alice와 Bob은 시그널링 서버를 통해 세션정보를 교환하여 맺은 PeerConnection으로 서로 연결되어 있다.</figcaption>
</figure>

WebRTC 기술을 이용하여 두 사용자 Alice와 Bob이 1:1 비디오 대화를 한다면 Alice와 Bob은 서로 어떻게 연결되어 있을까요?
두 사용자 Alice와 Bob이 WebRTC 기술을 통해 연결되어 있는 모습을 그림 1에서 개략적으로 표현하였습니다.
WebRTC에서는 ICE, RTP/RTCP, DTLS 등의 프로토콜이 복합적으로 연계되어 있는 양방향 연결인 **PeerConnection**을 통해 두 사용자를 직접적으로 연결하고 있습니다.
연결된 두 사용자는 PeerConnection을 통해 오디오나 비디오 등의 미디어를 전송하고, 필요하다면 DataChannel을 생성하여 미디어 이외의 데이터를 전송합니다.
다만, 최초에 두 사용자를 PeerConnection으로 연결시키기 위해서는 IP, 포트, 미디어 코덱 등의 세션정보를 교환할 필요가 있습니다.
여기서 두 사용자 사이에서 PeerConnection을 맺기 위한 세션정보를 교환해주는 서버인 **시그널링 서버**의 도움을 받아 두 사용자가 세션정보를 교환할 수 있습니다.
참고로 시그널링 서버에서 세션정보를 교환하는 기술에 대한 표준은 존재하지 않으며 WebSocket, STOMP, gRPC 등 다양한 방식으로 구현되고 있습니다.
Alice와 Bob이 시그널링 서버를 통해 PeerConnection을 맺는 과정은 일반적으로 다음과 같이 Offer/Answer 모델[[4]](#참고자료)에 따라 이뤄집니다.

1. Alice가 Bob에게 자신의 IP, 포트, 지원 가능한 미디어 코덱 등의 세션정보를 시그널링 서버를 통해 전달(Offer)합니다.
2. Bob은 전달받은 Alice의 세션정보를 바탕으로 PeerConnection을 맺을 준비를 합니다.
3. Bob은 연결 가능한 자신의 IP, 포트, 미디어 코덱 등의 세션정보를 시그널링 서버를 통해 Alice에게 전달(Answer)합니다.
4. Alice는 전달받은 Bob의 세션정보를 바탕으로 PeerConnection을 맺습니다.
5. Alice와 Bob은 PeerConnection을 통해 서로에게 미디어를 전송할 수 있습니다.

이와 같은 과정으로 WebRTC 기술을 통해 두 사용자를 직접 연결하여 아자르와 같은 1:1 비디오 대화를 할 수 있습니다.


# 미디어 서버의 필요성

한 사용자의 미디어를 여러 사람이 시청할 수 있는 1:N 스트리밍 환경을 구성하기 위해 어떤 기술을 사용해야 할까요?

여러 동영상 스트리밍 플랫폼들에서 주로 이용하는 방식은 동영상을 수초 간격의 매우 작은 동영상들로 분할하여 HTTP로 제공하는 기술인 HLS(HTTP Live Streaming)입니다.
HLS는 널리 퍼진 기술이라는 장점이 있으나 호스트가 미디어를 송출한 때부터 수초에서 수십초의 지연 시간(delay)이 발생한다는 단점이 있습니다.
하이퍼커넥트에서도 HLS 기술을 지원하고 있지만, 하쿠나 라이브의 게스트 모드나 아자르 라이브의 배틀 모드 등 여러 호스트가 모여 라이브하는 즐거운 경험을 제공하기 위해서는 WebRTC의 저지연성이 필요합니다.

그렇다면 WebRTC 기술을 이용하여 1:N 스트리밍 환경을 구성하려면 어떻게 해야할까요?
다음과 같이 Alice의 라이브를 Bob, Charlie, David, Eve가 시청하는 상황을 가정해봅시다.

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2023-01-02-introduction-to-media-server/02-p2p.png" | absolute_url}}' alt='그림 2. Alice와 Bob, Alice와 Charlie, Alice와 David, Alice와 Eve가 서로 각각 PeerConnection을 맺어 Alice의 라이브를 시청하고 있다.'>
  <figcaption>그림 2. Alice와 Bob, Alice와 Charlie, Alice와 David, Alice와 Eve가 서로 각각 PeerConnection을 맺어 Alice의 라이브를 시청하고 있다.</figcaption>
</figure>

우선, 그림 2처럼 Alice와 Bob, Alice와 Charlie, Alice와 David, Alice와 Eve가 각각 PeerConnection을 맺고, 동일한 Alice의 라이브 미디어를 Bob, Charlie, David, Eve에게 전달하는 방법을 생각해볼 수 있습니다.
이러한 방법은 경유지 없이 시청자가 Alice와 직접 연결되어 있으므로 단순하면서도 가장 짧은 지연 시간(latency)으로 Alice의 라이브를 시청할 수 있다는 장점이 있습니다.
그러나 Alice에게 연결되는 PeerConnection과 미디어를 전송하는 네트워크 트래픽이 시청자 수에 비례하여 늘어난다는 결점이 있습니다.
모바일 단말로 라이브를 스트리밍하여 수천, 수만 명이 시청하는 하쿠나 라이브, 아자르 라이브와 같은 서비스에서는 이러한 구조가 호스트에게 감당할 수 없는 부담(단말 배터리 소모, 데이터 요금 등)을 안겨주기 때문에 다른 방법을 고려해야 합니다.

다른 방법으로는 호스트의 라이브 미디어를 수신하여 시청자들에게 전달하는 (확장 가능한) 중계 서버를 구축하는 것을 생각해볼 수 있습니다.
즉, <sup>(1)</sup>호스트는 중계 서버와 PeerConnection을 맺고 <sup>(2)</sup>시청자들도 각각 중계 서버와 PeerConnection을 맺은 뒤 <sup>(3)</sup>중계 서버가 호스트로부터 받은 라이브 미디어를 시청자들과 맺은 PeerConnection으로 전송하는 것입니다.
이 방법은 호스트에게 집중되었던 부담을 중계 서버로 옮겨오게 하여 모바일 단말을 이용하는 호스트와 시청자들에게 우수한 사용자 경험을 줄 수 있습니다.
다만, 중계 서버의 세션 관리와 확장성이 라이브 스트리밍 서비스의 실시간성과 네트워크 품질에 크게 영향을 미치기 때문에 중계 서버를 주의하여 설계할 필요가 있습니다.
한편, 시그널링 서버는 사용자와 사용자 간 PeerConnection을 위한 세션정보를 교환하는 역할이 아니라 사용자와 중계 서버 간 PeerConnection을 위한 세션정보를 교환하는 역할을 하게 됩니다.
따라서 사용자와 PeerConnection을 직접 맺고 사용자 세션 관리를 담당하고 있는 중계 서버와 시그널링 서버를 통합하여 운영할 수 있습니다.
이렇게 호스트의 라이브 미디어를 시청자들에게 전달하는 미디어 스트리밍 서버를 **미디어 서버**라고 합니다.


<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2023-01-02-introduction-to-media-server/03-media-server.png" | absolute_url}}' alt='그림 3. Alice는 라이브를 미디어 서버로 송신하고, Bob, Charlie, David, Eve는 미디어 서버를 통해 Alice의 라이브를 수신하고 있다.'>
  <figcaption>그림 3. Alice는 라이브를 미디어 서버로 송신하고, Bob, Charlie, David, Eve는 미디어 서버를 통해 Alice의 라이브를 수신하고 있다.</figcaption>
</figure>

앞서 예를 들었던, Alice의 라이브를 Bob, Charlie, David, Eve가 시청하는 상황은 미디어 서버를 도입함으로써 그림 3처럼 개략적으로 표현할 수 있습니다.
Alice가 라이브를 시작해서 Bob이 Alice의 라이브를 시청하는 과정을 그림 3을 예시로 설명하면 다음과 같습니다.

1. Alice는 미디어 서버와 세션 정보를 교환하여 미디어 서버의 수신 Peer와 PeerConnection을 맺습니다.
2. Alice는 라이브 미디어를 미디어 서버의 수신 Peer와 맺어진 PeerConnection으로 전송합니다.
3. Bob은 미디어 서버로 시청하고자 하는 라이브(Alice의 라이브)를 요청하고 세션 정보를 교환하여 미디어 서버의 송신 Peer와 PeerConnection을 맺습니다.
4. 미디어 서버는 Alice에 대한 수신 Peer에서 받은 라이브 미디어를 Bob에 대한 송신 Peer로 전달합니다.
5. Bob은 미디어 서버의 송신 Peer와 맺어진 PeerConnection을 통해 Alice의 라이브를 시청합니다.

한편, 호스트의 라이브 미디어를 시청자의 네트워크 환경에 맞춰 적절한 품질(해상도, 비트레이트 등)로 제공하는 등 여러 기능이 필요할 경우가 있습니다.
이러한 기능들을 구현하기 위해 미디어를 어떻게 전달하고 처리하는지에 따라 미디어 서버의 종류를 구분하기도 합니다.
WebRTC 기술에서 자주 보이는 미디어 서버로 **SFU (Selective Forwarding Unit)** 또는 **SFM (Selective Forwarding Middlebox)** 이라고 불리는 것이 있습니다.
SFU(또는 SFM)에서는 호스트가 저화질 버전과 고화질 버전의 라이브를 모두 생성하여 미디어 서버로 전송(simulcast 라고 합니다)합니다.
그러면 SFU는 시청자의 요청이나 네트워크 환경 등에 맞춰 호스트가 전송한 저화질과 고화질 미디어 중 하나를 선택하여 시청자에게 전송합니다.
SFU 이외에도 다양한 종류의 미디어 서버들이 있는데 조금 더 자세히 알고 싶으신 분은 아래 참고자료의 RFC 메모[[5]](#참고자료)를 참조하시면 좋을 것 같습니다.


# 미디어 서버의 수평 확장

앞에서 살펴봤듯이 미디어 서버를 도입함으로써 호스트와 시청자의 부담을 줄이는 것이 가능해졌습니다.
그러나 미디어 처리·전송에는 상당한 시스템 자원과 네트워크 자원을 소모하기 때문에 아무리 고성능이라도 서버 한 대만으로는 수천, 수만 명의 호스트와 시청자를 감당하기 어렵습니다.
따라서 대규모의 미디어 스트리밍 서비스를 위해서는 여러 대의 미디어 서버를 구성하여 수평적으로 확장할 수 있는 인프라를 구축할 필요가 있습니다.


<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2023-01-02-introduction-to-media-server/04-simple-horizontal-media-server.png" | absolute_url}}' alt='그림 4. 가장 단순한 수평 확장 전략을 사용하여 구성된 미디어 서버 인프라를 통해 Alice와 Bob이 라이브를 하고, Charlie, David, Eve, Frank가 라이브를 시청하고 있다.'>
  <figcaption>그림 4. 가장 단순한 수평 확장 전략을 사용하여 구성된 미디어 서버 인프라를 통해 Alice와 Bob이 라이브를 하고, Charlie, David, Eve, Frank가 라이브를 시청하고 있다.</figcaption>
</figure>


우선 수평 확장 측면에서 가장 먼저 떠올릴만한 미디어 서버 인프라를 그림 4에 표현해보았습니다.
그림 4는 미디어 서버 인프라를 통해 Alice의 라이브를 Charlie외 David가 시청하고 있고, Bob의 라이브를 Eve와 Frank가 시청하고 있는 상황을 보여주고 있습니다.
여기서 미디어 서버 인프라의 구성 요소인 **Media Server Broker**는 로드밸런싱과 라우팅 기능이 있는 서버입니다.
Media Server Broker는 호스트에게는 라이브를 위한 적절한 미디어 서버를 선택하여 연결시키고, 시청자에게는 호스트가 있는 미디어 서버를 선택하여 연결시키는 역할을 합니다.
이러한 구조에서 미디어 서버 인프라의 동작 방식은 다음과 같을 것입니다.

1. 호스트인 Alice가 라이브를 시작하기 위해 미디어 서버 인프라에 연결 요청(시그널링)을 합니다.
2. Media Server Broker는 가장 사용량이 적은 것으로 판단한 첫번째 미디어 서버로 Alice의 요청을 전달합니다.
3. 첫번째 미디어 서버는 수신 Peer를 만들어 Alice와 PeerConnection을 맺고, Alice의 라이브 미디어를 수신합니다.
4. 시청자인 Charlie는 호스트인 Alice의 라이브를 시청하기 위해 미디어 서버 인프라에 연결 요청(시그널링)을 합니다.
5. Media Server Broker는 Alice의 라이브가 존재하는 첫번째 미디어 서버로 Charlie의 요청을 전달합니다.
6. 첫번째 미디어 서버는 송신 Peer를 만들어 Charlie와 PeerConnection을 맺고 Alice로부터 라이브 미디어를 전달받아 송신 Peer의 PeerConnection으로 미디어를 송신합니다.

이와 같이 미디어 서버를 여러 대 구성할 수 있는 인프라 구조가 되어 더 많은 호스트가 라이브를 하고 더 많은 시청자들이 시청할 수 있게 되었습니다.
그러나 이 구조에서도 하나의 방송은 하나의 미디어 서버에 국한되어 있기 때문에 처리할 수 있는 최대 시청자 수가 제한되어 여전히 수천, 수만 명의 시청자를 감당할 수 없게 됩니다.

여기서 미디어 서버 내부에서 수신 Peer(호스트)와 송신 Peer(시청자)가 분리되어 있다는 점을 이용하여 송신 Peer를 서로 다른 미디어 서버에도 배치하는 방법을 생각해볼 수 있을 것 같습니다.
이 구조에서는 이론 상 시청자가 여러 미디어 서버에 분포되어 있기 때문에 최대 시청자 수의 한계를 극복할 수 있습니다.
그래서 초창기 미디어 서버 인프라도 이와 같은 구조로 설계되었습니다.
그러나 이 구조에서는 라이브 스트리밍 서비스의 특성으로 인하여 미디어 서버 인프라의 안정성에 한계가 발생합니다.

라이브 스트리밍 서비스에서 가장 주목할만한 특성은 호스트보다 시청자가 압도적으로 많다는 점입니다.
이 특성으로 인해 이 구조에서는 호스트의 미디어 품질이 해당 미디어 서버에 존재하는 시청자들로 인해 상당히 많은 영향을 받게 됩니다.

안정적인 라이브 제공을 위해 호스트는 라이브 시작부터 종료까지 상당히 긴 시간동안 꾸준히 좋은 품질을 유지해야 합니다.
그러나 시청자들은 짧은 시간동안만 라이브를 시청하고, 특정 라이브에 한꺼번에 몰렸다가 한꺼번에 시청을 종료하는 경우가 많습니다.
이로 인해 미디어 서버 자원 사용량이 순간적으로 피크에 도달하는 경우가 잦아지게 됩니다.
따라서 호스트(수신 Peer)와 시청자(송신 Peer)가 동일한 미디어 서버에 존재하게 되면 호스트에게 안정적인 라이브 환경을 보장해주기가 곤란하게 됩니다.
그러므로 좀 더 스마트한 수평 확장 구조를 생각해야 합니다.

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2023-01-02-introduction-to-media-server/05-origin-edge-media-server.png" | absolute_url}}' alt='그림 5. Origin-Edge 구조로 구성된 미디어 서버 인프라를 통해 Alice의 라이브를 Charlie, David, Eve가 시청하고 있고, Bob의 라이브를 Frank가 시청하고 있다.'>
  <figcaption>그림 5. Origin-Edge 구조로 구성된 미디어 서버 인프라를 통해 Alice의 라이브를 Charlie, David, Eve가 시청하고 있고, Bob의 라이브를 Frank가 시청하고 있다.</figcaption>
</figure>

라이브 스트리밍 서비스의 특성을 반영하여 설계된 **Origin-Edge 구조의 미디어 서버 인프라**를 그림 5에 표현하였습니다.
기본적인 아이디어는 미디어 서버를 Origin과 Edge로 구분하고, **Origin 미디어 서버**에는 호스트만 접속하고, **Edge 미디어 서버**에는 시청자만 접속할 수 있도록 하는 것입니다.
그림 5와 같은 Origin-Edge 구조의 미디어 서버 인프라의 동작 방식은 다음과 같습니다.

1. 호스트인 Alice가 라이브를 시작하기 위해 미디어 서버 인프라에 연결 요청(시그널링)을 합니다.
2. Media Server Broker는 가장 사용량이 적은 것으로 판단한 첫번째 Origin 미디어 서버로 Alice의 요청을 전달합니다.
3. 첫번째 Origin 미디어 서버는 Alice와 PeerConnection을 맺고 Alice의 라이브 미디어를 수신합니다.
4. 시청자인 Charlie는 호스트인 Alice의 라이브를 시청하기 위해 미디어 서버 인프라에 연결 요청(시그널링)을 합니다.
5. Media Server Broker는 가장 적절하다고 판단한 첫번째 Edge 미디어 서버로 Charlie의 요청을 전달합니다.
6. 첫번째 Edge 미디어 서버는 Alice의 라이브가 있는 첫번째 Origin 미디어 서버로부터 Alice의 라이브 미디어를 릴레이 받습니다.<br/>
만약 첫번째 Edge 미디어 서버가 이미 Alice의 라이브 미디어를 수신하고 있었다면(즉, Alice의 라이브의 시청자가 이미 있다면) 이 과정은 생략합니다.
7. 첫번째 Edge 미디어 서버는 Charlie와 PeerConnection을 맺고, 릴레이 받은 Alice의 라이브 미디어를 Charlie에게 송신합니다.

이와 같이 미디어 서버를 호스트만 접속하는 Origin과 시청자만 접속하는 Edge로 구분함으로써 호스트의 라이브를 안정적으로 제공하고 수천, 수만 명의 시청자를 소화할 수 있는 미디어 서버를 구성할 수 있게 되었습니다.


# 미디어 서버의 글로벌 확장

하이퍼커넥트의 라이브 스트리밍 플랫폼은 전세계를 대상으로 서비스되고 있습니다.
아자르 라이브를 이용해보셨다면 한국에서 미국이나 중동 지역의 라이브를 문제 없이 시청하신 경험이 있으실 겁니다.
하이퍼커넥트에서는 글로벌 저지연 라이브 스트리밍 서비스를 제공하기 위해 클라우드 서비스를 이용하여 세계 각지에 미디어 서버 인프라를 두고 있습니다.

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2023-01-02-introduction-to-media-server/06-global-cloud.png" | absolute_url}}' alt='그림 6. Amazon Web Service의 글로벌 인프라를 활용하여 라이브 스트리밍 플랫폼을 전세계를 대상으로 서비스하고 있습니다. (AWS 글로벌 인프라 홈페이지에서 갈무리)'>
  <figcaption>그림 6. Amazon Web Service의 글로벌 인프라를 활용하여 라이브 스트리밍 플랫폼을 전세계를 대상으로 서비스하고 있습니다. (출처: AWS)</figcaption>
</figure>

혹시 아주 먼 거리에 있는 외국 호스트의 라이브를 한국에서 시청하려면 어떻게 서버를 구성하고 요청을 보내면 될지 생각해보신 적이 있나요?
가장 먼저 떠올려볼만한 방법은 외국 호스트가 라이브를 하고 있는 미디어 서버 인프라에 시청자가 직접 접속하여 라이브를 시청하는 것입니다.
빛이 느려서 발생되는 지연은 어쩔 수 없지만(TMI. 이론 상 빛이 지구를 한 바퀴 돌아 같은 지점으로 되돌아오기 위해 0.134초가 걸립니다) 호스트와 시청자가 있는 국가 내, 국가 간 네트워크 품질이 양호하다면 라이브를 시청하는데 특별한 문제가 발생하지 않습니다.
한국이나 일본, 미국 등에서의 네트워크 환경은 쾌적하기 때문에 시청자가 해외에 직접 접속하여 라이브를 시청하여도 그다지 문제가 되지 않습니다.
그러나 실제로 전세계에서 미디어 서버 인프라를 운영해보면 국가별로 다양하고 특징적인 네트워크 상황이 존재하는 것을 알 수 있습니다.
예를 들어, 중동의 시청자가 한국의 미디어 서버에 직접 접속할 경우, 중동 내부, 한국-중동 간 불안정한 네트워크로 인해 라이브를 정상적으로 시청하기 어려울 때가 있습니다.
따라서 미디어 서버 인프라를 글로벌로 확장할 때 조금 더 좋은 전략을 고민할 필요가 있습니다.

<figure style="text-align: center;">
  <img style="display: block; margin: 0 auto;" data-action="zoom" src='{{"/assets/2023-01-02-introduction-to-media-server/07-global-media-server.png" | absolute_url}}' alt='그림 7. 글로벌로 확장된 미디어 서버 인프라를 통해 미국에 있는 Alice의 라이브를 한국에 있는 Eve가 안정적으로 시청할 수 있다.'>
  <figcaption>그림 7. 글로벌로 확장된 미디어 서버 인프라를 통해 미국에 있는 Alice의 라이브를 한국에 있는 Eve가 안정적으로 시청할 수 있다.</figcaption>
</figure>

그림 7은 **글로벌로 확장된 하이퍼커넥트의 미디어 서버 인프라**의 구조를 나타낸 것입니다.
글로벌로 확장된 미디어 서버 인프라에서 호스트와 시청자는 항상 자신이 있는 지역의 미디어 서버 인프라에 접속합니다.
즉, 지역을 고려하지 않았을 때와 동일하게 호스트는 자신의 지역의 미디어 서버 인프라를 통해 라이브를 하고, 시청자는 자신의 지역의 미디어 서버 인프라를 통해 라이브를 시청합니다.
여기서 달라지는 점은 호스트가 다른 지역에 있다면 시청자는 호스트의 Origin 미디어 서버(해외)로부터 시청자의 Edge 미디어 서버(국내)로 미디어를 릴레이하여 시청한다는 점입니다.

얼핏 보기에 시청자가 직접 외국에 접속하는 것과 비슷해보이지만 실제 시청자의 경험에서는 서비스 품질에서 큰 차이가 발생합니다.
먼저 응답 시간 측면에서 시청자는 시그널링이나 라이브 시청과 관련된 제어 정보에 대한 응답을 빠르게 받을 수 있습니다.
시청자가 해외가 아닌 자신의 지역에 있는 미디어 서버 인프라에 접속하고 있기 때문입니다.
그리고 미디어 품질 측면에서 시청자는 자신의 네트워크 환경에서 시청할 수 없었던 해외 호스트의 고화질 라이브를 시청할 수 있습니다.
미디어 서버 인프라가 시청자를 대신하여 고품질의 국가 간 기업 네트워크 환경에서 미디어를 전달하고 있기 때문입니다.

실제로 위와 같이 글로벌 미디어 서버 인프라를 구성하여 운영함으로써 아자르 라이브에서 큰 개선이 있었습니다.
시청자가 해외 미디어 서버 인프라에 직접 요청을 보내는 것과 비교할 때, 다음과 같은 효과를 얻을 수 있었습니다.

- 시청자가 미디어 서버 인프라에 연결하는 시간은 약 25% 감소
- 시청자와 미디어 서버 인프라 간 RTT는 약 30% 감소 (일부 지역에서는 최고 1/30 로 감소)
- 미디어 패킷 손실은 최고 80% 감소


# 마치며

이번 글에서는 하이퍼커넥트의 글로벌 라이브 스트리밍 서비스 플랫폼의 기반이 되는 미디어 서버 인프라의 구조를 자세히 살펴보았습니다.
하이퍼커넥트의 미디어 서버 인프라는 WebRTC 기술을 기반으로 Origin-Edge 구조로 설계되어 전세계에서 라이브를 송출하고 시청 가능한 확장성을 지원하고 있습니다.
미디어 서버팀에서는 앞서 살펴본 바와 같이 글로벌 인프라 운영 경험을 바탕으로 고품질의 WebRTC 기반 글로벌 라이브 스트리밍 서비스 플랫폼을 지원하고 있으며, 지금도 더욱 더 다양한 국가에서 더 많은 시청자가 쾌적한 라이브 시청을 경험할 수 있도록 미디어 서버 인프라를 개선하고 연구하고 있습니다.
참고로 미디어 서버팀에서는 1:N 환경의 라이브 스트리밍뿐만 아니라 [하이퍼커넥트 Enterprise](https://hce.io/)에서 제공하는 N:N 환경의 그룹콜을 위한 미디어 서버 인프라도 개발·운영하고 있으며, WebRTC 기술 이외에도 RTMP, HLS 기반의 미디어 서버 인프라도 개발하며 운영하고 있습니다.
다음에 미디어 서버팀의 또 다른 이야기로 찾아뵙겠다는 인사를 드리며 이 글을 마치겠습니다.


# 참고자료

1. [RFC 8825 - Overview: Real-Time Protocols for Browser-Based Applications](https://datatracker.ietf.org/doc/html/rfc8825)
2. [RFC 8835 - Transports for WebRTC](https://datatracker.ietf.org/doc/html/rfc8835)
3. [RFC 8829 - JavaScript Session Establishment Protocol (JSEP)](https://datatracker.ietf.org/doc/html/rfc8829)
4. [RFC 3264 - An Offer/Answer Model with the Session Description Protocol (SDP)](https://datatracker.ietf.org/doc/html/rfc3264)
5. [RFC 7667 - RTP Topologies](https://datatracker.ietf.org/doc/html/rfc7667)

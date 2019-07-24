---
layout: post
date: 2019-06-28
title: Google Cloud Next 2019 참관기
author: phil
tags: google cloud conference infra
excerpt: Google Cloud Next 2019 참관기입니다
last_modified_at: 2019-06-28
---


## 서론
안녕하세요. 하이퍼커넥트 백엔드실의 Phil 입니다.
“IT쟁이”들의 공통된 특징에는 어떤 것들이 있을까요? 여러 가지 답이 있을 수 있겠지만 저에게 물어본다면 “새로운 것을 배우는 것을 좋아한다”는 점을 꼽고 싶습니다. 그 어느 곳보다 변화의 속도가 빠른 업계의 특성상 학습을 게을리하는 사람은 살아남기가 힘든 것도 한 가지 원인일 겁니다.

사람마다 배우는 스타일에는 여러 가지가 있습니다. 전통적인 방식대로 책을 통해 배우는 사람이 있는가 하면, SNS를 통해 사람들과 교류하면서 그들이 언급하는 키워드 중심으로 학습을 하는 사람도 있겠죠. 
그중 가장 비용이 많이 들면서도 특별한 경험을 제공하는 것은 해외 컨퍼런스 참가일 것입니다.

해외 컨퍼런스에는 어떤 매력이 있을까요? 반복되는 일상의 업무에서 벗어나 가벼운 마음으로 IT 선진국의 공기를 체험할 수 있다는 측면도 물론 중요하겠습니다만, 한국에서는 접하기 힘든 구글, 아마존, 애플, 오라클, 마이크로소프트 등 기라성 같은 IT 리더들의 프로덕트 전략과 트렌드를 현장에서 그들과 함께 호흡하면서, 때로는 소통하면서 접할 수 있다는 점이 가장 큰 매력일 것 같습니다. 한국에서도 얼마든지 각종 미디어를 통해 간접적으로 접할 수 있다지만, 엘 클라시코 티켓이 생겼을 때 TV로 보는 게 더 편하다며 거절할 축구 팬이 과연 있을까요?

아무래도 해외 컨퍼런스 참가에는 많은 비용이 들 수밖에 없는 것이 사실입니다. 하지만 하이퍼커넥트에서는 직원들에 대한 교육 투자의 일환으로 다양한 컨퍼런스 참가를 지원하고 있습니다. 2018년 현재까지의 기록으로는 매년 전체 30% 가량의 엔지니어가 해외 컨퍼런스 참가 기회를 얻어 왔습니다.

제가 이번에 운좋게도 참가 기회를 얻게 된 컨퍼런스는 Google Cloud Next 2019 라는 컨퍼런스로, 구글에서 제공하는 클라우드 서비스인 Google Cloud Platform 관련으로 매년 개최되고 있는 컨퍼런스입니다. 장소는 각종 IT 컨퍼런스의 개최지로 유명한 샌프란시스코의 Moscone Center 였습니다.

## Anthos
컨퍼런스의 꽃인 키노트에서 단연 주목을 끈 발표 내용은 바로 Anthos 였습니다. 이미 Google Services Platform 이라는 이름으로 베타를 진행 중이었는데, 이번 발표로 이름을 바꾸며 GA 상태가 되었습니다.

Anthos 의 가장 기본이 되는 서비스는 on-premise 인프라에서 GCP의 관리형  Kubernetes 서비스인 GKE를 그대로 사용할 수 있는 GKE on-prem 입니다. 데모에서는 on-prem 뿐만 아니라 AWS 등의 타 클라우드에서도 사용할 수 있다는 내용이 공개되어 흥미를 끌었습니다만, 공식 문서에는 2019년 6월 현재 아직까지 반영이 되지 않고 있습니다.

구글 클라우드의 전략적 차원에서 Anthos 를 이해해 보자면, AWS 가 압도적인 1위를 달리고 있는 클라우드 시장에서 아직 클라우드로의 이전이 완료되지 않은 엔터프라이즈들에게 저비용으로 **인프라 현대화** 를 제공하여 점유율을 높임과 동시에, 이미 AWS 등의 경쟁 서비스의 고객을 대상으로는 Kubernetes 측면의 강점을 내세워서 멀티클라우드 전략을 적극적으로 지원함으로써 경쟁자의 파이를 빼앗아오려는 포석이 담겨 있다고 보입니다.

Anthos migrate 는 가장 마법 같은 프로덕트였습니다. 기존 on-premise VM 을 기반으로 Kubernetes 에서 기동시킬 수 있는 컨테이너 이미지를 만들 수 있는 서비스로서, 전통적인 IT 자산에 대한 투자가 많은 대기업 입장에서는 최소한의 비용 투자로 현대적인 Kubernetes 환경을 구축할 수 있다는 점이 어필할 수 있을 것으로 보입니다.

하이퍼커넥트는 대부분의 워크로드가 AWS 를 기반으로 하고 있기 때문에 Anthos 에서 가장 관심을 끈 부분은 멀티클라우드 지원이었습니다. 키노트에서 데모는 되었지만 공식 문서에는 없는 내용이라 Anthos 부스에서 직접 직원한테 문의해 봤더니, 빠른 시일 내에 출시될 예정이라는 답변을 들었습니다.

Anthos 는 시작 가격이 월 1만불로서 저렴하지는 않습니다. 하지만 Anthos 가 타겟으로 하는 회사들이라면 비용 때문에 도입을 주저하지는 않을 것으로 보입니다.
아무래도 on-premise 환경에 대한 투자가 많은 대기업을 대상으로 하는 서비스이다 보니, 시작부터 cloud-native 였던 하이퍼커넥트로서는 당장 어필하는 점이 크지는 않아 보입니다. 향후에 multi-cloud 지원이 보편화되면 다시 고려해 볼 수도 있을 것 같습니다.


## Kubernetes, Kubernetes, Kubernetes
이번 Google Cloud Next 에서 느낀 점은, Kubernetes 가 이제 돌이킬 수 없는 업계의 대세가 되어 버렸다는 점입니다. Anthos 에서도 강조된 키워드는 **인프라 현대화(Infrastructure modernization)** 였습니다. 여기서 현대화란 **Kubernetes 화** 를 당연히 포함할 정도로, Kubernetes 도입은 이제 선택의 문제가 아니라 시기의 문제가 되어 버린 느낌입니다. OpenShift, CloudFoundry 등의 PaaS 서비스들도 신버전에서는 일제히 기존 방식을 버리고 Kubernetes 위에 레이어링으로 동작하는 것만 봐도 Kubernetes 가 대세라는 것을 알 수 있습니다. 이제는 감히 Kubernetes 가 아닌 것은 legacy 라고 단언해도 될 법한 분위기입니다. 설령 Kubernetes 자체의 장점을 크게 못 느끼더라도 앞으로 쏟아져 나올 Kubernetes 기반의 각종 도구를 사용하려면 어쩔 수 없이 도입할 수밖에 없을 것으로 예상됩니다.

그렇다면 왜 모든 사람이 Kubernetes 에 열광하고 있을까요? Docker 가 보여준 컨테이너의 가능성을 오늘날의 마이크로서비스 환경에서 실제로 구현하기 위해서는 여러 컨테이너를 효율적으로 조직(orchestrate)하는 방법이 필요했었는데, DC/OS, Swarm 등의 경쟁자를 물리치고 컨테이너 오케스트레이션 플랫폼 전쟁에서 살아남은 플랫폼이 바로 Kubernetes 였기 때문입니다. 네트워크 효과의 특성상 승자독식이 될 수밖에 없는 상황에서 일부 niche 케이스를 제외하고는 이제 대세를 돌이키기는 힘들 것으로 보입니다.
이런 상황에서, Kubernetes 에 가장 큰 지분을 가지고 있고, 3대 클라우드 서비스 중 가장 성숙한 Kubernetes 지원을 자랑하는 구글 클라우드로서는 더더욱 전략적으로 Kubernetes 를 내세울 수밖에 없겠다는 생각이 듭니다.


## AI 기술의 commodity 화
또 하나 느낄 수 있었던 점은, AI 기술 중 많은 부분이 이제는 commodity 화 되어 가고 있다는 점입니다. 이미 구글 클라우드의 많은 ML기반 API를 대량으로 사용하고 있을 뿐만 아니라 우수한 자체 ML 팀도 보유하고 있는 하이퍼커넥트입니다만, 이제 ML practitioner 가 아니라는 이유로 ML 과 상관없다고는 말하기 힘든 상황이 되었습니다. 데이터만 제공하면 모델을 스스로 설계하고 배포까지 해 주는 구글 클라우드의 AutoML 서비스는 이번에 추가된 AutoML Video 기능을 통하여 동영상 classification 도 수행할 수 있게 되었습니다. Video & AI 기반 기술회사를 지향하는 하이퍼커넥트로서는 관심이 가는 신기능이 아닐 수 없습니다. 뿐만 아니라 BigQuery 에서도 분석가들이 엔지니어의 도움 없이 기본적인 ML 학습을 통해 모델을 만들어 classification 에 활용할 수 있으니, 가히 **ML 의 민주화** 라고 할 만합니다.

## 그 외 인상깊었던 세션
* [Implementing GCP Stackdriver and Adapting SRE Practices to Samsung’s AI System](https://www.youtube.com/watch?v=45UoGDxuwto)

    알 만한 사람들은 다 아는 클라우드 헤비유저인  삼성전자에서도 DevOps 관련 세션을 준비했습니다. 하이퍼커넥트에 큰 도움을 주고 계신 구글 코리아의 Terry 님이 같이 발표하신다니 더더욱 들을 수밖에 없었습니다.  삼성의 빅스비 서비스에서 Stackdriver / Cloud Dataflow 를 이용하여 로그 집중화와 모니터링 시스템을 구현한 경험을 소개해 주셨습니다. 하이퍼커넥트에서도 Stackdriver 를 많이 활용하고 있고 앞으로 더 많이 사용할 예정입니다. 로그 집중화를 고민하고 계신 분이라면 Stackdriver 를 꼭 고려해 보시기 바랍니다.

* [Canary Deployments With Istio and Kubernetes Using Spinnaker](https://www.youtube.com/watch?v=CmZWau04ZS4)

    하이퍼커넥트에서도 canary 배포를 종종 활용하고 있는 편입니다만, 매뉴얼하게 일부 배포 후 간단한 이상 여부만 체크한 다음 전체 배포를 하는 단순화된 워크플로우였습니다. 이 세션에서는 Istio 의 세밀한 트래픽 제어를 활용하여 비교군 / 대조군을 완벽하게 동일한 조건으로 나누어 배포한 후 카나리 분석을 통계적으로 엄밀하게 수행하며, 더군다나 분석을 포함한 전 과정을 spinnaker 를 통해 자동화하는 방법을 소개해 주고 있었습니다. 향후 카나리 배포의 고도화 과정에서 충분히 참고할 만한 내용이었습니다.
    
* [Connected Vehicles as Air Quality Sensors: Powered by BigQuery GIS](https://www.youtube.com/watch?v=jzHvVw_XDIU)

    존재하는지도 몰랐던 BigQuery GIS 기능에 이끌려 신청한 세션입니다. 환경 정보 관련 회사들이 공공기관의 차량을 이동식 공기질 센서로 활용하여 커버리지를 늘리고, 그 센서들이 수집한 데이터를 BigQuery GIS 를 이용하여 분석하였다는 내용입니다. 미세먼지에 시달리는 한국인으로서는 관심을 가질 수밖에 없는 내용이었습니다.

## 결론
AWS 를 주력으로 사용하고 있지만 GCP 에도 만만찮은 투자를 하고 있는 하이퍼커넥트의 일원으로서, 처음 참관하는 Google Cloud Next 는 인상깊은 경험이었습니다. 주최측의 전략에 동의하든 동의하지 않든 그들이 제시하는 새로운 시각으로 우리가 당면한 문제를 바라볼 수 있고, 우리가 알고 있었던 문제들 뿐만 아니라 존재하는지도 몰랐던 문제들에 대해 먼저 고민한 경험을 공유하기 위해 세계 각지에서 모여든 사람들과 직접 소통할 수 있다는 점은 컨퍼런스만이 가지고 있는 매력이 아닌가 합니다.
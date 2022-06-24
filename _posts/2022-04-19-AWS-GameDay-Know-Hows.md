---
layout: post
date: 2022-04-19
title: AWS 대회 2관왕한 사람이 푸는 우승 Know-Hows
author: james.b
tags: security aws Gameday ctf 
excerpt: AWS Gameday 에 참가해 우승했던 후기를 공유합니다.
last_modified_at: 2022-04-19
---

안녕하세요😎  HyperConnect Security Team에서 Security Engineer로 일하고 있는 James.B 입니다. 

지난해, 2021년 11월에는 AWS Gameday 가 2회(AWS AI/ML Gameday ASEAN, AWS Microservice Gameday Korea) 개최되었습니다.

Chihuahua or Muffin 팀(AWS DNA 3기 멤버) 와 dj?! 팀(Hyperconnect Security Team)으로 각 대회에 참여하여 2관왕을 차지했습니다.

두 개의 AWS Gameday가 어떤 Concept를 가진 대회였는지, 인상깊은 문제들과 그 문제들을 어떻게 해결했는지, 마지막으로 대회 우승 소감, 후기 등을 공유하려 합니다.

개인적으로 AWS AI/ML Gameday ASEAN 대회 보단 HyperConnect Security Team 분들과 함께 한 AWS Microservice Gameday Korea 대회가 좀 더 기억에 남아 두 번째 대회를 중점적으로 회고를 해보려 합니다.

# AWS Gameday 개요

AWS Gameday는 대회마다 Concept을 가지고 있는데, Concept에 맞는 시스템/서비스를 구축하고, 다양한 운영 장애/변수 등에 대응하고 성공적으로 시스템/서비스를 구축하고 안정적으로 서비스를 유지하면 Point를 얻는 대회입니다. 해킹대회 방식 중 하나인 CTF(Capture The Flag)를 아시는 분들이라면 비슷한 방식으로 대회가 진행된다고 이해하시면 될 것 같습니다.

자세한 내용은 아래 AWS 공식 문서를 참고해보시면 좋습니다.

[AWS GameDay](https://aws.amazon.com/ko/gameday/)

# AWS Gameday AI/ML(Asean 지역 대회)

AWS Gameday AI/ML 대회의 경우 ASEAN 지역 대회로 개최되었습니다. 한국, 인도, 일본 등 AWS를 사용하는 다양한 ASEAN 지역에서 여러 팀들이 출전 했는데 AWS DNA 3기 멤버끼리 출전한 저희 `Chihuahua Or Muffin` 팀이 1위를 차지했습니다.

![AWS Gameday ASEAN 대회는 1등 인증서도 발급해 주었습니다 🙂]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/AIML Certification.png"}}){: height="700px" .center-image } <center>AWS Gameday ASEAN 대회는 1등 인증서도 발급해 주었습니다 🙂</center>


## 대회 구성

대회의 주제는 AI/ML 이었는데요 간략하게 대회의 Concept를 설명해보면 아래와 같습니다. 

- 참가팀들은 모두 상상의 동물 유니콘을 대여(Rental)해주는 회사인 Unicorn Rental의 AI/ML 팀에 소속되어 있습니다. 

- 각 참가팀들은 Unicron을 Rental 해주는 아래 서비스를 AWS SaaS 서비스들을 활용해 만들어야 합니다.
1. [Amazon Forecast](https://docs.aws.amazon.com/ko_kr/forecast/latest/dg/what-is-forecast.html)와 S3에 업로드 되어 있는 Historic demand data를 이용해 Unicorn Rental의 미래 수요값 예측 모델 구축
2. [Amazon SageMaker](https://aws.amazon.com/ko/about-aws/whats-new/2017/11/introducing-amazon-sagemaker/)와 [EventBridge](https://docs.aws.amazon.com/ko_kr/eventbridge/latest/userguide/eb-what-is.html)를 이용해 **프리미엄 유니콘 렌탈 서비스**를 구독할 확률이 높은 사용자를 선별하는 모델 구축
3. [Amazon Lex](https://docs.aws.amazon.com/ko_kr/lexv2/latest/dg/what-is.html)를 이용해 AI 대화형 챗봇 서비스 구축

- 각 참가팀들은 위 3가지 서비스를 구축 후 안정적으로 운영하여야 지속적으로 Point를 획득할 수 있다.

요약하자면, Unicorn Rental에서 요구하는 3가지 AI/ML 서비스를 AWS SaaS 를 이용해 빠르게 구축하고 장애없이 안정적으로 운영하여 Point를 가장 많이 획득한 팀이 우승하게 됩니다.

## Know-How

### 대회 전략
- 2명, 2명으로 나누어 서비스를 구축
- 구축하며 문제가 발생할 시 모두가 붙어 빠르게 해결

2번 문제가 가장 기억에 남는데, .ipynb(쥬피터 노트북) 파일로 제공되는 Guide를 참고해 내용을 수정하며 Sage Maker를 구축한 뒤 새로운 훈련 데이터가 생길 때마다 EventBridge를 사용해 모델을 재훈련 시키는 Pipeline을 구성해야 했습니다.<br>
그러나 문제가 생겼습니다. 초기 Pipeline을 구성한 뒤  첫 번째 Pipeline 실행은 성공했으나 두 번째 실행부터는 계속 Pipeline 실행에 실패했습니다.<br>
우리 팀은 빠르게 2번 문제의 실패 원인에 대해 분석했고, Sagemaker에 전송되는 Parameter 값이 잘못 구성되어 있는 것을 확인했습니다.<br>
10분 안에 문제를 찾아 다른팀들보다 빠르게 2번 서비스를 완성시킬 수 있었고 1,2번 서비스를 거의 동시에 구축해 포인트에 많이 앞서갈 수 있었습니다.<br>
(대회가 끝난 후 알게되었는데, 이 Parameter 문제를 찾지 못한 팀들은 수동으로 매번 Pipeline에 Parameter를 넣어가며 수작업으로 해결했다고 합니다.)

### 분담의 중요성

AI/ML 대회에서는 분담을 잘 하여 1,2,3번 문제까지 다른팀들보다 빠르게 구축하였고, 서비스도 안정적으로 운영하며 대회 마지막 3시간은 편하게 모니터링만 하며 대회를 1등으로 마무리 했습니다.<br>
중간부터 1등을 할 수 있겠다라는 확신이 있었기에 맘 편히 대회를 치룰 수 있었습니다.<br>
해당 대회를 통해 Gameday에서는 분담을 통해 빠르게 서비스를 구축하고 문제를 해결하는 것이 중요하다는 것을 느꼈습니다.<br>
AI/ML Gameday를 통해 이후 **AWS Gameday Microservice-magic** 대회에서는 더 수월하게 대회를 시작할 수 있었습니다.

![Chihuahua or Muffin팀 우승 기념 사진]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/AIML_ceremony.jpg"}}){: .center-image } <center>Chihuahua or Muffin팀 우승 기념 사진</center>



### 우승 인터뷰

AWS Gameday AI/ML 우승 팀인 **Chihuahua or Muffin** 팀의 인터뷰는 아래 링크에서 확인하실 수 있습니다.

🏅 [아시아 지역 AWS AI/ML GameDay에서 우승한 자랑스런 한국 개발자들](https://aws.amazon.com/ko/blogs/korea/aws-gameday-tour-de-machine-learning-korean-winners/) 🏅

# AWS Gameday Microservice Magic(한국 지역 대회)

AWS Gameday Microservice Magic 이라는 명칭으로 개최된 Gameday 대회는 기존 Monolith 아키텍처로 운영되고 있는 서비스들을 AWS SaaS 서비스를 활용해 Microservice 아키텍처로 전환하는 Concept를 가진 대회였습니다.<br>
이미 AWS Gameday AI/ML를 참가한 뒤이기 때문에 출전할지 말지 고민했지만 Hyperconnect 내 Security Team원들도 출전 의향이 있어 같이 팀을 꾸려 총 5명의 Engineering Unit 인원으로 출전하게 되었습니다.

### 팀이름 작명 비하인드

참고로 팀 이름은 개발자 밈 중에 하나인 “별로 놀랄 일도 아닌 일에 ‘어?~’ 금지” 에서 따온 dj?!(어?!) 였습니다. (우승한 후에 든 생각은, 좀 더 HyperConnector인 것을 티 낼 수 있는 이름으로 정했으면 더 좋았을 것 같았습니다 😊)

![dj?!]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/Developers_meme.png"}}){: height="500px" .center-image }

## 대회 구성

- 참가 팀들은 동일한 Monolithic Architecture 형태의 서비스를 제공받습니다.
- 제공된 서비스 종류는 총 3가지 이며 이 3가지 서비스는  Monolithic Architecture 로 합쳐져 구성되어 있습니다.
- 참가 팀들은 제공된 Monolithic Architecture 서비스를 AWS SaaS 서비스를 이용해 Microservice Architecture로 전환 및 배포해야 합니다.

![출처 : [AWS 모놀리스 애플리케이션을 마이크로서비스로 분할](https://aws.amazon.com/ko/getting-started/hands-on/break-monolith-app-microservices-ecs-docker-ec2/)]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/Monolith_to_microservice.png"}}){: .center-image } <center>출처 :<a href="https://aws.amazon.com/ko/getting-started/hands-on/break-monolith-app-microservices-ecs-docker-ec2/"> AWS 모놀리스 애플리케이션을 마이크로서비스로 분할</a></center>

활용해야 하는 AWS SaaS는 아래와 같았습니다.
- AWS Fargate
- AWS Beanstalk
- AWS ECS

타 팀이 우리팀의 Microservice를 많이 사용할수록, 속도가 빠를 수록 그리고 각 서비스를 성공적으로 구축할 때마다 Point를 획득할 수 있습니다.
- 또한 대회 중간마다 Unicorn Rental의 보안팀이 AWS 내 다양한 설정들을 변경하여 서비스 운영에 장애가 발생할 수 있는데, 참가팀들은 이를 빠르게 정상화 시켜야 합니다.

## Know-How

HyperConnect Security Team원들이 참여한 **dj?!**팀은 대회 Point를 얻는 조건을 보고 몇 가지 전략을 세웠습니다.

### dj?! 팀의 전략

- 대회 사전교육 청강 및 Work Shop 실습을 진행하며 대회에서 사용되는 AWS 서비스들을 경험해봤습니다.
- 빠른 포인트 획득을 위해 아래와 같이 인원분배를 진행했습니다.
    - **3개의 Microservice 구축을 각각 담당할 3명**
    - **서비스 장애 여부, Unicorn Rental 보안팀의 행위 추적 담당 1명**
    - **타 참가팀의 서비스 중 정상적으로 운영되고 있는 서비스 모니터링 및 등록 1명**
- Microservice를 구축하며 도움이 필요한 부분은 위 2,3번 인원이 추가로 지원했습니다.
그리고, 각자의 서비스가 정상 운영되는 과정에서는 2,3번에 분담하여 더욱 빠른 대처를 할 수 있도록 유연하면서도 강한 한 팀이 되고자 했습니다

우리 팀은 대회 시작 후 서비스를 빠르게 구축 & 배포하여야 다른 팀들이 우리의 서비스를 쓸 것이라 판단해 인원을 나눠 서비스를 구축해 나가기 시작했습니다.<br>
우선 서비스를 빠르게 배포해놓은 뒤 점수가 쌓이는 Dashboard를 모니터링 하다보니, 타 팀이 우리의 서비스를 많이 쓸 수록 점수가 가장 빠르게 오르는 것을 확인했습니다<br>
여기서 우리는 점수를 많이 받기 위해서는 아래와 같은 조건과 Action Item이 필요하다고 생각했습니다.
<br>
조건 1. 서비스 장애 시간을 최소화할 것

: Action Item. 우리팀은 3가지 서비스를 다 구축해놓고 주기적으로 Down되거나 장애가 발생하는 서비스들을 **모니터링하면서 장애 시간을 최소화** 했습니다.
    
조건 2. 서비스 요청 처리 속도를 높일 것

: Action Item. 우리팀은 서비스 앞단에 성능 좋은 **ALB(Application Load Balancer)를 구성**하고, 인스턴스 및 Container를 **다중화 구성**하여 각 서버 및 Container에 가해지는 부담을 최소화 시켰습니다
    
조건 3. 다른팀이 많이 쓰고 있는 우리팀의 서비스 1개에 많은 신경을 쏟을 것

: Action Item. 꾸준하게 많은 점수를 획득하기 위해 우리팀은 3개의 서비스에 최소한의 신경을 쓰되, 다른팀이 이미 많이 사용하고 있는 서비스에 **모니터링 및 장애대응 리소스를 최대한 집중**시켰습니다.
<br>
우리 팀은 시작할 때 거의 꼴찌로 시작했지만, 위와 같이 역할을 분담하고 점수를 얻는 Point를 파악하여 Action Item들을 잘 수행한 결과, **게임 초반부터 1위**로 올라설 수 있었습니다.

![Gameday 초반 대회 설명을 듣는 Security Team원들]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/MSMG_while_gaming.jpg"}}){: height="500px" .center-image } <center>Gameday 초반 대회 설명을 듣는 Security Team원들</center>

## 변수 발생, 우리는 어떻게 대응했을까?(How Did We Respond?)

대회를 중간, 1등을 차지한 우리팀은 굉장히 기뻐하면서도 1등을 뺏길지도 모르겠다는 생각에 각자의 역할에 더욱 충실하려 노력했고, 모니터링을 더욱 열심히 했습니다.

그러나 AWS Gameday 주최측에서 변수들을 발생시켰고, 우리는 빠르게 합심해 이에 대응하기 시작했습니다.

### **변수 1. Unicron Rental 보안팀의 AWS 설정 변경**

대회 중반부터, Unicorn Rental 보안팀이 AWS 설정을 전반적으로 변경한다는 컨셉으로 AWS 내의 다양한 설정이 변경되며 서비스 운영에 장애가 생기기 시작했습니다. 

#### **How Did We Respond?** 
우리는 우선 우리 팀의 계정이 아닌 다른 계정으로 일어나는 작업들을 살피기 위해 1명이 CloudTrail 로그를 감시하기 시작했습니다. <br>
그 결과, Unicron Rental 보안팀이 작업하는 계정을 알아낼 수 있었습니다. 그 후 보안팀의 작업에는 몇가지 패턴이 있다는 것을 파악하고, 대회가 끝날 때까지 CloudTrail Log를 모니터링하며 해당 계정으로 일어난 작업에 대해 빠르게 대응할 수 있었습니다.

#### **개인적인 아쉬움**
게임 내에서 보안팀이 서비스의 장애를 유발시키는 악역(?)으로 나온 점이 Security Engineer로 일하고 있는 우리 팀에게는 조금 억울했습니다. <br><center>세상에 나쁜 보안팀은 없습니다 !</center>

<br>
<br>

### **변수 2. 다른 팀 서비스에 대한 공격 기능 추가**

대회를 2시간 앞둔 시점에서 우리팀에게 또 다른 위기가 닥쳐옵니다.

1위팀을 제외한 모든 팀들이 타 팀 서비스를 Down 시키는 공격을 할 수 있는 기능이 추가되었는데요
(우리팀은 중반부터 계속 1등이었기에, 공격을 당할 수 밖에 없는 점이 매우 억울했습니다 ㅠㅠ)

수 많은 팀들이 우리팀을 공격해왔기 때문에 아래 화면과 같이 점수가 오히려 깎이는 상황이 발생되기 시작했습니다.

![image (2).png]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/MSMG_point_loosing.png"}}){: .center-image }

#### **How Did We Respond?** 
이때부터 우리는 3가지 서비스를 모두 유지하는 것이 어렵다고 판단해, 다른 팀들이 가장 많이 사용하고 있는 우리팀의 서비스 1개에만 모든 모니터링 및 장애대응 리소스를 쏟아 붓기 시작했습니다. <br>
그 결과, 타 팀의 공격을 2/3 무시할 수 있었고, 한 개의 서비스는 장애가 발생해도 30초 안에 복구하여 꾸준히 포인트를 획득할 수 있었습니다.

### 마지막 30분

마지막 30분동안 모든 팀의 공격이 우리팀에게 집중되면서 서비스 1개를 운영하는 우리팀과 2위팀(팀명 : 샛별코딩)과의 격차가 점점 좁혀졌습니다.<br>
(혹시나 역전될까봐 1위팀이 집중적으로 공격을 받는 것이 매우 억울했습니다)<br>
거의 10만점 가까이 차이나던 점수는 게임 종료 10분을 앞두고 불과 2만점 정도로 좁혀졌고, 우리팀은 계속해서 서비스가 Down 되지 않도록 노력했습니다.<br>
그 결과, 1등을 지켜낼 수 있었고 마지막까지 긴장감이 유지되어 우승에 대한 기쁨이 더 컸습니다<br>

![약 1만점의 점수차이로 우승할 수 있었습니다 🙂]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/MSMG_dashboard.png"}}){: height="800px" .center-image } <center>약 1만점의 점수차이로 우승할 수 있었습니다 🙂</center>

### 우승 인터뷰

AWS Gameday Microservice Magic 우승 팀인 하이퍼커넥트 Security Team `dj?!`팀의 인터뷰는 아래 링크에서 확인하실 수 있습니다.

🏅 [AWS GameDay - Microservice Magic의 우승팀을 인터뷰하였습니다!](https://aws.amazon.com/ko/blogs/korea/aws-gameday-microservice-magic-interview/) 🏅

# AWS Gameday 후기

## AWS Gameday를 통해 얻은 것들

AWS Gameday를 2번 우승하며 제가 얻은 것들은 아래와 같습니다.

**이런거 잘 챙겨주는 하이퍼커넥트에 어서 합류하세요!**

1. 포상 휴가
2. 회사차원 격려금 및 회식비
3. HyperConnector들의 축하
4. AWS Gameday 우승 상품 : AWS Echo Dot 2개, AWS Gameday 메달, AWS 에코백
5. AWS 서비스에 빠르게 익숙해지는 방법

## AWS Gameday 성적을 잘 내기 위해 필요한 것들

대회에 참가하기 전에는 AWS Gameday를 우승하기 위해선 마냥 AWS 환경에서 개발에 익숙하고 SaaS 서비스 사용에 익숙해야 할 것만 같았습니다. 

하지만 직접 대회에 참가해보니 더 중요한 것이 있었기에 제가 느낀 **Gameday 에서 성적을 잘 내기 위해 필요한 것들**을 공유합니다.

1.  **대회에서 제공해주는 Workshop 문서 및 Readme 잘 읽기**
    - Gameday 뿐 아니라 일할 때도 매우 중요한 것들입니다. Back to Basic 이란 말이 있는 것처럼 생각보다 발생되는 문제는 **기본에 충실하지 않음**에서 나오는 경우가 많았습니다.
2.  **Point를 가장 빠르고 효율적으로 획득할 수 있는 방법을 빠르게 파악하기**
    - Gameday 대회별로 포인트를 주거나 깎는 방법은 다 다릅니다. 우리 팀원들은 흔히 해킹대회라고 불리는 CTF(Capture The Flag)에 참가했던 경험이 많기 때문에, Point를 효율적으로 얻을 수 있는 방법을 찾아내고 이에 집중했습니다.
3.  **AWS Gameday에서 사용되는 SaaS에 대해 미리 예습해오기**
    - 대회에서 서비스 구축에 대한 Workbook과 소스코드 등을 제공해주지만 이용해야하는 AWS SaaS 서비스에 대한 이해가 아예 없으면 서비스의 전체적인 큰 틀과 SaaS를 이용해야하는 목적을 이해하기 어렵습니다. 따라서, 대회 시작전 적어도 대회에 사용되는 AWS 서비스에 대한 문서를 읽어보거나 Workshop 실습 등을 미리 해보는 것을 추천드립니다.

**To Thankful People**
---
두 번의 대회를 출전할 때마다 스스로 AWS에 아주 익숙한 편이 아니고, 주로 출전하시는 Devops Engineer, 개발자 분들보다는 불리할 것이라고 생각했기 때문에 우승보다는 경험하는 것에 의의를 두어 대회에 참여했습니다.

글 제목은 **“AWS 대회 2관왕한 사람이 푸는 우승 Know-Hows” 이라는** 아주 거만한(?) 제목을 썼지만 제가 대회에서 2번 우승할 수 있었던 가장 큰 이유는 **합이 잘 맞는 분들과 대회를 함께할 수 있어서** 이었습니다.

이 자리를 빌어 저와 함께 대회에 출전해주신 **dj?! 팀 (**Hyperconnect Security Team의 Hardt, Ricky, Cape, Finn) 과 **Chihuahua or Muffin 팀** (새미님, 영록님, 보현님) 팀원분들께 감사하다는 말씀을 드리고 싶습니다.

![dj?!팀 : 하이퍼커넥트 Security Team 왼쪽부터 Cape, James.B, Hardt, Ricky, Finn]({{"/assets/2022-04-19-AWS-GameDay-Know-Hows/MSMG_ceremony.png"}}){: .center-image } <center> dj?!팀 : 하이퍼커넥트 Security Team 왼쪽부터 Cape, James.B, Hardt, Ricky, Finn </center>

# References

[1] [AWS GameDay](https://aws.amazon.com/ko/gameday/)

[2] [아시아 지역 AWS AI/ML GameDay에서 우승한 자랑스런 한국 개발자들](https://aws.amazon.com/ko/blogs/korea/aws-gameday-tour-de-machine-learning-korean-winners/)

[3] [AWS 모놀리스 애플리케이션을 마이크로서비스로 분할](https://aws.amazon.com/ko/getting-started/hands-on/break-monolith-app-microservices-ecs-docker-ec2/)

[4] [AWS GameDay - Microservice Magic의 우승팀을 인터뷰하였습니다!](https://aws.amazon.com/ko/blogs/korea/aws-gameday-microservice-magic-interview/)

---
layout: post
date: 2021-06-07
title: 회귀 단절 모형을 활용한 전후 비교 분석
author: yun
tags: data-analysis regression econometrics
excerpt: 회귀 단절 모형을 이용한 효과적인 전후 비교 방법을 소개합니다
---

안녕하세요, 하이퍼커넥트의 데이터 분석가 강동윤입니다.

하이퍼커넥트에서는 사용자들에게 보다 나은 경험을 선사하고자 다양한 실험을 진행합니다. 
이와 관련하여 데이터 분석팀에서 매번 고민하는 주제는 **"이번 실험의 효과는 무엇이었는가?"** 입니다. 
그러나 인과 관계를 분석하는 것은 매우 어려운 주제이고, 때문에 저희는 다양한 방법을 연구 및 시도하고 있습니다.
이번 포스팅에서는 그 방법 중 하나인 **회귀 단절 모형(Regression Discontinuity)** 에 대해 소개합니다. 


## 인과 관계란?
회귀 단절 모형(이하 RD)을 소개하기 전에 인과 관계에 대해 간략하게 짚고 넘어갈 필요가 있습니다.
만약 4월 20일에 어떤 이벤트가 있었고 그 때를 기점으로 유저들의 앱 체류시간이 증가했다면, 과연 그 이벤트(원인)로 인해 체류시간이 증가(결과)했다고 단언할 수 있을까요?
이를 쉽게 판단하려면 4월 20일로 타임머신을 타고 돌아가 예정되어 있던 이벤트를 취소한 다음, 이벤트를 실행했을 때의 미래와 비교하면 됩니다.
즉, **다른 모든 조건이 동일한** 두 집단을 만들어 비교하는 것이죠.
이렇게 하면 두 집단 간의 유일한 차이점은 이벤트 실행 여부 뿐이므로, 체류시간의 차이는 곧 이벤트로부터 비롯된 결과라고 생각할 수 있게 됩니다. 

그러나 당연하게도 자연 과학을 제외한 분야에서는 동일한 조건에서의 재현이 사실상 불가능하기 때문에 인과 관계를 분석하기 매우 까다롭습니다.
그래서 계량 경제학이라고 부르는 학문에서는 재현이 아닌 방법으로 다른 모든 조건이 동일한 두 집단을 구성하는 것에 초점을 맞춥니다.
이는 일반적으로 **무작위 또는 무작위에 준하는 방법**으로 집단을 구성함으로써 가능해집니다. 
어떤 두 집단을 무작위로 뽑아 (충분히 많은 수로) 구성했다면, 두 집단은 통계적으로 동일한 특성을 가진 집단이라고 간주할 수 있기 때문입니다.

하지만 예를 들어 **"법적 최소 음주 연령을 제한하는 것이 연령에 따른 사망률에 영향을 미칠까?"** 라는 주제를 분석한다고 할 때, 원인에 해당하는 법적 최소 음주 연령 제한은 무작위와 거리가 먼 사건이므로(법은 모두에게 일괄 적용되므로) 앞서와 같은 개념을 적용하기 어렵습니다.
이처럼 무작위에 기대기 어려운 주제에서는 무작위에 준하는 방법을 대신 활용할 수 있는데요.
지금부터 그 방법 중 하나인 RD에 대해 소개하겠습니다.

## RD(Regression Discontinuity)란?
[고수들의 계량경제학](https://www.masteringmetrics.com/) 에서는 RD를 활용하는 예시로 법적 최소 음주 연령을 21세로 제한하는 정책이 등장합니다. 
그 영향을 분석하기 위해서는 정책으로 인해 제한을 받는 그룹(21세 미만)과 받지 않는(21세 이상) 그룹을 비교해야 적절할 것입니다.
여기서 좀 더 구체적으로 들어가서, 만약 **21세보다 조금 어린 사람**과 **21세를 조금 넘은 사람**을 비교한다면 어떨까요?
아래 그래프와 함께 자세히 설명하겠습니다.

![1]({{"/assets/2021-06-07-regression-discontinuity-in-time/1.png"}}){: .center-image }{: width="55%" height="35%"}
RD 예시 - 법적 최소 음주 연령을 지정하는 정책의 효과
{: style="font-size: 80%; text-align: center;"}

위 그래프는 1997~2003년 기준 21세에 근접한 모든 미국인들의 사망률을 연령에 따라 보여주고 있습니다. 
x축은 연령(월 단위로 표시)이고, y축은 사망률(10만 명당 연 사망자 수로 측정)을 의미합니다.
여기서 21세에 표시된 점선 왼쪽을 **A그룹**, 오른쪽을 **B그룹**이라고 하겠습니다.
그러면 21세 생일이 한 달 남은 100명의 미국인은 A그룹에 속할 것이고, 21세 생일이 한 달 지난 100명의 미국인은 B그룹에 속하게 됩니다.
기본적으로 각 연령에 해당되는 모든 미국인이 대상일 뿐더러, 서로 비슷한 나이 또래(위 예시에서는 고작 2달 차이)이므로 두 그룹 간 인구통계학적 특성은 기본적으로 유사할 것이라 짐작해볼 수 있습니다.
즉, A와 B그룹은 음주 정책의 적용 여부를 제외한 다른 모든 조건이 동일한 두 집단로 간주할 수 있는 것이죠.
앞서 언급한 것처럼 정책은 기본적으로 무작위성과 거리가 멀지만, 역설적이게도 이 예시에서는 관찰하는 데이터의 범위를 좁힘으로써 무작위에 준하는 훌륭한 실험을 가능케 한 것입니다.

다시 위 그래프로 돌아가면, 21세를 기점으로 사망률이 눈에 띄게 상승한 사실을 알 수 있습니다.
이를 회귀식의 형태로 표현하면 아래와 같습니다.

$$
\bar{M}_a = \alpha + \rho D_a + \gamma a + e_a
$$

먼저 $$\bar{M}_a$$는 연령 $$a$$에 따른 사망률을 의미합니다. 
그리고 $$D_a$$는 $$a \geq 21$$이면 1,  $$a \lt 21$$이면 0의 값을 가집니다.
즉, $$D_a$$의 계수인 $$\rho$$는 21세를 기점으로 나타나는 사망률의 급격한 변동을 포착하는 값인 것이죠.
그리고 연령을 나타내는 $$a$$의 계수인 $$\gamma$$는 이 정책과 무관하게 연령에 따라 달라지는 사망률의 변동을 통제합니다.
**회귀 단절 모형**이라는 이름의 유래는, 이처럼 결과에 영향을 주는 다른 변수를 통제할 때 회귀식의 형태를 사용하는 관행 때문입니다. 

![2]({{"/assets/2021-06-07-regression-discontinuity-in-time/2.png"}}){: .center-image }{: width="55% height="35%"}
Case1: 임계치 전후 비선형성이 나타나는 경우
{: style="font-size: 80%; text-align: center;"}
![3]({{"/assets/2021-06-07-regression-discontinuity-in-time/3.png"}}){: .center-image }{: width="55%" height="35%"}
Case2: 임계치 전후 그래프가 매끄럽게 이어지는 경우
{: style="font-size: 80%; text-align: center;"}

물론 위 예시처럼(Case1) 깔끔한 직선이 아닌 경우에는 다항함수 등을 활용해 비선형성을 직접 모형에 반영해야 하고, 또는(Case2) 임계치 전후에 급격한 차이가 나지 않고 매끄럽게 이어지는 모양새인 경우 신뢰할만한 RD추정치를 도출하기 어려우므로 주의해야 합니다. 

## RDiT(Regression Discontinuity in Time)란?
그렇다면 RDiT는 무엇일까요? 

**"in Time"** 에서 유추할 수 있듯이 RDiT는 독립변수가 시계열(시간)인 RD모형을 의미합니다. 
여기서 독립변수가 시간이라는 점으로 인한 여러 차이점이 발생합니다. 
자세하게는 다음과 같습니다.

![4]({{"/assets/2021-06-07-regression-discontinuity-in-time/4.png"}}){: .center-image }{: width="55%" height="35%"}
RDiT 예시 - 대기 오염 물질 배출 규제 이후 대기중 오존 농도 변화
{: style="font-size: 80%; text-align: center;"}

**첫째**, 실험 설계의 관점에서 차이가 있습니다. 
예를 들어 대기 오염 물질을 배출하는 공장을 규제하는 정책의 효과를 분석한다고 해보겠습니다.
공장의 규모가 1000mw이상인 경우를 규제 대상으로 볼 때, **RD**의 관점에서는 1000mw보다 작은 규모의 공장과 그보다 큰 규모의 공장으로 두 집단을 나눠 비교할 것입니다.
그러나 **RDiT**의 관점에서는 1000mw보다 큰 공장에 한해서 정책 도입 전후를 비교하게 됩니다.
즉, RD에서는 규모가 서로 다른 두 공장 집단을 비교하는 반면, RDiT에서는 동일 집단의 서로 다른 시점을 비교하는 것이죠.

**둘째**, 비교 집단을 구성하는 관점에서 차이가 있습니다.
같은 예시에서 **RD**를 고려하는 경우 무작위에 준하는 실험을 위해 임계치(1000mw) 부근의 값끼리 비교하게 됩니다.
앞서 언급한 것처럼 300mw인 공장과 10000mw인 공장을 비교한다면 규모 뿐 아니라 다른 여러 부분에서 차이가 있을 것이므로 공정한 비교가 어렵지만, 999mw와 1001mw를 비교한다면 규모 외의 다른 차이점은 없다고 생각할 수 있기 때문입니다.
하지만 **RDiT**에 이와 같은 개념을 적용하기에는 무리가 있습니다.
4월 3일과 5일을 비교하는데, 3일은 평일이라 공장을 가동했지만 5일은 공휴일이라 가동이 중단되었다면 어떨까요?
혹은 하루 사이에 발생한 급격한 온도 변화가 정책과 무관하게 오존 농도에 영향을 줄 수도 있겠죠? 
이처럼 시간의 변화는 수많은 변수를 낳기 때문에 임계점에 근접한 날짜들이라고 동일하게 여기기 어렵습니다.

**셋째**, 샘플 사이즈 관점에서 차이가 있습니다.
**RD**에서는 샘플 사이즈를 가능한 만큼 늘릴 수 있습니다.
다양한 규모의 많은 공장들을 시간과 체력이 허락하는 한 관찰하면 되기 때문입니다.
그러나 **RDiT**에서 샘플 사이즈를 늘린다는 것은 관찰 기간을 넓힌다는 의미이고, 위와 마찬가지로 시간의 변화에 따른 수많은 변수가 생기게 됩니다.
그렇게되면 정책 도입 전후의 오존 농도 차이는 정책의 효과일수도, 혹은 해당 기간에 발생한 예측 불가능한 이벤트 때문일수도 있겠죠.
결국 RDiT로 계산된 추정치를 신뢰하기 어렵게 됩니다.

종합하면, 독립변수가 시간이라는 점 때문에 RDiT 활용 시 사전에 고려할 부분이 많아집니다.
하지만 언제나 핵심은 임계점 전후 집단을 **모든 조건이 동일한 두 집단**으로 구성하는데 있습니다.
따라서 임계 시점 전후로 다른 이벤트가 없었음을 어느정도 확신할 수 있는 상황이라면 충분히 활용 가능한 방법입니다.
이는 내부 정보를 이용함에 따른 혜택이므로 자신의 도메인이 아닌 분야에서는 활용하기 어렵겠습니다. 

## RDiT를 활용한 전후비교
이제 RDiT를 실제 전후비교에 사용하는 방법을 간략히 소개하겠습니다.
하이퍼커넥트의 소셜 라이브 스트리밍 서비스인 하쿠나 라이브에는 여러 사람들이 함께 방송할 수 있는 **라운지(Lounge)** 가 있습니다.
지난 2/24에 이 라운지로의 진입을 늘리기 위한 팝업을 배포했는데요.
이번 전후비교의 예시로 팝업의 배포 전후 탭 진입율이 유의미하게 변화했는지를 분석해보겠습니다.

![7]({{"/assets/2021-06-07-regression-discontinuity-in-time/7.png"}}){: .center-image }{: width="75%"}
하쿠나 라이브의 라운지
{: style="font-size: 80%; text-align: center;"}

먼저 각 나라 별로 임계 시점(2/24) 전후 30일치 데이터를 확보했고, 내부 정보를 활용하여 해당 기간 동안 팝업 배포 외 진입율에 영향을 줄만한 그 어떠한 이벤트도 없었음을 확인하였습니다.

다음은 데이터를 눈으로 살펴볼 차례입니다.
산점도는 다음의 r코드로 구현할 수 있습니다.

```r
# import raw data
raw = read.csv("file-path", header=T)

# plot the data of Region A
region_A = raw[,c(1,2)]
plot(raw2,
     col="steelblue",
     pch=20,
     xlab="dt", 
     ylab="tab enter ratio")
abline(v=31, col="black", lty=5)
```

아래는 국가 별 라운지 진입율의 산점도입니다.
**x**축은 1부터 60까지의 숫자로 표현된 날짜, **y**축은 라운지 탭 진입율을 의미합니다.
임계 시점 전후를 구분하기 위해 31번째 시점에 수직선(abline)을 추가하였습니다. 

![6]({{"/assets/2021-06-07-regression-discontinuity-in-time/6.png"}}){: .center-image }{: width="100%"}
*위 데이터는 서비스 실제 데이터가 아닌 임의의 샘플 데이터임을 참고 바랍니다 
{: style="font-size: 80%; text-align: center;"}

우선 임계 시점 전후 데이터에 선형적 추세가 있다고 봐도 무리가 없을 것 같습니다.
그리고 **A, C, D**국가의 경우 임계 시점 이후 진입율이 상승한 부분이 비교적 명확하게 보입니다.
반면 **B**와 **E**국가는 눈으로 보기에는 별로 달라진게 없어 보이네요.

이제 아래 코드로 데이터를 **RD**에 fitting해보겠습니다.
* 임계 시점에 해당하는 데이터의 number를 **cutpoint**로 입력했습니다.
* 국가에 관계없이 전후 데이터의 기울기가 서로 유사한 편이므로 **slope = "same"** 옵션을 지정했습니다. 

```r
# import library
install.package("rddtools")
library(rddtools)

# import raw data
raw = read.csv("file-path", header=T)

# construct RD data 
region_A = raw[,c(1,2)]
data <- rdd_data(y=region_A[,2], 
                 x=region_A[,1],
                 data=region_A,
                 cutpoint=31)

# estimate the sharp RD model
rdd_mod <- rdd_reg_lm(rdd_object=data, 
                      slope="same")
summary(rdd_mod)
```

마지막의 **summary**를 실행하면 아래와 같이 상세한 결과를 출력합니다.
* 하단 **p-value**가 0.01보다도 낮은 수준이므로, 해당 모형이 통계적으로 유의미함을 알 수 있습니다.
* **결정 계수(R-squared)** 가 0.5주변이므로 데이터에 대한 모형의 설명력이 나쁘지 않은 수준입니다.
* 임계치 전후 차이를 포착하는 변수 **$$D$$**또한 유의미하며, 그 값이 0.03, 즉 A국가의 경우 팝업 배포로 인해 탭 진입율이 3%p가 증가했음을 알 수 있습니다.  

![8]({{"/assets/2021-06-07-regression-discontinuity-in-time/8.png"}}){: .center-image }{: width="50%"}

위와 동일한 방식으로 5개국 모두의 결과를 요약하면 다음과 같습니다.
* **A국가** : 3.0%p상승
* **B국가** : 3.7%p상승
* **C국가** : 4.1%p상승
* **D국가** : 2.9%p상승
* **E국가** : 유의미하지 않음

## 마치며
지금까지 RDiT의 개념과 이를 전후비교에 활용하는 방법에 대해 다뤄보았습니다.
시간이라는 개념이 엮여있기 때문에 고려할 부분이 많지만, 잘 설계한다면 매우 좋은 비교방법이 될 수 있습니다.

## References
[1] Joshua D. Angrist , Jorn-Steffen Pischke, [Mastering 'Metrics](https://www.masteringmetrics.com/)

[2] Catherine Hausman, David S. Rapson, [Regression Discontinuity in Time:Considerations for Empirical Applications](http://deep.ucdavis.edu/uploads/5/6/8/7/56877229/deep_wp019.pdf)
---
layout: post
date: 2026-01-12
title: 비즈니스 문제를 AI 문제로 정렬하는 방법
authors:
    - zerry 
tags:  machine-learning recommender-system
excerpt: 최적화 이론의 완화(relaxation) 개념을 비즈니스 문제에 적용하여, 비즈니스 문제를 AI 문제로 정렬하는 방법을 소개합니다. 
last_modified_at: 2026-01-12
---


AI 조직은 비즈니스 문제를 AI 문제로 정렬해서 푸는 조직입니다.
AI 문제란 무엇일까요?
우리가 현업에서 정말 다양한 업무들을 하지만, 본질은 효용 함수(또는 손실 함수)를 최적화하는 문제입니다.
명시적이든 암시적이든, 우리는 문제를 최적화 식(optimization form)으로 쓰게 됩니다.
ML 알고리즘을 통해 최적화 식의 해(solution)를 찾고, 이 해를 이용해 비즈니스 문제를 풉니다.
결국, AI 조직은 수학적 해를 통해 비즈니스의 해를 찾아가는 조직입니다. 

비즈니스 문제는 본질적으로 어렵습니다.
그렇다면 우리는 이런 어려운 문제를 어떻게 풀어야 할까요?
최적화 이론에서는 이런 어려운 문제를 풀기 쉬운 문제로 완화(relaxation)해서 풉니다.
특히, 여러 개의 지역(local) 최솟값에 갇힐 수 있는 비볼록(non-convex) 문제를 볼록(convex) 문제로 바꾸어 해결하는 방법들을 중요하게 다룹니다.
볼록 문제는 지역 해가 곧 전역 해인 아름다운 성질을 가지는 덕분에 우리는 경사 하강(gradient descent) 같은 단순한 방법으로도 전역 최적해를 찾을 수 있습니다.
그래서 최적화 이론에서는 비볼록 문제를 볼록 문제로 바꾸는 변환 과정을 볼록 완화(convex relaxation)라고 부르며, 어려운 문제를 풀 수 있는 형태로 재정의하는 방법 중 하나로 중요하게 다룹니다.

직접적으로 풀기 어려운 비즈니스 문제도, 최적화 이론에서 제시하는 것처럼 풀 수 있는 형태로 완화(relaxation)하면 훨씬 다루기 쉬워집니다.
완화된 문제를 잘 설계하면, 비록 원래의 복잡한 비즈니스 문제를 직접 푸는 것은 아니더라도, 그 해가 원래 문제(original problem)의 해와 충분히 유사한 결과를 만들어낼 수 있습니다.
실제로 AI 조직에서 다루는 문제의 대부분은 의식적으로든 무의식적으로든 이러한 완화된 형태를 띱니다.
예를 들어, 어떤 AI 기능을 개발하기 위해 분류기(classifier)를 만든다고 해봅시다.
우리가 진정으로 개선하고자 하는 것은 특정 비즈니스 지표일 것입니다.
하지만 현실적으로 그 지표를 직접 최적화하기는 어렵기 때문에, 대신 우리는 "분류기를 잘 학습시키는 문제"로 바꾸어 풉니다.
이 분류 문제는 원래의 비즈니스 목표를 근사적으로 대변하는 완화된 문제(relaxed problem)라고 볼 수 있습니다.
결국, AI 조직은 비즈니스 문제를 바로 푸는 대신, 그 문제를 AI 문제로 적절히 완화하고, 그 완화된 문제를 최적화함으로써 비즈니스 임팩트를 만들어내는 조직이라 할 수 있습니다.

## Preliminary: Convex Relaxation

원래의 문제를 "잘" 완화한다는 것은 무엇일까요?
이 질문에 대한 좋은 힌트는 convex relaxation에서 찾을 수 있습니다.
우리는 머신러닝을 처음 배울 때 거의 예외 없이 Lasso regression을 접하게 됩니다.
그 이유는 단순합니다.
Lasso는 "풀기 어려운 문제를 풀기 쉬운 형태로 바꾸는" convex relaxation의 가장 대표적인 예이기 때문입니다.
우선, 기본이 되는 선형회귀(linear regression)를 생각해봅시다.

$$
\arg\min_{\beta} \| y - X\beta \|_2^2
$$

이 문제는 모든 변수(feature)를 그대로 사용하는 회귀식입니다.
하지만 우리는 종종 모델이 너무 복잡해지는 것을 피하고 싶습니다.
일부 계수($$\beta_i$$)만 남기고 나머지는 0으로 만들어, sparse한 해를 얻고 싶은 거죠.
그렇게 하려면 다음과 같은 제약식을 추가해야 합니다.

$$
\arg\min_{\beta} \| y - X\beta \|_2^2 \quad \text{s.t. } \|\beta\|_0 \le k
$$

여기서 $$\|\beta\|_0$$은 0이 아닌 계수의 개수를 세는 항으로, "전체 변수 중 최대 $$k$$개만 사용할 수 있다"는 제약을 뜻합니다.
하지만 이 문제는 모든 feature subset을 탐색해야하는 조합 최적화(combinatorial optimization) 문제이기에 해를 찾는 데 지수적 탐색이 필요합니다.
다시 말해, 현실적으로 풀기 어렵습니다.

그래서 등장한 것이 Lasso regression입니다.

$$
\arg\min_{\beta} \|y - X\beta\|_2^2 + \lambda \|\beta\|_1
$$

Lasso는 원래의 $$\ell_0$$ 제약 조건을  $$\ell_1$$ 정규화 항으로 바꾸어, 문제를 볼록하게 만듭니다.
이렇게 하면 경사하강법 같은 간단한 방법으로도 해를 안정적으로 구할 수 있습니다.
이 변환이 바로 convex relaxation입니다.
즉, 원래의 "풀기 어려운" 조합 최적화 비볼록 문제를 "풀기 쉬운" 볼록 문제로 완화한 것입니다.

물론, 두 문제의 해가 항상 동일하지는 않습니다.
하지만, 몇 가지 가정(mutual incoherence condition, restricted isometry property)이 만족되면, Lasso의 해는 원래 문제의 해와 거의 동일하거나 동일하게 일치한다는 것이 증명되어 있습니다.
이런 의미에서, Lasso는 "잘 완화된 문제"의 대표적인 사례입니다.
정리하자면, 아래와 같습니다.

$$

\underbrace{\arg\min_{\beta} \|y - X\beta\|_2^2 \ \text{s.t. } \|\beta\|_0 \le k}_{\text{original problem}}
\quad
\text{vs.}
\quad
\underbrace{\arg\min_{\beta} \|y - X\beta\|_2^2 + \lambda \|\beta\|_1}_{\text{relaxed problem}}

$$

우리가 Lasso regression 문제를 푼다는 것은 결국 "풀기 어려운 원래 문제를 풀 수 있는 비슷한 문제로 바꾼 뒤 최적화하는 것"입니다.
그리고 몇 가지 가정 아래에서 원래 문제와 완화된 문제의 해가 거의 같습니다.

Convex relaxation에서 우리가 진짜로 주목해야 하는 것은 단순히 문제를 쉽게 바꾸는 기술이 아닙니다.
"언제 원래 문제와 완화된 문제를 사실상 같은 것으로 볼 수 있는가"를 이해하는 일입니다.
Lasso의 예에서처럼, 우리는 비볼록($$\ell_0$$) 문제를 볼록($$\ell_1$$) 문제로 바꾸지만 두 문제의 해가 항상 같지는 않습니다.
두 문제를 동일한 문제로 간주하려면 몇 가지 가정이 필요합니다.
몇몇 가정들이 충족될 때에만 두 문제가 사실 상 동일한 문제로 간주할 수 있습니다.

비즈니스 문제를 AI로 문제로 치환할 때에도 동일하게 적용됩니다.
현실의 비즈니스 문제는 복잡하고, 여러 지표가 얽혀 있어 직접적으로 풀기 어렵습니다.
이런 문제를 AI 문제로 바꾸어 풀기 위해서는 명시적인 가정을 세워야 합니다.
그리고 그 가정이 타당한지를 제품 환경에서의 A/B 테스트로 검증하게 됩니다.
만약 완화된 문제를 잘 풀었는데도 비즈니스 지표가 개선되지 않았다면, 이는 우리가 세운 가정 중 일부가 현실과 맞지 않았다는 뜻입니다.
이때는 가정을 다시 점검하고, 다른 방식으로 문제를 완화해 새롭게 접근해야 합니다.

정리하자면, "잘 완화한다는 것"의 핵심은 세 가지입니다.
첫째, 완화된 문제의 해가 원래 문제의 해와 충분히 유사해야 합니다.
둘째, 두 문제의 유사성을 보장하기 위한 가정들을 명시적으로 세워야 합니다.
셋째, 그 가정들이 현실에서 타당한지 A/B 테스트를 통해 지속적으로 검증해야 합니다.
Lasso에서 mutual incoherence condition 같은 가정들이 만족될 때 원래 문제와 완화된 문제의 해가 유사해지듯이, 비즈니스 문제를 AI 문제로 완화할 때도 우리가 세운 가정들이 현실과 부합할 때 비즈니스 임팩트를 만들어낼 수 있습니다.



## 비즈니스 문제를 어떻게 AI 문제로 완화할까?

이제 실제 사례를 통해 비즈니스 문제를 AI 문제로 완화하는 과정을 구체적으로 살펴보겠습니다.
하이퍼커넥트의 과거 시스템에서 사용되었던 접근 방식을 예시로 들어 설명하겠습니다.
아자르에서 AI 기반 추천 시스템을 만들어 사람들을 실시간으로 더 잘 매칭시켜줘야 한다고 해봅시다. 
추천 시스템은 유저들을 일정한 주기로 모으고 이 유저들 중에 어떤 유저들끼리 매칭시킬지를 결정합니다.
비즈니스 문제를 AI 문제로 치환해본 경험이 없더라도 대부분의 AI PM 혹은 연구자들은 이런 시스템을 고안할 가능성이 큽니다. 
두 유저 사이의 대화 시간을 예측하는 모델을 만들고, 예측 대화 시간이 높은 유저 쌍 순서대로 매칭시켜 줍니다.
그럼 우리가 실제 푸는 문제는 아래와 같은 대화 시간을 예측하는 문제로 바뀌게 됩니다.
즉, 비즈니스 문제를 풀기 위해 대화 시간 예측을 잘 하는 새로운 완화된 문제를 풉니다.

$$
\text{minimize } \sum_{u,p,c \in \mathcal{D}} \mathcal{L}(c, f(u,p))
$$

여기서 $$u$$는 유저, $$p$$는 매칭 상대 유저(파트너), $$c$$는 실제 대화 시간, $$f(u,p)$$는 유저 $$u$$와 파트너 $$p$$의 대화 시간을 예측하는 함수, $$\mathcal{L}$$은 손실 함수, $$\mathcal{D}$$는 학습 데이터셋을 의미합니다.

비즈니스에서의 최종 목표는 장기 매출(long-term revenue)의 극대화입니다.
하지만 "장기 매출을 최적화하라"는 문장은 실제로는 너무 복잡하고 애매해서 바로 최대화하기 어렵습니다.
매출은 수많은 요인(사용자 유입, 리텐션, 구매 전환율, 결제 금액, 콘텐츠 품질, 시장 요인 등)이 얽힌 비선형적 결과이기 때문입니다. 우리는 이 거대한 비볼록 문제를 그대로 풀 수 없습니다. 

$$
\text{maximize } (\text{long-term-revenue})
$$

장기 매출 최대화 문제는 그대로 풀기 어렵기 때문에, 먼저 지금보다 문제를 조금 더 단순하게 만들 필요가 있습니다. 
먼저, 오늘을 day $$0$$이라고 할 때, 오늘로부터 $$N$$일 후인 day $$N$$의 매출을 $$\text{revenue}_{N}$$이라고 합시다. 

$$\textbf{Assumption 1.}$$ $$N$$이 충분히 크면, 시스템이 정상 상태(steady state)에 도달하여 day $$N$$의 매출이 장기 매출을 대표할 수 있다. 

$$
\begin{aligned}
& \text{maximize } (\text{long-term-revenue}) \\
=\ & \text{maximize } (\text{revenue}_N)
 \end{aligned}
$$

$$\textbf{Assumption 1}$$을 통해 장기 매출 최대화 문제를 조금 더 쉬운 문제로 완화하였습니다. 
하지만, $$\text{revenue}_N$$은 직접 최적화하는 문제는 아직 어렵습니다. 
더 문제를 쉽게 바꿀 필요가 있습니다. 
이를 위해 제품 분석에서 표준적으로 사용되는 다음과 같은 방식으로 $$\text{revenue}_N$$을 분해할 수 있습니다. 

$$
\text{revenue}_N = \text{DAU}_N \times \text{PUR}_N \times \text{ARPPU}_N
$$

여기서 $$\text{DAU}_N$$는 $$N$$일째의 활성 사용자 수(Daily Active Users), $$\text{PUR}_N$$은 $$\text{DAU}_N$$ 중 구매자의 비율(Purchase User Rate), $$\text{ARPPU}_N$$는 $$N$$일째의 구매자 1인당 매출(Average Revenue Per Paying User)을 의미합니다.

$$\textbf{Assumption 2.}$$ $$\text{DAU}_N$$을 변화시켜도 $$\text{PUR}_N$$과 $$\text{ARPPU}_N$$이 변하지 않는다.

실제로는 우리의 액션에 따라 $$\text{DAU}_N$$, $$\text{PUR}_N$$, $$\text{ARPPU}_N$$ 세 가지 지표가 모두 변화할 수 있습니다.
하지만, 문제를 단순화하기 위해 모든 요인을 동시에 최적화하기보다는 일부 요인을 고정하고 다른 요인에 집중하는 가정을 세울 수 있습니다.
$$\textbf{Assumption 2}$$ 가정 아래에서 장기 매출 최대화 문제를 아래와 같이 완화할 수 있습니다.

$$
\begin{aligned}
& \text{maximize } (\text{long-term-revenue}) \\
=\ & \text{maximize } (\text{revenue}_N) \\
=\ & \text{maximize } (\text{DAU}_N)
 \end{aligned}
$$

하지만 $$\text{DAU}_N$$을 직접 최대화하는 것도 여전히 어렵습니다.
따라서 추가적인 가정이 필요합니다.

$$\textbf{Assumption 3.}$$ DAU는 [carrying capacity 가설](https://keithschacht.medium.com/web-and-mobile-products-understanding-your-customers-d8ee1e56b5a3)에 의해 $$N$$이 충분히 클 때, $$\text{DAU}_N$$을 아래와 같이 표현할 수 있다.

$$
\text{DAU}_N = \frac{\text{inflow}_0}{1 - \text{retention}_0}
$$

여기서 $$\text{retention}_i$$은 day $$i$$의 활성 유저를 코호트로 잡을 때의 D1 리텐션을 의미하며, $$\text{retention}_0$$은 오늘 활성화된 유저들의 D1 리텐션, 즉 오늘 활성화된 유저들이 내일도 방문하는 비율을 의미합니다.
$$\text{inflow}_i$$는 day $$i$$에 유입되는 유저(신규 유저 + 부활 유저)를 의미합니다.
물론, DAU가 위 모형보다 더 복잡한 모형을 따른다고 가정할 수도 있지만, 일단 문제를 더 쉽게하기 위해 매우 간단한 모형을 가정해보기로 합니다.

$$\textbf{Assumption 4.}$$ $$\text{inflow}_0$$는 우리가 변경할 수 없다.

$$\text{inflow}_0$$를 우리가 바꿀 수 없다는 추가 가정을 두면, 결국 $$\text{DAU}_N$$을 최대화하는 문제는 오늘의 D1 리텐션을 높이는 문제로 완화할 수 있습니다.
$$\textbf{Assumption 1-4}$$을 적용하면, 장기 매출 최대화 문제는 리텐션 최대화 문제로 완화됩니다.

$$
\begin{aligned}
& \text{maximize } (\text{long-term-revenue}) \\
=\ & ... \\
=\ & \text{maximize } (\text{DAU}_N) \\
=\ & \text{maximize } (\text{retention}_0)
 \end{aligned}

$$

하지만, 리텐션을 최대화하는 문제도 여전히 어렵습니다.
그래서 한 번 더 완화가 필요합니다.
[이전 테크 블로그](https://hyperconnect.github.io/2024/04/26/azar-aha-moment.html)에서 밝혔듯이, 아하 모멘트 프레임워크로 리텐션을 올리는 더 쉬운 1차 지표를 찾을 수 있습니다. 
아하 모멘트 프레임워크를 통한 분석을 통해 $$\textbf{Assumption 5}$$를 찾았다고 가정해봅시다. 

$$\textbf{Assumption 5.}$$ $$\text{DAU}_0$$ 중에서 $$X$$분 이상 채팅한 유저의 비율을 올리면 $$\text{retention}_0$$이 올라간다.

$$
\begin{aligned}
& \text{maximize } (\text{long-term-revenue}) \\
=\ & ... \\
=\ & \text{maximize } (\text{retention}_0) \\
=\ & \text{maximize } (\text{DAU}_0 \text{ 중에 } X \text{분 이상 채팅한 유저의 비율})
 \end{aligned}
$$

아래의 $$\textbf{Assumption 6}$$을 추가하면, $$\text{DAU}_0$$ 중에서 $$X$$분 이상 채팅한 유저의 수를 최대화하는 문제로 장기 매출 최대화 문제를 한번 더 완화할 수 있습니다. 

$$\textbf{Assumption 6.}$$ $$\text{DAU}_0$$의 수는 우리가 제어할 수 없는 것이다. 

$$
\begin{aligned}
& \text{maximize } (\text{long-term-revenue}) \\
=\ & ... \\
=\ & \text{maximize } (\text{DAU}_0 \text{ 중에 } X \text{분 이상 채팅한 유저의 비율})\\
=\ & \text{maximize } (\text{DAU}_0 \text{ 중에 } X \text{분 이상 채팅한 유저의 수})
 \end{aligned}
$$

하지만 $$\text{DAU}_0$$ 중에서 $$X$$분 이상 채팅한 유저 수를 직접 최대화하는 것도 여전히 어렵습니다.
이를 더 단순화하기 위해, $$\mathcal{U}_i$$를 day $$i$$에 활성화된 유저들의 집합이라고 정의할 때 다음과 같은 가정을 추가로 해볼 수 있습니다. 

$$\textbf{Assumption 7.}$$ $$\text{DAU}_0$$ 중에서 $$X$$분 이상 채팅한 유저 수를 최대화하는 문제는 각 유저 $$u \in \mathcal{U}_0$$에 대해 그날 경험한 총 대화 시간을 최대화하는 문제와 같다.

$$
\begin{aligned}
& \text{maximize } (\text{long-term-revenue}) \\
=~& ... \\
=\ & \text{maximize } (\text{DAU}_0 \text{ 중에 } X \text{분 이상 채팅한 유저의 수}) \\
=\ & \text{maximize } \sum_{u \in \mathcal{U}_0} (\text{유저 } u \text{가 그날 경험한 총 대화 시간})
\end{aligned}
$$

아자르 추천 시스템은 일정한 주기(틱)로 유저들을 모아 매칭을 수행합니다.
우리가 할 수 있는 것은 유저 $$u$$의 그날 경험을 제어하는 것이라기 보다는, 한 틱 안에 $$N$$명이 모여있을 때 그 $$N$$명의 사람들을 어떻게 매칭시켜줄지를 제어하는 것에 가깝습니다. 

$$\textbf{Assumption 8.}$$ 각 틱은 독립적인 매칭 라운드로 한 틱에서의 매칭 결과가 다른 틱의 매칭에 영향을 주지 않는다.

각 틱이 독립적이라고 가정하면, 임의의 틱 $$t$$에 대해 그 틱 안의 유저 $$u \in \mathcal{U}_0^t$$가 경험한 대화 시간을 최대화하는 문제로 완화할 수 있다고 볼 수 있습니다. 

$$
\begin{aligned}
& \text{maximize } (\text{long-term-revenue}) \\
=~& ... \\
=\ & \text{maximize } \sum_{u \in \mathcal{U}_0} (\text{유저 } u \text{가 그날 경험한 총 대화 시간}) \\
=\ & \text{maximize } \sum_{u \in \mathcal{U}_0^t} (\text{유저 } u \text{가 틱 } t \text{ 안에서 경험한 대화 시간})
\end{aligned}
$$

이제 이 최적화 문제를 그래프 이론의 관점에서 재해석해봅시다.
아자르의 매칭 시스템은 각 유저를 정확히 한 명의 피어 유저와 1:1로 매칭시킵니다.
즉, 틱 $$t$$에 모인 $$|\mathcal{U}_0^t|$$명의 유저들을 $$\lfloor |\mathcal{U}_0^t|/2 \rfloor$$개의 쌍으로 나누는 것입니다.
유저 $$u$$가 피어 $$p$$와 매칭되면, 유저 $$u$$가 틱 $$t$$ 안에서 경험하는 대화 시간은 $$u$$와 $$p$$ 간의 대화 시간과 동일합니다.
따라서 전체 대화 시간의 합은 모든 매칭된 쌍 $$(u, p)$$의 대화 시간의 합과 같습니다.
이를 그래프로 모델링하면 다음과 같습니다:

- 각 유저 $$u \in \mathcal{U}_0^t$$를 그래프의 노드로 표현합니다.
- 임의의 두 유저 $$u$$와 $$p$$ 사이에 간선(edge)을 그립니다.
- 간선의 가중치(weight)는 두 유저가 만났을 때의 대화 시간으로 설정합니다.

이제 "모든 매칭된 쌍의 대화 시간 합을 최대화"하는 문제는, 그래프에서 각 노드가 최대 하나의 간선에만 포함되도록 간선들을 선택하여 선택된 간선들의 가중치 합을 최대화하는 문제가 됩니다.
이것이 바로 최대 가중치 매칭(maximum weight matching) 문제입니다.
최대 가중치 매칭 문제를 최적으로 풀기 위해서 Blossom 알고리즘 등 다양한 방법들이 존재합니다.
하지만, 문제를 더 쉽게 만들기 위해 아래 가정을 추가합니다.

$$\textbf{Assumption 9.}$$  탐욕(greedy) 알고리즘을 통해 최대 가중치 매칭 문제를 푼다.

다행히도 $$\textbf{Assumption 9}$$는 과도하게 강한 가정은 아닙니다.
탐욕 알고리즘이 최적해의 간선 가중치 합의 절반 이상을 보장한다는 것이 이론적으로 증명되어 있기 때문입니다.

마지막으로, 간선 가중치를 정확히 계산하기 위해서는 두 유저가 만났을 때의 대화 시간을 알아야 합니다.
하지만 두 유저가 실제로 만나기 전까지는 이 값을 알 수 없습니다.
따라서 $$\mathcal{U}_0^t$$의 임의의 두 유저가 만났을 때 얼마나 오래 대화할지 예측하는 문제를 풀어야 합니다.
$$\textbf{Assumption 9}$$에 따라 예측된 대화 시간이 높은 순서대로 탐욕 알고리즘으로 매칭을 수행한다면, 대화 시간 예측기의 예측 오차를 최소화하는 것이 전체 대화 시간 합을 최대화하는 것과 동일한 문제가 됩니다.

$$
\begin{aligned}
&\text{maximize } (\text{long-term-revenue}) \\=~& \dots \\
=\ & \text{maximize } \sum_{u \in \mathcal{U}_0^t} (\text{유저 } u \text{가 틱 } t \text{ 안에서 경험한 대화 시간}) \\
=\ & \text{minimize } \sum_{u,p,c \in \mathcal{D}} \mathcal{L}(c, f(u,p)) 
\end{aligned}
$$

결국, 장기 매출 최대화 문제는 굉장히 많은 가정들을 통해 대화 시간 예측기를 만드는 문제로 변화합니다.
이 최종 형태는 많은 AI PM이나 연구자들이 직관적으로 생각하는 접근법과 동일합니다.
하지만 중요한 차이점은, 우리가 어떤 가정들을 통해 이 문제로 도달했는지를 명시적으로 알고 있다는 것입니다.
흔히 추천 시스템에서 "CTR이나 시청 시간 같은 1차 지표를 올리는 것과 비즈니스 임팩트는 큰 관계가 없다"는 지적이 나오곤 하는데요, 이런 현상이 발생하는 이유는 우리가 만든 암시적 가정 중 일부가 현실에서 동작하지 않기 때문입니다.
어떤 가정이 깨졌는지, 그리고 그에 따라 어떻게 문제를 재정의해야 하는지를 이해해야만 비로소 비즈니스 임팩트를 만들어낼 수 있습니다.

## 그럼, 위에서 도출한 9개의 가정을 바탕으로 아자르에 적용했을 때 결과는 어떻게 됐을까요?

아래 그림에서 볼 수 있 듯 리텐션은 사상 최고치를 기록했습니다. 
이 결과를 통해 $$\textbf{Assumption 3-9}$$는 어느 정도 성립했다고 볼 수 있습니다.
리텐션이 올라갔다는 것은 이 가정들이 현실과 부합했다는 의미이기 때문입니다.
하지만, PUR(Purchase User Rate)이 떨어졌습니다.
$$\textbf{Assumption 2}$$에서는 $$\text{DAU}_N$$을 변화시켜도 $$\text{PUR}_N$$이 변하지 않는다고 가정했지만, 실제로는 리텐션을 올리면서 PUR이 함께 변화했습니다. 

![retention-pur-over-time]({{ "/assets/2026-01-12-how-to-relax-a-business-problem/retention-pur-over-time.png" | absolute_url }}){: width="80%" .center-image }

## 그럼 이제 어떻게 해야 할까요?

$$\textbf{Assumption 2}$$가 필요 없도록 문제를 재정의해야 합니다.
이를 위해 장기 매출을 다른 방식으로 분해해보겠습니다.
원래 $$\text{DAU}_N \times \text{PUR}_N \times \text{ARPPU}_N$$로 분해했던 것을, 이번에는 $$\text{purchase-user}_N \times \text{ARPPU}_N$$로 분해하겠습니다.
여기서 $$\text{purchase-user}_N$$는 $$N$$일차의 일일 구매자 숫자를 의미합니다.
이렇게 분해하면 구매자의 리텐션을 올리는 문제로 접근할 수 있으며, 비슷한 가정들을 적용하면 아래와 같이 장기 매출 최적화 문제를 완화할 수 있습니다. 

$$
\begin{aligned}
\text{maximize } &(\text{long-term-revenue}) \\
=\ & \text{maximize } (\text{revenue}_N) \\
=\ & \text{maximize } (\text{purchase-user}_N \times \text{ARPPU}_N) \\
=\ & \text{maximize } (\text{purchase-user}_N) \\
=\ & \text{maximize } (\text{purchase-user-retention}_0) \\
=\ & \text{maximize } (\text{purchase-user}_N \text{ 중에 } X \text{분 이상 채팅한 유저의 비율}) \\
=\ & \text{maximize } (\text{purchase-user}_N \text{ 중에 } X \text{분 이상 채팅한 유저의 수}) \\
=\ & \text{maximize } \sum_{u \in \mathcal{U}_{0, \text{purchase-user}}} (\text{유저 } u \text{가 그날 경험한 총 대화 시간}) \\
=\ & \text{maximize } \sum_{u \in \mathcal{U}^{t}_{0, \text{purchase-user}}} (\text{유저 } u \text{가 틱 } t \text{ 안에서 경험한 대화 시간}) \\
=\ & \text{minimize } \sum_{u,p,c \in \mathcal{D}_{\text{purchase-user}}} \mathcal{L}(c, f(u,p)) 
\end{aligned}
$$

이렇게 문제를 재정의하면서, 구매자에 대한 대화 시간 예측기의 성능이 핵심적인 역할을 하게 되었습니다.
비즈니스 목표가 DAU 최대화에서 purchase-user 수 최대화로 전환됨에 따라, 예측 모델의 정확도가 최종 매출에 직접적으로 영향을 미치는 핵심 요인이 되었습니다.
문제를 재정의하여 적용한 결과, 아래 그림과 같이 비즈니스 지표에서 유의미한 개선을 확인할 수 있었습니다.
이 성과는 매치 그룹의 2023 2Q 주주서한에도 공개되었습니다.

![earnings-letter-2023-2q]({{ "/assets/2026-01-12-how-to-relax-a-business-problem/earnings-letter-2023-2q.png" | absolute_url }}){: width="80%" .center-image }

현재 추천 모델은 3년여의 시간이 지난만큼 더 강력해졌습니다. 
최근 모델에 대한 소개는 다른 블로그 포스트를 통해 소개드릴 예정입니다.

## 마치며

명시적 가정을 통해 문제를 완화하는 접근법의 가장 큰 장점은 문제가 발생했을 때 디버깅을 용이하게 한다는 것입니다.
이 사례에서는 $$\textbf{Assumption 2}$$만 깨졌고 이를 보정하여 성과를 낼 수 있었지만, 현실은 이보다 훨씬 복잡합니다.

여러 가정이 동시에 깨지는 경우가 빈번하며, 이때 어떤 가정부터 수정해야 할지 우선순위를 정해야 합니다.
또한 사용자 제품은 마케팅이나 외부 요인으로 인해 본질적으로 비정상성(non-stationary) 분포를 따르기 때문에, 한 번 성립했던 가정이 계속 유효하다고 보장할 수 없습니다.
따라서 원래 잘 작동하던 알고리즘이 갑자기 성능이 저하되는 경우도 발생합니다.
이런 상황에 대비해 기존 가정들이 여전히 유효한지, 가정이 깨졌더라도 원래 문제는 잘 해결되고 있는지를 지속적으로 모니터링하는 시스템이 필요합니다.

가정은 AI 문제에서 일종의 기술 부채입니다.
가정들은 모니터링이 지속적으로 필요할 뿐만 아니라, 추상화에 의한 레이어링을 만들어 최적 솔루션에 도달하기 어렵게 만들기도 하기에 우리는 이를 기술 부채로 바라봐야 합니다. 
가정을 제거하면 제거할수록, 우리가 원하는 장기 매출 최적화에 더 가까워지고 더 견고한 시스템을 구축할 수 있습니다.
예를 들어, $$\textbf{Assumption 7}$$은 매우 강력한 가정이며, 이를 다른 방식으로 완화하면 더 나은 해를 찾을 수 있습니다.
실제로 추천 시스템 분야에서는 강화학습(RL) 등을 활용해 리텐션을 직접적으로 최적화하는 연구가 활발히 진행되고 있으며, 특히 빅테크 기업들에서 이런 방향으로 많은 연구가 이미 공개되어있습니다. 

비즈니스 문제를 AI 문제로 치환하는 과정은 본질적으로 '무엇을 가정하고', '어떻게 단순화할 것인가'를 결정하는 작업입니다.
모델을 만드는 것 자체는 점점 쉬워지고 있습니다. 
진짜 어려운 것은 모델을 만들었을 때 원하는 비즈니스 목표가 달성되지 않았을 때, 왜 달성되지 않았는지를 파악하고 문제를 재정의하는 것입니다.
하이퍼커넥트 AI는 명시적인 가정을 통해 비즈니스 문제를 AI 문제로 완화하고, 이러한 가정들을 지속적으로 검증하고 관리함으로써 비즈니스 임팩트를 만들어가고 있습니다.

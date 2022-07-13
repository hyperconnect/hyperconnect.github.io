---
layout: post
date: 2022-07-11
title: 머신러닝 어플리케이션을 위한 데이터 저장소 기술
author: owen.l
tags: machine-learning data-store
excerpt: 머신러닝 어플리케이션의 데이터 사용 패턴을 분석하고, 데이터 사용 패턴에 적합한 데이터 저장소엔 어떠한 것들이 있는지에 대해서 소개합니다.
cover_image: "/assets/2022-07-11-data-stores-for-ml-apps/cover.png"
last_modified_at: 2022-07-11
---

하이퍼커넥트는 내부적으로 다양한 머신러닝 기반의 어플리케이션을 운용 중입니다. 개인화 추천 시스템, 실시간 이상 유저 탐지 시스템, 검색 엔진, 챗봇 등 머신러닝 모델을 메인으로 하는 어플리케이션들이 이에 해당하죠.

이런 머신러닝 어플리케이션에서 데이터는 각별한 의미를 가집니다. 컴퓨터 비전, 자연어 처리, 추천 시스템 등 분야를 가리지 않고 데이터가 많으면 많을수록 머신러닝 모델의 성능은 더 높아지고 있으며, 세계적인 기업들은 더 많은 데이터 수집에 투자를 아끼지 않고 있습니다. 하지만 더 많은 데이터를 수집할수록, 저장과 관리를 어떻게 해야 할지에 대한 고민이 생겨나기 시작합니다. **어떤 데이터 저장소를 사용하는지에 따라 머신러닝 어플리케이션의 성능과 개발 속도가 달라질 수도 있기 때문**입니다.

특히 추천 시스템 처럼 테이블 형태(tabular)의 데이터를 많이 사용하는 어플리케이션에서는 모델 “**학습**” 로직에서의 데이터 사용 패턴과 모델 “**서빙**” 로직에서의 **데이터 사용 패턴**이 현저하게 다릅니다. 데이터의 사용 패턴이 달라지면 데이터 저장소 기술도 달라져야 합니다. 데이터 저장소를 잘못 사용하게 된다면 어플리케이션의 응답 시간이나 처리 시간이 낮아질 수 있기 때문이죠. 기존 백엔드 어플리케이션을 개발하면서는 고려하지 않았던 모델 “학습"과 “서빙"의 데이터 사용 패턴 차이 문제를 해결하기 위한 저장소에 대한 고민이, 머신러닝 어플리케이션 개발에서는 매우 중요해지고 있습니다.

이번 포스트에서는 머신러닝 어플리케이션을 위한 데이터 저장소 기술에 대해 다루어보려 합니다. 머신러닝 어플리케이션의 데이터 사용 패턴을 분석하고, 또 데이터 사용 패턴에 적합한 데이터 저장소엔 어떠한 것들이 있는지에 대해서 소개합니다. 또한 하이퍼커넥트는 어떤식으로 머신러닝을 위한 데이터를 저장하고 관리하는지도 함께 공유해드리고자 합니다.


# 머신러닝 어플리케이션에서의 데이터 사용 패턴

대부분의 머신러닝 어플리케이션에서는 **모델 학습 로직**과 **모델 서빙 로직**이 분리됩니다.

- **학습 로직:** 수집된 데이터를 불러오고 가공한 뒤, Tensorflow, PyTorch 등의 머신러닝 프레임워크를 이용하여 모델을 학습
- **서빙 로직:** 온라인에서 필요한 데이터를 불러온 후, 해당 데이터를 입력으로 하여 머신러닝 모델을 추론하고, 그 결과를 제품이나 서비스에서 활용

비전 모델과 같이 입력이 이미지 바이너리인 경우에는, 모델 추론을 위해 데이터 저장소에서 통계 정보와 같은 추가적인 데이터를 불러올 필요가 없기 때문에 서빙 로직에서 별도의 데이터 저장소가 필요하지 않을 수 있습니다. 하지만 추천 시스템과 같은 머신러닝 어플리케이션에서는 서빙 로직에서 모델 추론을 위해 온라인 데이터를 불러와야 합니다. 예를 들어 사용자라면 성별, 국가 코드, 생일, 가입 날짜, 평균 구매 금액 등이 있을 수 있고, 상품이라면 가격, 카테고리, 구매 횟수 등이 모델 추론 시 사용되는 온라인 데이터라고 할 수 있습니다.

이처럼 머신러닝 어플리케이션은 학습 로직과 서빙 로직이 분리되고, 각각의 로직에서 데이터 읽기가 필요할 수 있습니다. 다만 **학습 로직**에서의 데이터 읽기 패턴과 **서빙 로직**에서의 데이터 읽기 패턴은 매우 다릅니다. 학습과 서빙 로직에서의 데이터 읽기 패턴에 대해서 정리를 해보자면 아래와 같습니다.

|  | 학습 데이터 | 서빙 데이터 |
| --- | --- | --- |
| 읽기 패턴 | Timestamp 기반의 다수 레코드 접근 | 키 기반의 특정 레코드 접근 |
| 질의 주기 | 가끔. 주기적 | 매우 자주 |
| 지연 시간 (latency) | 상관없음 | 빨라야 함 |
| 쿼리당 처리량 (throughput) | 높아야 함 | 상관없음 |

학습 로직과 서빙 로직의 데이터 사용 패턴을 모두 만족시키는 데이터 저장소를 구현하기란 매우 어렵습니다. 키 기반의 특정 레코드 접근 시에는 빠른 응답 시간을 보여주면서, timestamp 기반의 다수의 레코드 접근 시에는 높은 처리량과 저렴한 비용으로 쿼리 수행이 가능한, 그러면서도 갑자기 다수의 레코드를 읽는 쿼리를 수행하더라도 특정 레코드를 읽는 다른 쿼리들에 성능 저하를 가져오지 않는 저장소를 구현하기란 쉽지 않기 때문이죠.

이러한 이유로 많은 머신러닝 어플리케이션에선 학습을 위한 데이터와 서빙을 위한 데이터를 서로 다른 저장소에 저장하고 있습니다.


# 모델 학습을 위한 저장소

앞선 문단에서 모델 학습을 위한 데이터 읽기 패턴에 대해 소개를 해드렸습니다. 머신러닝 자체는 최근 기술이고, 학습이라는 개념 또한 최근 등장했지만, 정말 모델 학습에서의 데이터 읽기 패턴은 새로운 것일까요? 사실 그렇지 않습니다. **모델 학습 로직에서의 데이터 읽기 패턴**은 사실 **데이터 분석 작업에서의 데이터 읽기 패턴과 유사**합니다.

### 데이터 웨어하우스

데이터 분석 작업에서 사용되는 저장소는 OLAP (Online Analytic Processing) 혹은 데이터 웨어하우스(Data Warehouse)라고 불립니다. 이는 1980년대부터 존재했던 개념으로 [1], 오랜 시간동안 검증되었고 이미 상용화 단계를 거친 기술이라고 할 수 있습니다.

데이터 웨어하우스는 데이터 분석 등을 거쳐 최종적으로 **비즈니스 의사결정**을 하기 위한 저장소로 만들어졌습니다. 데이터 웨어하우스가 생겨나기 이전에도 비즈니스 의사결정을 위한 니즈는 존재했습니다. 하지만 비즈니스 의사결정을 위해 프로덕션 데이터베이스에 쿼리를 수행하게 되면, 프로덕션 데이터베이스가 마비되거나 응답시간이 튀는 일이 잦았습니다. 분석용 쿼리를 수행하기까지 시간이 오래 걸린다는 단점도 존재했구요.

이러한 문제로 인해 비즈니스 의사결정을 위한 쿼리용 데이터 저장소로 등장한 것이 데이터 웨어하우스입니다. 대표적인 데이터 웨어하우스엔 Google Cloud의 BigQuery가 있습니다.

### 데이터 웨어하우스와 모델 학습 로직

모델의 학습 로직과 비즈니스 의사결정을 위한 데이터 분석 작업은 매우 유사한 데이터 사용 패턴을 가지고 있습니다.

- 대부분의 쿼리가 다수의 레코드에 동시에 접근
- 지연 시간 (latency)은 크게 중요하지 않음
- 쿼리당 처리율 (throughput)은 높으면서 비용은 낮아야 함

데이터 사용 패턴이 비슷하기 때문에 **모델 학습 로직**에서도 데이터 분석을 위해 만들어진 **데이터 웨어하우스를 사용하는 것은 적합**하다고 할 수 있습니다.

### 데이터 웨어하우스의 구현

그렇다면 데이터 웨어하우스는 어떻게 구현되어 있을까요? 구현을 이야기하기 앞서서, 데이터 웨어하우스에서 주로 사용되는 쿼리를 먼저 살펴보고자 합니다.

아래는 *데이터 분석/학습*에서 주로 사용될법한 쿼리입니다.

```sql
SELECT gender, count(*)
FROM user_profile
GROUP BY gender
```

반대로 *프로덕션 데이터베이스*에서 사용될법한 쿼리를 가져와볼까요?

```sql
SELECT *
FROM user_profile
WHERE user_id=1234
```

차이를 눈치채셨나요?

- *프로덕션 데이터베이스*에서 주로 사용되는 쿼리는 **“단일/소수 레코드 + 다수 컬럼 접근”** 이라는 특징을 가지고 있습니다.
- *데이터 분석/학습용*에서 주로 사용되는 쿼리는 **“다수 레코드 + 단일/소수 컬럼 접근”** 이라는 특징을 가지고 있습니다.

프로덕션 데이터베이스에서는 비즈니스 특성에 따라 같은 테이블 내에서도 자주 접근되는 레코드 (hot)와, 자주 접근되지 않는 레코드 (cold)가 나누어집니다. 이런 특성을 이용하여, 캐시(cache)를 사용하여 자주 접근되는 레코드에 대해 지연시간을 낮추는 기법을 주로 사용하기도 합니다. 하지만 **데이터 분석/학습용 쿼리에서는 캐시의 중요도가 낮습니다**. 대부분 다수 레코드에 대해 접근하며, 또 지연시간이 중요하지 않기 때문이죠. 

또 다른 재미있는 부분도 있습니다. 바로 데이터 분석/학습용 쿼리에서는 다수 컬럼이 아닌 단일/소수 컬럼에 대해서만 접근한다는 부분입니다. 이런 특성으로 인해 프로덕션 데이터베이스에서 행(row) 단위로 레코드를 저장했던 것과 달리, **데이터 웨어하우스에서는 주로 컬럼(column) 단위로 데이터를 저장**합니다.


### 컬럼 지향 저장소 (Column-oriented store)

![컬럼 지향 저장소]({{"/assets/2022-07-11-data-stores-for-ml-apps/column-oriented-store.png" | absolute_url}}){: width="600px" .center-image }

그림 1: 로우 지향(row-oriented) 저장소와 컬럼 지향(column-oriented) 저장소
{: style="text-align: center; font-style: italic;"}

위 그림과 같이 컬럼 지향 저장소와 로우 지향 저장소는 아래처럼 어떤 단위로 데이터를 저장하느냐에 따라 나뉘어집니다.

- **Row-oriented**: 로우(row) 단위로 데이터를 저장
- **Column-oriented**: 컬럼(column) 단위로 데이터를 저장

주로 로우 단위의 데이터를 접근한다면 컬럼 지향 저장소를 사용할 이유가 없지만, 주로 컬럼 단위의 데이터를 접근한다면 컬럼 지향 저장소는 좋은 선택지입니다. 컬럼 지향 저장소는 기본적으로 테이블에 많은 컬럼이 있을수록 유리합니다. 필요한 컬럼만 조회시 리소스가 더 절약될 수 있기 때문이죠. 다만 컬럼 지향 저장소에서 단일 레코드에 대한 검색은 매우 비효율적입니다. 단일 레코드를 가져오기 위해선 전체 테이블 스캔(scan)이 필요하기 때문이죠.

검색에 대한 특징 말고도, 기본적으로 컬럼 지향 저장소는 **압축 효율이 좋다는 특징**도 가지고 있습니다. 압축 효율이 좋은 이유는 일반적으로 로우 데이터보다 컬럼 데이터가 데이터 중복성이 높기 때문입니다 [[2]](https://cloud.google.com/bigquery/docs/storage_overview#storage_layout). 대표적인 데이터 웨어하우스인 BigQuery도 컬럼 지향으로 디자인되어 있습니다. 데이터 분석 / 학습에서 주로 사용되는 쿼리 패턴에도 잘 맞고, 압축 효율도 좋은 것이 주된 이유죠.

### 컬럼 지향 저장소에서의 파티셔닝 (partitioning)

앞선 설명만 들으면 컬럼 지향 저장소는 데이너 분석용에서 만능처럼 보이지만, 사실 큰 문제가 하나 존재합니다. 바로 **시간이 지날수록 레코드의 수는 계속 늘어난다**는 점입니다.

일반적으로 데이터 웨어하우스에는 로그 형태의 데이터를 쌓게 됩니다. 매일 새로운 로그 데이터가 저장소에 쌓이게 될 텐데, 컬럼 지향 저장소에서는 조회 시 항상 모든 레코드를 스캔하게 됩니다. 컬럼 숫자는 쿼리로 인해 고정되어 있더라도 레코드 자체가 계속 쌓이기 때문에, 시간이 지나면서 같은 쿼리라고 하더라도 읽게 되는 행의 숫자는 계속 늘어나게 되는 것이죠.

하지만 사실 오래된 데이터의 경우에는 분석 작업이나 모델 학습 작업에 자주 사용되지는 않습니다. 그렇다면 모든 레코드에 대한 스캔은 너무 비효율적이지 않을까요? 이 문제를 해결하기 위해 주로 파티셔닝(partitioning)이 사용됩니다.

![컬럼 지향 저장소의 파티셔닝]({{"/assets/2022-07-11-data-stores-for-ml-apps/bigquery-partitioning.png" | absolute_url}}){: width="700px" .center-image }

그림 2: 날짜 필드로 파티션을 나눈 테이블. 출처: [Google Cloud](https://cloud.google.com/bigquery/docs/storage_overview#partitioning)
{: style="text-align: center; font-style: italic;"}

파티셔닝은 컬럼 지향 저장소에서 물리적인 테이블을 특정 키를 기준으로 쪼개는 것을 말합니다. 파티셔닝은 인덱스(index)와 비슷하게 보일 수도 있지만, 단일 레코드 검색 최적화가 아닌 스캔 범위를 줄인다는 측면에서 다릅니다. 실제로 파티션을 설정하게 되면, 파티션 키에 따라서 물리적 테이블이 나누어지고, 테이블 내부적으로는 컬럼 지향으로 데이터를 저장합니다 [[3]](https://cloud.google.com/bigquery/docs/storage_overview#partitioning). 결과적으로 파티셔닝을 잘 활용하면, 많은 데이터가 저장소에 있어도 더 적은 레코드만 스캔하여 쿼리를 수행할 수 있습니다. 이를 통해 컬럼 지향 저장소가 갖는 한계를 어느 정도 해결할 수 있죠.

### 중간 정리

예전부터 프로덕션용 데이터베이스와 분석용 데이터 스토어를 같이 사용하면 응답시간이 튀거나 비용이 많이 드는 문제가 발생했습니다. 이 문제를 해결하기 위해 업계에서는 데이터 웨어하우스라고 불리는 분석용 저장소를 따로 만들어서 사용하고 있었죠. 데이터 웨어하우스는 주로 컬럼 지향으로 구현되어 있으며, 파티셔닝을 통해 레코드 스캔에 대한 부담을 줄이고 있습니다.

머신러닝 어플리케이션의 학습 로직은 기본적으로 데이터 분석 작업과 데이터 사용 패턴이 유사합니다. 따라서 학습 로직에서 데이터 웨어하우스를 사용하는 것은 적합하다고 볼 수 있습니다. 다만 데이터 웨어하우스는 독특한 방식으로 구현되어 있기 때문에, **컬럼 지향적 특성을 고려하고 파티셔닝을 잘 활용하여 효율적으로 사용하는 것이 중요**합니다. 이것만 기억하면 모델 학습을 위한 저장소에 대해서는 큰 고민은 덜었다고 할 수 있습니다.


# 모델 서빙을 위한 저장소

이제 머신러닝 모델을 **서빙**할 때 필요한 저장소에 대해서 생각해 봅시다. 먼저 서빙 데이터는 앞에서 말했듯이 키 기반의 특정 레코드 접근이 대부분이고, 질의 주기가 매우 짧으며, 지연시간은 낮아야 합니다. 서빙 데이터의 이런 특징으로 인해, 데이터 웨어하우스는 모델 서빙 로직에서 사용할 수 없습니다. 느린 응답시간과 비싼 비용(record scan)이 문제가 되기 때문이죠.

모델 서빙을 위한 저장소로는 OLTP (Online Transaction Processing) 데이터베이스를 사용할 수 있습니다. OLTP는 요즘은 잘 쓰지 않는 용어로, 초창기 웹을 통해 “상거래”를 구현하기 위해 만들어진 저장소라서 트랜잭션이라는 이름이 붙었습니다 [1]. 이후 웹은 상거래용을 넘어서 많이 확대되었지만, 여전히 같은 유형의 데이터베이스를 사용 중입니다. **머신러닝 어플리케이션도 상거래와는 거리가 멀지만, 서빙 데이터의 사용 패턴은 여전히 상거래와 비슷합니다.** 따라서 이런 데이터베이스를 그대로 서빙 로직에서 사용할 수 있죠.

Transactional 데이터베이스에서 주로 등장하는 개념들에는 아래 정도가 있습니다.

- RDBMS vs NOSQL
- CAP Theorem
- B-Tree vs LSM-Tree
- In-memory store

위 개념들에 대해 잘 이해하고 있어야, 머신러닝 어플리케이션에서 모델 서빙을 위한 저장소를 효율적으로 운용할 수 있습니다. 그렇다면 각각에 대해서 더 알아보도록 합시다.

### RDBMS vs NOSQL

현대의 온라인 데이터베이스는 주로 RDBMS와 NOSQL로 나누어집니다. RDBMS와 NOSQL은 꽤 긴 기간 동안 많은 사람들이 이야기했던 주제입니다. 그만큼 많은 자료들이 공개되어 있기에 짧게 정리하고 넘어가려고 합니다. 아래 표는 RDBMS와 NOSQL를 비교하여 정리한 결과입니다.

|      | RDBMS | NOSQL |
| ----- | --- | --- |
| 스키마 | 주로 엄격하며, 사전에 정의됨(predefined) [[4](https://www.mongodb.com/scale/nosql-vs-relational-databases)] | 유연함 [[4](https://www.mongodb.com/scale/nosql-vs-relational-databases),[5](https://docs.microsoft.com/ko-kr/dotnet/architecture/cloud-native/relational-vs-nosql-data)] |
| 구현  | 정규화된 테이블 형태로, 테이블을 조인하는 방식의 구현 [[5](https://docs.microsoft.com/ko-kr/dotnet/architecture/cloud-native/relational-vs-nosql-data)] | Document-based, graph databases, key-value pairs,<br> wide-column stores [[4](https://www.mongodb.com/scale/nosql-vs-relational-databases),[5](https://docs.microsoft.com/ko-kr/dotnet/architecture/cloud-native/relational-vs-nosql-data)] |
| ACID | 보장 [[5](https://docs.microsoft.com/ko-kr/dotnet/architecture/cloud-native/relational-vs-nosql-data)] | 일반적으로 보장하지 않음 [[5](https://docs.microsoft.com/ko-kr/dotnet/architecture/cloud-native/relational-vs-nosql-data)] |
| 예시  | MySQL, MariaDB, Oracle, PostgreSQL | MongoDB, Cassandra, DynamoDB, (Redis) |

### CAP 정리

CAP 정리 (CAP theorm)는 다음과 같은 세 가지 조건을 모두 만족하는 분산 컴퓨터 시스템은 존재할 수 없음을 증명한 정리입니다 [[6]](https://ko.wikipedia.org/wiki/CAP_%EC%A0%95%EB%A6%AC).

- **일관성(Consistency):** 모든 노드가 같은 순간에 같은 데이터를 볼 수 있다 *(최신 데이터 반환)*.
- **가용성(Availability):** 모든 요청이 성공 또는 실패 결과를 반환할 수 있다 *(읽기/쓰기가 오류 없이 항상 가능)*.
- **분할내성 (Partitio- tolerance)**: 메시지 전달이 실패하거나 시스템(네트워크) 일부가 망가져도 시스템이 계속 동작할 수 있다.

모든 데이터베이스는 일관성, 가용성, 분할내성 중에 두 가지만 보장할 수 있으며, 데이터베이스의 설계 목적에 따라서 세 가지 중 어떤 것을 trade-off 할지 결정하게 됩니다.

![CAP 정리]({{"/assets/2022-07-11-data-stores-for-ml-apps/cap-theorm.png" | absolute_url}}){: width="300px" .center-image }

그림 3: CAP 정리. [출처](https://hazelcast.com/glossary/cap-theorem/)
{: style="text-align: center; font-style: italic;"}


**CA (Consistency + Availability)**에 해당하는 데이터베이스는 분할내성(Partition-tolerance)을 포기했다고 할 수 있습니다. 분할내성을 포기했다는 말은 시스템이나 네트워크 장애가 발생하지 않는다는 것을 가정한 것을 의미합니다. 따라서 일반적으로 **단일 노드**로 구성된 데이터베이스만을 CA 구성이라고 하며, 이 구조에서는 Scale-up으로만 트래픽 변화에 대응할 수 있습니다. 하지만 단일 노드 구성은 비현실적이기 때문에, CA 시스템은 현실적으로 불가능하다는 주장도 있습니다 [[7]](https://codahale.com/you-cant-sacrifice-partition-tolerance/).

**CP (Consistency + Partition Tolerance)**에 해당하는 데이터베이스는 가용성(Availability)를 포기했다고 할 수 있습니다. 이 시스템에서는 항상 최신 데이터 반환을 보장하지만, 일부 노드 장애 시 일시적으로 읽기나 쓰기가 동작하지 않을 수 있습니다 [[8]](https://www.analyticsvidhya.com/blog/2020/08/a-beginners-guide-to-cap-theorem-for-data-engineering/). 대표적인 CP 데이터베이스에는 MongoDB, Big Table, Hbase, Redis가 있습니다.

**AP (Availability + Partition Tolerance)**에 해당하는 데이터베이스는 일관성(Consistency)를 포기했다고 할 수 있습니다. 이 시스템에서는 일부 노드 장애 시에도 읽기/쓰기가 가능하지만, 최신 데이터를 반환하지 않을 수 있습니다 [[8]](https://www.analyticsvidhya.com/blog/2020/08/a-beginners-guide-to-cap-theorem-for-data-engineering/). AP에 해당하는 데이터베이스는 완전한 일관성을 보장하지는 않지만, 일반적으로 **최종 일관성** (Eventual Consistency)은 보장합니다. 최종 일관성이란 일시적으로는 일관성이 깨질 수 있지만, 시간이 지나면 결과적으로 일관성이 보장된다는 개념입니다. 대표적인 AP 데이터베이스에는 Cassandra, DynamoDB, CouchDB가 있습니다.

### B-Tree vs LSM-Tree

앞선 개념들은 데이터베이스의 설계 철학과 가깝다고 볼 수 있습니다. 그렇다면 실제 데이터베이스의 내부 구현은 어떻게 되어있을까요? 대부분의 디스크 기반 데이터베이스는 B-Tree 혹은 LSM-Tree로 구현되어 있습니다. 

|  | B-Tree | LSM-Tree |
| --- | --- | --- |
| 유형 | Page-oriented | Log-structured |
| 등장 시기 |  1970년대 등장 | 최근 떠오르고 있음 (90년대 제안. 2000년대 이후 상용화) |
| 성능 | 안정된 읽기/쓰기 성능 | 빠른 쓰기 성능 (읽기는 상대적으로 느림) |
| 예시 | MySQL, MongoDB | Cassandra, LevelDB, RocksDB, BigTable |

**B-Tree는** Binary Search Tree, AVL Tree, Red-Black Tree 등과 같은 검색을 위한 자료구조입니다. B-Tree의 검색 및 삽입 시간 복잡도는 모두 O(log N)이며, 보장된 검색/삽입 성능을 보장합니다. B-Tree가 다른 검색 트리와 다른 점은 노드의 크기가 주로 4 KB로 설정된다는 점입니다. 4 KB라.. 익숙한 숫자 아닌가요? 32비트 운영체제의 Page 크기가 바로 4 KB입니다. B-Tree는 디스크에서 메모리로 데이터를 로드하는 작업을 최적화하기 위해 노드의 크기를 운영체제의 Page 크기와 맞춘 자료구조입니다. 이 때문에 page-oriented 데이터베이스라고도 불리죠.

![B-Tree 예시]({{"/assets/2022-07-11-data-stores-for-ml-apps/b-tree.jpg" | absolute_url}}){: width="600px" .center-image }

그림 4: B-Tree 예시. 출처: [1]
{: style="text-align: center; font-style: italic;"}

B-Tree에는 또 다른 중요한 개념이 있습니다. 바로 WAL (Write-ahead Log)입니다. B-Tree 기반의 데이터베이스에 삽입 명령이 들어오면, 트리의 어떤 노드에 데이터를 삽입할지 검색한 후 새로운 데이터를 쓰게 되며, 적합한 공간이 없다면 새로운 노드를 만들거나 필요에 따라 노드 리밸런싱을 수행하게 됩니다. 하지만 다양한 이유로 삽입 과정에서 트리가 망가질 수 있습니다.

트리가 망가진 상황에서 복구를 할 수 있도록 B-Tree 기반의 데이터베이스에서는 **대부분 삽입 연산전에 로그를 기록**합니다 (Write-ahead Log). 로그는 append 방식으로 쓰이기 때문에 인덱스가 망가질 가능성이 없어서 원본 데이터를 보장한다는 측면에서는 훨씬 안전합니다. WAL은 보편적인 구현이지만, 이 특성으로 인해 삽입 명령 하나를 처리하기 위해 B-Tree 기반의 데이터베이스는 최소 두 번의 디스크 쓰기 연산을 수행해야 합니다. 디스크 쓰기는 읽기보다 훨씬 비싼 작업입니다. B-Tree 기반의 데이터베이스에서 검색과 삽입의 시간 복잡도가 모두 O(log N)이라고 하더라도, 쓰기가 더 느린 이유에는 이런 이유가 있죠.

**LSM-Tree (Log-structured Merge Tree)**는 In-place 업데이트를 수행하는 B-Tree와 다르게, append 방식으로 데이터를 쓰는 방식입니다. 이런 이유로 log-structured 라는 이름이 붙었습니다. 로그 기반으로 동작하는 만큼, LSM-Tree는 기본적으로 쓰기 성능이 우수합니다. 하지만 문제는 어떻게 검색 성능을 보장할까에 있습니다.


![LSM-Tree]({{"/assets/2022-07-11-data-stores-for-ml-apps/scylla-lsm-tree.png" | absolute_url}}){: width="600px" .center-image }

그림 5: LSM-Tree 기반의 데이터베이스 구현 (출처: [Scylla](https://docs.scylladb.com/kb/compaction/))
{: style="text-align: center; font-style: italic;"}

LSM-Tree에서는 삽입 명령이 들어오면 일단 memtable이라고 불리는 메모리 캐시에 저장을 합니다. 캐시에 데이터가 어느 정도 차게 되면 배치로 묶은 후 정렬하여 블록 단위의 로그로 저장합니다 (flush). 이때 정렬된 블록 구조를 SSTable (Sorted String Table)이라고 합니다.

삽입 연산이 들어온 순차대로 로그에 데이터가 append 된다면 검색 시 모든 레코드를 스캔해야 합니다. 대신 완전히 랜덤 한 순서로 저장되지 않고 정렬된 블록(SSTable)이 쌓여있는 구조라면, SSTable들을 이용하여 더 빠른 검색을 구현할 수 있게 됩니다. SSTable을 통해 검색 성능을 더 높일 수는 있긴 하지만, 여전히 SSTable이 여러 개 존재하는 문제는 존재합니다 (그림 6-좌). SSTable의 숫자가 늘어난다면 검색 성능은 떨어질 수밖에 없죠.

![늘어나는 LSM-Tree과 병합]({{"/assets/2022-07-11-data-stores-for-ml-apps/sstable-advanced.jpg" | absolute_url}})

그림 6. 좌: 늘어나는 SSTable(좌). 우: LSM-Tree의 병합 (compaction) 과정. 출처: [1]
{: style="text-align: center; font-style: italic;"}

이 문제를 해결하기 위해 LSM-Tree에서는 SSTable들을 주기적으로 병합(merge) 하는 방법을 사용합니다 (그림 6-우). Log-structured Merge Tree라는 이름이 나온 이유가 이 때문이죠. 병합은 컴팩션(compaction)이라고도 불립니다. 병합 과정에서는 단순히 여러 블록을 합치는 일 이외에도, 중복되거나 삭제된 레코드를 지우는 일도 수행합니다. 덕분에 디스크에 기록되는 전체 데이터 크기를 줄여주는 효과도 얻을 수 있죠.

B-Tree와 LSM-Tree는 완전히 다른 방식으로 구현되어 있습니다. 구현이 다르기 때문에 장단점도 명확하죠. 더 많은 내용을 다루기엔 내용이 길어질 것 같아 이 포스트에서는 B-Tree와 LSM-Tree를 아주 간략하게만 설명했습니다. 더 정교하고 깊게 들어가면 틀린 부분들이 있을 수 있으며, 더 정확한 설명은 추가적인 자료들을 보시는 것을 추천드립니다.

### In-memory store

앞서 나온 B-Tree, LSM-Tree는 디스크 기반의 데이터베이스를 위한 구현체입니다. 디스크를 사용하지 않고, 모든 데이터를 메모리에 올려버린다면 구현에 대한 고민을 덜해도 되며, 또 매우 빠른 검색/삽입 성능을 보장할 수 있습니다. 다만 In-memory 저장소의 문제는 보통 가격과 지속성입니다. 저장소로 디스크(HDD, SDD) 대신 RAM을 사용해야 하는데, 일반적으로 RAM이 디스크보다 비쌉니다. 또 RAM의 특성상 전원이 꺼지면 데이터가 손실되기 때문에, 지속성(durability) 문제가 있을 수 있습니다.

현대에 와서는 메모리 비용이 낮아지며 In-memory store의 활용도가 높아지고 있습니다. 지속성 문제도 어플리케이션마다 요구사항이 다르기도 하고, 또 부분적인 지속성을 보장해 주는 기능을 제공하는 저장소도 있기 때문에 [[9]](https://redis.io/docs/manual/persistence/), 디스크 기반의 저장소를 대체해서 사용하거나 같이 사용되는 사례들이 증가하고 있습니다. 대표적인 In-memory store에는 Redis가 있습니다.

### 중간 정리

현재 온라인 데이터베이스는 본래 상거래(Transaction)를 위해 만들어졌지만, 머신러닝 어플리케이션의 **서빙 로직**도 **상거래용 어플리케이션들과 비슷한 데이터 사용 패턴**을 보이고 있기 때문에 온라인 데이터베이스를 그대로 사용할 수 있습니다. 

온라인 데이터베이스에는 정말 다양한 것들이 있습니다. 웹 어플리케이션들은 어떤 문제를 해결하는지에 따라 서로 다른 데이터베이스를 선택해 왔습니다. 머신러닝 어플리케이션 또한 다르지 않습니다. 데이터의 사용 패턴에 따라 적합한 데이터베이스를 선택하는 전략이 필요합니다. 하이퍼커넥트 AI Lab에서도 필요에 따라 다른 데이터 저장소를 사용하고 있습니다. 아래는 하이퍼커넥트 AI Lab에서 사용 중인 주요한 데이터 저장소들입니다.

- **MySQL**: RDBMS
- **MongoDB**: NOSQL, CP(가용성 포기), B-tree based, Persistent
- **Cassandra(ScyllaDB)**: NOSQL, AP(일관성 포기), LSM-tree based, Persistent
- **Redis:** (NOSQL), In-memory

MySQL과 같은 RDBMS는 확장성(scalability)이 아주 중요하지 않으면서 강력한 스키마가 필요한 경우에 유용하며, MongoDB의 경우에는 유연한 스키마와 확장성을 필요로할 때 선택하기에 괜찮은 저장소입니다. Cassandra의 경우에는 빠른 쓰기 성능과 높은 확장성을 보이는 데이터베이스로, 쓰기 연산이 많은 머신러닝 어플리케이션에서 유용하죠. Redis는 주로 캐시로 많이 사용하며, 빠른 응답시간을 필요로하는 로직에서 사용하면 좋습니다. 하이퍼커넥트 AI Lab에서도 필요에 맞게 적합한 데이터베이스를 서빙용 데이터 저장소로 사용하고 있습니다.


# 피쳐 스토어 - 학습과 서빙 저장소를 통합하려는 움직임

앞선 섹션들을 읽다보면 학습용 저장소와 서빙용 저장소를 분리하는 것은 필수적으로 느껴집니다. 하지만 머신러닝 어플리케이션을 운용하다 보면, 두 저장소에 저장되는 데이터는 같아야한다라는 요구사항에 부딪힙니다. 데이터의 사용 패턴에 따라 적합한 학습용 저장소와 서빙용 저장소를 정했다고 하더라도, **두 데이터 저장소 간 일관성을 보장하는 것은 또 다른 어려움**을 야기합니다. 학습용 데이터 저장소에 피쳐를 삽입하는 로직과 서빙용 데이터 저장소에 피쳐를 삽입하는 로직이 따로 관리된다면, 같은 피쳐임에도 두 저장소 간에 서로 다른 데이터를 가질 수 있죠. 이는 Spofity와 같은 큰 기업에서도 겪은 문제입니다 [[10]](https://engineering.atspotify.com/2021/11/the-rise-and-lessons-learned-of-ml-models-to-personalize-content-on-home-part-i/). 

이 문제를 해결하기 위해 최근 등장하고 있는 개념이 피쳐 스토어 (Feature Store)입니다. 실제로는 머신러닝 어플리케이션을 위해 학습/서빙용 저장소를 따로 쓰지만, 저장소 앞에 새로운 추상화 계층을 추가하여 **하나의 저장소만 존재하는 것처럼 illusion을 주자는 것**이 피쳐 스토어의 핵심 개념이라고 할 수 있습니다.

![Feast 시스템 아키텍처]({{"/assets/2022-07-11-data-stores-for-ml-apps/feast-system-arch.png" | absolute_url}}){: width="550px" .center-image }

그림 7: 오픈소스 피처스토어 중 하나인 Feast의 시스템 아키텍처
{: style="text-align: center; font-style: italic;"}

현재 많은 기업들에서 피쳐 스토어를 공개하고 있습니다 (오픈소스 혹은 단순 포스트 공개). 하지만 아직 de-facto standard는 나오고 있지 않는 중이죠. 오픈소스 피쳐 스토어를 쉽게 적용하기도 어려운 게, 데이터를 사용하는 패턴이 회사마다 너무 다릅니다. 물론 언젠가는 대부분의 요구사항을 만족하는 오픈소스나 상용 피쳐 스토어가 등장하겠지만, 그때까지 기다리기엔 이미 데이터 저장소로 인한 여러 문제들을 겪고 있을 수 있습니다. 이러한 이유로 하이퍼커넥트 AI Lab에서도 내부적으로 단순하고 원시적인 형태의 피쳐 스토어를 운영 중이며, 필요에 따라 점진적으로 개선해나가고 있습니다.


# 결론

머신러닝 어플리케이션은 다양한 데이터 사용 패턴을 가지고 있고, 특히 학습 로직과 서빙 로직은 매우 다른 데이터 사용 패턴을 보이고 있습니다. 하지만 데이터 사용 패턴에 따라 알아서 다해주는 만능 데이터 스토어는 아직까지 없습니다. 결국 학습과 서빙 로직에서는 다른 데이터 저장소를 사용해야 하죠. 정리하자면 요즘 머신러닝 어플리케이션은 다양한 데이터 사용 패턴에 대응하기 위해 여러 데이터 저장소를 사용하는 대신, 여러 데이터 스토어를 사용하며 생기는 새로운 문제 (ex. 학습/서빙 데이터 일관성 문제)는 새로운 컴포넌트(ex. 피쳐스토어)로 해결하는 방향으로 발전하고 있다고 할 수 있습니다.

머신러닝을 더 잘하기 위한 조직으로 거듭나기 위해서는 소프트웨어 엔지니어링 기술이 뒷받침되어야 합니다. 하이퍼커넥트 AI Lab은 프로덕트 조직과 함께 다양한 글로벌 서비스들을 개발하고 있으며, 머신러닝 성능을 더욱 높이기 위해서 글로벌 스케일에서 오는 수많은 데이터를 어떻게 효율적으로 다룰 수 있을지와 같은 고민들도 하고 있습니다. 저희가 풀고 있는 다른 문제들도 궁금하신가요? 하이퍼커넥트 AI Lab에 합류하시면 더 다양한 문제를 풀어볼 수 있습니다!

- [Hyperconnect 채용공고 바로가기](https://career.hyperconnect.com/jobs/)
- [Machine Learning Software Engineer 채용공고 바로가기](https://career.hpcnt.com/job/6ff2687d-9a9a-431a-9f44-68432cfca156)


## References

[1] “Designing Data-Intensive Applications”, Martin Kleppmann, O’reilly

[2] [https://cloud.google.com/bigquery/docs/storage_overview#storage_layout](https://cloud.google.com/bigquery/docs/storage_overview#storage_layout)

[3] [https://cloud.google.com/bigquery/docs/storage_overview#partitioning](https://cloud.google.com/bigquery/docs/storage_overview#partitioning)

[4] [https://www.mongodb.com/scale/nosql-vs-relational-databases](https://www.mongodb.com/scale/nosql-vs-relational-databases)

[5] [https://docs.microsoft.com/ko-kr/dotnet/architecture/cloud-native/relational-vs-nosql-data](https://docs.microsoft.com/ko-kr/dotnet/architecture/cloud-native/relational-vs-nosql-data)

[6] [https://ko.wikipedia.org/wiki/CAP_정리](https://ko.wikipedia.org/wiki/CAP_%EC%A0%95%EB%A6%AC)

[7] [https://codahale.com/you-cant-sacrifice-partition-tolerance/](https://codahale.com/you-cant-sacrifice-partition-tolerance/)

[8] [https://www.analyticsvidhya.com/blog/2020/08/a-beginners-guide-to-cap-theorem-for-data-engineering/](https://www.analyticsvidhya.com/blog/2020/08/a-beginners-guide-to-cap-theorem-for-data-engineering/)

[9] [https://redis.io/docs/manual/persistence/](https://redis.io/docs/manual/persistence/)

[10] [https://engineering.atspotify.com/2021/11/the-rise-and-lessons-learned-of-ml-models-to-personalize-content-on-home-part-i/](https://engineering.atspotify.com/2021/11/the-rise-and-lessons-learned-of-ml-models-to-personalize-content-on-home-part-i/)

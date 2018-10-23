---
layout: post
title: 날짜 변환, 과연 그리 간단할까?
date: 2018-03-27
author: hwan
published: true
excerpt: 안드로이드에서 사용하는 SimpleDateFormat 클래스의 관대함(lenient)를 알아봅니다
tags: android tip
---

안드로이드에서는 입력한 날짜를 변환 및 검증하는 로직을 간단하게 구현하기 위해 SimpleDateFormat 클래스를 종종 활용하게 되는데 이 클래스는 규칙에 관대하다(lenient)는 재미난 특성이 있습니다. java.text.SimpleDateFormat 클래스의 근간이 되는 [java.text.DateFormat](https://developer.android.com/reference/java/text/DateFormat.html#parse(java.lang.String,%20java.text.ParsePosition)) 클래스의 다음 API 문서를 살펴봅시다.

> By default, parsing is lenient: If the input is not in the form used by this object's format method but can still be parsed as a date, then the parse succeeds. Clients may insist on strict adherence to the format by calling setLenient(false).

>파싱 기본 동작은 관대합니다. 이 객체의 날짜 포맷과 일치하지 않는 입력이 주어지더라도 날짜 형태만 유지한다면 파싱이 성공합니다. 클라이언트 코드에서는 setLenient(false) 메소드를 호출해 파싱 규칙을 여전히 엄격하게 가져갈 수 있습니다.

lenient 라는 흔하지 않은 단어 때문에 의미가 잘 와닿지 않습니다만, [캠브릿지 영영사전](https://dictionary.cambridge.org/dictionary/english/lenient)에 따르면 '관대하다' 라는 뜻이 있다고 하네요.

>lenient /ˈliː.ni.ənt/ ▶ adjective ▶ Level C2(Mastery Proficiency)

>A lenient punishment is not severe.

> Thesaurus: allowing, forgiving, merciful, permissive, tolerant

하지만 규칙에 관대하다는 말이 무슨 의미인지 여전히 와 닿지 않습니다. 잠시, 아래의 소스코드를 읽고 그 결과를 한번 예측해 볼까요? parse 메소드는 기본적으로 lenient 하다는 특성에 주의합시다.

```kotlin
/*
 * 2017년 13월 32일 이라는 입력에 대해 어떤 결과가 나타날까?
 * 1. 2017-13-32
 * 2. 2018-02-04
 * 3. 2017-01-01
 * 4. 2018-01-01
 * 5. ParseException 이 발생
 */
val userDate  = "2017-13-32"
val date      = SimpleDateFormat("yyyy-MM-dd").parse(userDate)
val localDate = LocalDateTime.ofInstant(date.toInstant(), ZoneOffset.UTC)

println ("사용자의 ISO-8601 Date 입력 결과는 ${localDate.year}년-${localDate.month}월-${localDate.dayOfMonth}일 입니다.")
```

lenient 라는 사전 hint 없이 바로 문제를 낼 경우 사람들이 제일 많이 선택한 결과는 **ParseException 이 발생한다** 였습니다. 하지만 `lenient` 한 특성으로 인해 실행 결과는 의외로 두번째, 즉 `2018년 2월 4일` 입니다. 막상 글로 풀어 쓰려니 별 것 아닌 내용처럼 보입니다만, 필자가 담당하는 서비스에서 이 특성을 제대로 파악하지 못해 특정 사용자의 생년월일을 제대로 인식하지 못한 문제가 있었습니다.

또한 우리가 흔히 아는 달력을 쓰지 않는 국가도 있다는 점 까지 고려한다면 날짜 변환이라는 것이 간단한 문제가 아니게 됩니다. 즉, 한국인의 관념 속의 '달력' 이란 **Gregorian calendar 를 기반으로 한 ISO-8601 달력** 입니다. 그런데 이 달력을 쓰지 않는 문화권도 있습니다(한국도 흔하진 않지만 '단기' 라는 별도의 달력을 쓰기도 합니다). 이런 문제 때문에, 글로벌 서비스를 준비하고 계신다면 날짜 변환 문제를 꼭 점검해 보셔야 합니다.

Android 에는 [이 문제를 해결해 주는 클래스](https://developer.android.com/reference/java/time/chrono/AbstractChronology.html)가 있습니다만 불행히도 API Level 이 26이나 되어 2018년 현재에는 제대로 쓰긴 어렵습니다. 다행히도 이 문제를 보완한 joda-time 라이브러리의 안드로이드 포팅 버전도 있으니 이 라이브러리의 도입을 검토해 보는 것도 좋은 문제 해결 방법이 될 것입니다.


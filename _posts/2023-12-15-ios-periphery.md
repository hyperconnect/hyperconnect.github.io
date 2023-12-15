---
layout: post
date: 2023-12-15
title: Azar iOS Team이 잊힌 코드를 추모 하는 법
author: hongsam
tags: iOS periphery
excerpt: Azar iOS Team에서 잊힌 코드를 추모하기 위해 Periphery라는 라이브러리를 도입하고, 어떻게 적용했는지에 대해 설명해 보고자 합니다.
last_modified_at: 2023-12-15
---

Azar에서는 매달, 매주, 매일 수많은 기능이 나타났다 사라집니다.
고민하고, 만들고, 테스트해 봅니다.

고민하고 만들고 테스트하고 지우고를 반복하다 보면 어느 순간 모두에게 잊힌 코드들이 생기기 마련입니다.

누가 만든 코드인지, 동작은 하는 코드인지, 존재해야 하는 코드인지, 지워도 되는 코드인지
누구도 알 수 없는 레거시라는 존재가 되어 버립니다.
레거시 코드는 유지 보수의 어려움, 성능의 문제를 일으키거나, 생산성 저하 등 여러 문제를 일으킵니다.

Azar iOS Team은 이러한 문제점을 극복하기위해
[Periphery](https://github.com/peripheryapp/periphery){:target="_blank"}라는 라이브러리를 도입하고
어떻게 적용했는지에 대해 설명해보고자 합니다.

## [Periphery](https://github.com/peripheryapp/periphery){:target="_blank"}
![4]({{ "/assets/2023-12-15-ios-periphery/1.png" | absolute_url }}){: width="20%"}

**A tool to identify unused code in Swift projects.**

periphery는 프로젝트에서 사용되지 않는 코드들을 검출해 내는 라이브러리입니다.
프로젝트 내에서 사용되지 않는 미사용 객체들을 탐지하고 제거할 수 있도록 개발자에게 알려줍니다.

### 설치
Periphery는 3가지 방식을 통해 [설치](https://github.com/peripheryapp/periphery#installation){:target="_blank"}가 가능합니다.

1. [Homebrew](https://brew.sh/){:target="_blank"}
2. [Mint](https://github.com/yonaskolb/Mint){:target="_blank"}
3. [CocoaPods](https://cocoapods.org/){:target="_blank"}

Azar iOS에서는 세 가지 설치 방법을 모두 사용하고 있지만 [Mint](https://github.com/yonaskolb/mint){:target="_blank"}를 통해 설치를 진행했습니다.


### 실행

`periphery scan --setup` 명령어를 통해 초기 설정을 잡아줍니다.
명령어를 실행하면 몇 가지 질문 창이 나타납니다.

1. 분석 대상 선택 (`targets`)
	- 어떤 프로젝트를 분석하여 결과를 볼 것인지
2. 빌드 시 필요한 scheme (`schemes`)
3. Objective-C 사용 여부 (`retain_objc_accessible`)
	- [공식문서](https://github.com/peripheryapp/periphery#objective-c)를 참고
	- y인 경우 미사용으로 판단하지 않습니다.
4. public 접근 제한자 사용 여부 (`retain_public`)
	- periphery가 public 접근 제한자를 가진 코드를 미사용으로 판단할지 결정합니다.
	- y인 경우 미사용으로 판단하지 않습니다.
5. 설정 저장 여부 (`.periphery.yml`)
	- 앞서 결정했던 내용을 `.periphery.yml`로 저장하여 사용할지 묻는 단계입니다.

설정을 완료하고 나면 첫 번째 분석이 실행되며
분석 결과는 console에 바로 출력됩니다.
setup 단계는 최초 1번만 실행하면 되며

5번 단계에서 설정을 저장하기로 결정했다면 `.periphery.yml` 파일이 생성되며
`periphery scan` 명령어를 실행할 때마다 yml파일에 적용되어 있는 설정을 자동으로 반영하게 됩니다.

**Azar에 설정된 `periphery.yml `**

![12]({{ "/assets/2023-12-15-ios-periphery/4.png" | absolute_url }})

### 설정

최초 설정을 이후 periphery 실행 시 사용할 옵션 두 가지를 추가했습니다.

첫 번째 옵션은 `--report-exclude` 옵션입니다.
특정 파일들을 결과에서 제외해 주는 옵션입니다.

**periphery는 컴파일 타임에 미사용 코드를 검출합니다. 컴파일 타임에는 사용하지 않는 코드로 판단했지만 실제론 사용하는 코드들이 존재합니다.**

이러한 코드들을 파일 단위로 결과에서 제거하기에 용이한 옵션입니다.
코드만 제외해야 하는 경우엔 [comment Commands](https://github.com/peripheryapp/periphery#comment-commands)를 사용해 코드 단위 무시도 가능합니다.

두 번째는 `--quiet` 옵션입니다.
이름만 봤을 땐 무슨 옵션인지 전혀 감이 잡히지 않았지만
console에 검출 결과만 출력해 주는 옵션입니다.

저는 결과 파일을 직접 다룰 생각이었는데 결과 이외의 텍스트가 적혀있다면 컨트롤하기가 어려워지니
결과만 출력해 주는 옵션을 사용하기로 했습니다.

더 많은 옵션은 `periphery scan --help`를 통해 확인이 가능합니다.

## 고민

periphery를 적용하기 전 나름의 규칙을 세웠습니다.

1. <a name="1">별도의 설치 과정을 거치지 않는다.</a>
2. <a name="2">develop branch 기준의 결과를 보여준다.</a>
	- (optional) 기준 브랜치를 정할 수 있게 한다.
3. <a name="3">주기적으로 실행해야 한다.</a>
4. <a name="4">모두가 공통된 실행 결과를 봐야 한다.</a>
5. <a name="5">실행 결과를 보기 위해 별도의 프로그램을 설치하지 않는다.</a>

위와 같은 규칙들을 정하고 적용하던 중 예상 밖의 문제가 나타나 고민에 빠지게 되었습니다.

## TroubleShooting

[1](#1), [2](#2), [3](#3)의 규칙은 비교적 처리하기 쉬웠습니다.
이미 Azar iOS에선 Mint를 사용하고 있고 팀원 모두가 Mint를 쓰고 있기 때문에 Mint 설정 파일에 periphery를 추가하고

[2](#2), [3](#3)은 githubActions를 통해 처리하기로 결정했습니다.

[4](#4), [5](#5) 번 규칙에서 예상 밖의 문제가 나타났는데
`검출 결과가 console에 나타난다.`는 점과
`출력 결과를 공유하고 싶은데 마땅한 format을 지원하지 않는다.`는 점이었습니다.

1. ### 검출 결과가 console에 나타난다.
	* 규모가 클수록 미사용 코드가 많이 검출될 것이고 console에 한 번에 출력하게 된다면 유실 가능성이 있다고 판단했습니다.
	* 하지만 아무리 찾아봐도 별도의 파일에 저장하는 옵션이 보이지 않았습니다.
	* [Xcode Integration](https://github.com/peripheryapp/periphery#xcode-integration){:target="_blank"}을 진행하여 Xcode에서 실행 결과를 볼 수 있지만 build phase script를 추가해야 한다는 점이 마음에 걸렸습니다.
		* 공통된 결과를 공유하기 위해 crontab, hook을 사용하여 주기적, 강제적 실행을 의도하고 있었고 현재 작업 상황, 위치한 브랜치에 따라 결과가 달라질 수 있다고 판단했습니다.
		* 또한 사용자가 원할 때만 실행하는 옵션은 제가 원하는 방식이 아니었습니다.
	* console 출력 결과를 직접 저장하기로 결정하고
	*  **검출 결과를 출력 리디렉션 연산자 (`>`)를 사용해 파일로 저장하기로 결정했습니다.**
	*  **`periphery scan > periphery_result.csv`**

2. ### 출력 결과를 공유하고 싶은데 마땅한 format을 지원하지 않는다.
	* ![5]({{ "/assets/2023-12-15-ios-periphery/2.png" | absolute_url }})
		* `periphery run scan --help`를 통해 살펴 본 지원하는 format 목록
	* 팀원 모두가 공통된 검출 결과를 볼 수 있게 하고 결과 파일을 보기 위해 [별도의 프로그램을 설치하게 하는 것을 피하고 싶었습니다.](#5)
	* 이 부분은 작업 당시 마음에 드는 방법이 생각나지 않아 일단 넘어가고 할 수 있는 것부터 하기로 했습니다.
	* **결론부터 말하자면 csv로 결과를 뽑고 html로 컨버팅 했습니다.**

## GithubActions

첫 번째 고민을 넘기고 나니 이후부턴 명확한 작업들만 남았습니다.

### 규칙 3. periphery를 주기적으로 실행 해야한다. [#](#3)

주기적으로 실행하는 방법은 간단했습니다.
Azar iOS Team은 `GithubActions`를 통해 CI/CD 작업을 진행하는데 이 부분을 응용한다면 쉽게 주기적인 실행을 할 수 있었습니다.

[GithubActions Workflow Schedule](https://docs.github.com/ko/actions/using-workflows/events-that-trigger-workflows){:target="_blank"}을 통해 crontab을 실행시킨다면 쉽게 적용할 수 있었습니다.

```yml
on:
  schedule:
    - cron: '0 0 * * 1'

jobs:
  run_periphery:
    steps:
      - name: Periphery
        run: mint run periphery scan > periphery_result.csv
```

매일 실행할 필요는 없으니 일주일에 한 번만 실행하기로 하고
매주 월요일 아침에 받아보면 좋겠다고 생각했습니다.

수동으로도 실행할 수 있다면 더 유연하게 대처할 수 있기 때문에 [workflow_dispatch](https://docs.github.com/ko/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch)를 추가하여 개발자가 직접 수동으로 workflow를 실행할 수 있게 추가를 해주었습니다.

물론 로컬에서 `periphery run scan`을 통해서도 실행할 수 있습니다.

```yml
on:
  schedule:
    - cron: '0 0 * * 1'
  workflow_dispatch:
~~ 생략 ~~
```


`workflow_dispatch` 옵션과 `GithubActions workflow`를 통해

[2. develop branch 기준의 결과를 보여준다, 기준 브랜치를 정할 수 있게 한다.
](#2) 조건도 자연스레 충족할 수 있었습니다.

### 규칙 5. 실행 결과를 보기 위해 별도의 프로그램을 설치하지 않는다. [#](#5)

이 부분은 periphery에서 제공하는 대부분의 포맷을 사용하면 별문제가 없는 부분입니다.
아래에서 설명할 [규칙 4.](#4)에서 많은 시간을 고민하다 보니 일단 html 형식이면 문제가 없을 거라 생각이 들었습니다.

다만 periphery가 html은 지원하지 않다 보니 csv format으로 출력하고 html로 컨버팅 하는 스크립트를 별도로 만들어야 했습니다.

javascript로 간단한 정렬 기능도 제공한다면 좋을 것 같다는 생각이 들어서 ordering까지 넣어보기로 했습니다.

이 부분은 python을 통해 간편하게 만들 수 있었습니다.

```python
def csv_to_html_table(file, remove_column_titles=None):
    if remove_column_titles is None:
        remove_column_titles = []

    reader = csv.reader(file)

    header_row = next(reader)
    remove_indices = [i for i, title in enumerate(header_row) if title in remove_column_titles]

    header = "<tr>"
    header += f'<th style="background-color: #f2f2f2; padding: 10px; text-align: left; border: 1px solid #ccc;">Index</th>'
    current_column_index = 0
    for idx, key in enumerate(header_row):
        if idx not in remove_indices:
            header += f'<th style="background-color: #f2f2f2; padding: 10px; text-align: left; border: 1px solid #ccc; cursor: pointer;" onclick="sortTable({current_column_index})">{key}</th>'
            current_column_index += 1
    header += "</tr>"

    body = ""
    row_count = 0
    for row in reader:
        body += "<tr>"
        body += f'<td style="vertical-align: top; padding: 10px; text-align: left; border: 1px solid #ccc;">{row_count}</td>'
        for idx, value in enumerate(row):
            if idx not in remove_indices:
                body += f'<td style="vertical-align: top; padding: 10px; text-align: left; border: 1px solid #ccc;">{value}</td>'
        body += "</tr>"
        row_count += 1

    title = f"""
    <h1> Periphery Result</h1>
    <h2> 검출 결과 총 {row_count}개</h2>
    """
    table = f'<div style="overflow-y: auto;"><table style="width: 100%; border-collapse: collapse;" border="1">{header}{body}</table></div>'
    return sort_js() + title + table
```

```yml
~~ 생략 ~~
- name: Convert Result
  run: python3 periphery_to_html.py
```
위에서 작성한 스크립트를 workflow에서 실행하도록 해서 컨버팅 결과를 출력할 수 있도록 했습니다.

### 규칙 4. 모두가 공통된 결과를 봐야 한다. [#](#4)

[artifact](https://docs.github.com/ko/actions/using-workflows/storing-workflow-data-as-artifacts){:target="_blank"}를 통해 결과 파일을 업로드하고 개발자가 다운받아 확인할 수 있도록 작업을 했습니다.
가장 많은 시간을 고민한 부분이었습니다.

원래 계획은 AWS S3와 같은 클라우드 스토리지를 통해 static website hosting을 한다면 간편하게 볼 수 있지 않을까라고 생각했고
html로 컨버팅 하는 스크립트까지 이미 작성한 상태였습니다.

결과적으로는 호스팅을 하지 않고 artifact를 통해 파일 공유를 하게 되었는데
결정한 이유는 다음과 같았습니다.

- 어쨌든 비용이 발생한다.
  - 호스팅을 해야 하다 보니 트래픽 비용이 발생할 것이고 업로드 또한 결코 공짜가 아니기 때문에 적게나마 비용이 발생할 것이라 생각했습니다.
  - 팀원들에게만 공유되면 되는 내용이기에 호스팅보단 내부에서 공유할 수 있는 방법을 찾아야 했습니다.
- periphery 결과가 유의미하게 줄어든다면 PR마다 실행시킬 것이다.
  - 검출 결과를 줄이고 나면 PR마다 실행시켜 관리할 생각이 있었습니다.
  - PR 단위 실행 결과가 업로드된다면 더 많은 파일을 관리해야 하니 비용, 관리 측면에서 어려움이 있을 거라 생각했습니다.
- 우리는 이미 githubActions을 잘 활용하고 있으니 지원하는 기능을 찾아보자.
- ~~그냥 artifact 한번 써보고 싶었다.~~

```yml
~~ 생략 ~~
steps:
  - name: Upload
    uses: actions/upload-artifact@v3
    with:
      name: periphery_Result
      path: periphery_result.html
      retention-days: 7
```

## 실행

**완성된 work flow**
```yml
on:
  schedule:
    - cron: '0 0 * * 1'
  workflow_dispatch:

jobs:
  run_periphery:
    steps:
      - name: Periphery
        run: mint run periphery scan > periphery_result.csv
      - name: Convert Result
        run: python3 periphery_to_html.py
      - name: Upload
        uses: actions/upload-artifact@v3
        with:
          name: periphery_Result
          path: periphery_result.html
          retention-days: 7
```

**html로 확인할 수 있는 미사용 코드**

![6]({{ "/assets/2023-12-15-ios-periphery/3.png" | absolute_url }})


길었던 작업의 결과물을 보니 참으로 뿌듯했습니다.

이제 잊힌 코드들을 한눈에 살펴볼 수 있게 되었습니다.

workflow도 만들었고 스크립트도 만들었고 규칙도 다 지켰으니 이제 정말 마무리가 된것 같습니다.

## Done?

### **미사용 코드를 찾아줄 뿐, 제거해주는 마법같은 일은 일어나지 않습니다.**

이제 출발점에 섰을 뿐입니다.

앞으로 수많은 코드를 검토하고 제거하는 반복적인 작업이 남아 있습니다.

그리고 더 이상 미사용 코드가 생기지 않도록 계속해서 관리해 나가야 할 겁니다.

코드를 제거하기 위해선 개발자가 직접 검토하고 제거해도 되는 것인지 확인 후 제거하고 빌드를 돌려보고
이상이 없다는 것을 확인한 후에야 비로소 한 줄의 코드가 사라지게 됩니다.

[Periphery](https://github.com/peripheryapp/periphery){:target="_blank"}는 모두에게 잊혔던 코드들을 찾아주어
개발자가 직접 검토, 탐색하는 시간을 절약할 수 있습니다.

잊힌 코드로 인해 고통받는 개발자들에게 작은 도움이 되었으면 좋겠습니다.

읽어주셔서 감사합니다.
---
layout: post
date: 2018-08-28
title: "2018 PYCON KR 젬 줍기 배틀 후기"
author: steve
published: true
lang: ko
excerpt: 2018 PYCON KR 에서 진행된 젬 줍기 배틀의 후기입니다.
tags: pycon.kr python coding-battle
---

파이콘 한국 2018 X 하이퍼커넥트: 젬 줍기 배틀을 마무리하며
===========================================================

※ 글을 작성하기에 앞서 도와주신 모든 분들과 제출해주신 모든 참가자분들 그리고 관심을 가져주신 모든 분들에게 진심으로 감사 말씀 전합니다.

## 안녕 파이콘!
지난 8월 18, 19일 코엑스에서 열린 2018 파이콘 하이퍼커넥트 부스에서 코딩배틀을 진행 했던 steve입니다.
제 인생 첫 파이콘에서 이런 뜻깊은 행사를 진행 할 수 있어서 정말 영광이었습니다.  
![하이퍼커넥트 부스]({{ "/assets/2018-08-25-pycon-wrap-up/booth.JPG" | absolute_url }}){: width="50%" } <br/> 
이 멋진 현장에서 벌어졌던 저의 좌충우돌기를 들려드리고자 합니다.

## 들어가며
처음 게임 테마를 정한 뒤 저의 생각은 '개발자스럽게(?) 터미널에서 보여주자'였습니다.
하지만 그러면서도 보기 싫지 않도록 예쁘게. (=현대적인 복고풍의 옷을 주세요.)  
그래서 무색무취의 깔끔한 삶을 추구하는 저는 0과 1로만 이루어진 판을 만들었죠. ~~예쁘게라면서요~~
그러던 와중 파이콘 하루 전날 젬을 유니코드 이모지중 다이아몬드로 아예 하면 안되나요? 그게 더 재밌어 보일 것 같아요!
라는 말에 저는 "유니코드 이모지를 코드에 써본적이 없어서 힘들 것 같습니다."라고 당차게 말을하려 했지만 입에서 나오고 있는 말은 "네 알겠습니다!" 였었습니다. 패기로만 살아온 저에게는 당연한 일이였죠.

역시나 JSON 디코딩 문제에 부딪혔지만 이미 구현 난이도가 높은데 코드 속에서 이모지를 쓰면 참가자들이 더 헷갈릴 것 같다고 판단되어
(절대 시간이 부족하지 않았습니다. 아무튼 아님.) 구조를 그대로 유지하고 출력만 이모지로 하는 형식으로 바꾸게 됩니다.    
결국 파이콘이 다 끝나고 나서야 해결방법을 깨닫게 되었다는...  
그렇게 해서 만들어진 판이  
![젬줍판]({{ "/assets/2018-08-25-pycon-wrap-up/board.png" | absolute_url }}){: width="50%" } <br/>
입니다. __우리 이모지 예쁘죠?__  
원래 계획은 부스에 찾아오시면 테스트코드와도 돌려봐드리고 이런저런 전략 얘기도 하고 싶었는데 역시 인생은
원하는 대로만 되는 것이 아니었죠.

자 이제 모두들 궁금해 하셨을 1, 2, 3등의 코드 전략, 그 외 배틀 관련 간략한 이야기를 하겠습니다.

## 코딩배틀
#### 수상자들 
중간집계가 나온 후 1등의 결과에 술렁였었죠. 저희 진행측도 그 결과를 보고 혹시나 해서 바로 코드를 확인헀습니다.
정말 놀랍게도 아무런 트릭이 없었습니다! (많은 분들도 같은 생각이었을거라 예상됩니다.) 이 코드는 가장 마지막에 보기로
하고 아래에 1등 2등 3등의 대결을 동영상으로 확인하세요! 우선 3등을 하신 닉네임 jordan님의 코드를 보겠습니다.
* jordan  
jordan님께 간략한 전략을 들을 수 있었습니다. 
 
'저 같은 경우는 평소에도 효율을 중요시하는 편이라서, 각각의 경우를 다 계산하는 것 보다 동적으로 프로그래밍하는게 좋다고 생
각이 되어서 현재 position에 갈 수 있는 위치에 대한 점수를 계산해서 가장 점수가 높게 나오는 위치로 이동하게 로직을 작성했습니다.
'  

그리고 메일에는 반영이 안되었을 거라 하셨는데 수정본 메일을 보내주신 후로는 수정된 코드로 진행이 되었습니다. :)  
코드를 간략히 보면 (일부분 입니다 코드가 연속적이지 않을 수 있습니다.)
```
def check_position_score(x, y, depth=1):
    score = 0
    if depth >= 0:
        if x < max_length and map[x+1][y] == "*":
            score += 1
            score += check_position_score(x+1, y, depth-1)/2

        if x > min_length and map[x-1][y] == "*":
            score += 1
            score += check_position_score(x-1, y, depth-1)/2

        if y < max_length and map[x][y+1] == "*":
            score += 1
            score += check_position_score(x, y+1, depth-1)/2

        if y > min_length and map[x][y-1] == "*":
            score += 1
            score += check_position_score(x, y-1, depth-1)/2

    return score
    
    //

    if row > min_length and map[row-1][column] == "*":
        highest = check_position_score(row-1, column)

    if row < max_length and map[row+1][column] == "*":
        if highest < check_position_score(row+1, column):
            highest, result = check_position_score(row+1, column), 'D'

    if column < max_length and map[row][column+1] == "*":
        if highest < check_position_score(row, column+1):
            highest, result = check_position_score(row, column+1), 'R'

    if column > min_length and map[row][column-1] == "*":
        if highest < check_position_score(row, column-1):
            highest, result = check_position_score(row, column-1), 'L'
```
코드는 설명을 첨부해주신 첫번째 버젼으로 보여드렸습니다. 정말 복잡하지 않으면서 좋은 효율을 냈던 코드인 것
같습니다!

그리고 2등을 하신 lsw님의 코드를 보겠습니다.
* lsw  
lsw님께도 간단한 전략 설명을 들을 수 있었습니다.

'제가 구현한 전략은 다음과 같습니다.

기존 움직임과 미래의 움직임은 생각하지 않고 현재의 지도만 보고 젬을 가장 오래 먹을 수 있을 것으로 예측되는 방향으로 이동한다.

여기서 방향을 판단하는 로직은
각 방향에 대해 DFS 를 이용한 완전탐색으로 1개의 젬을 먹는 경우의 수, 2개의 젬을 먹는 경우의 수, .... 14개의 젬을 먹는 경우의 수를 구합니다. 

최대 14개로 정한 것은 15 이상부터 경우의 수를 계산하는데 시간이 2초이상 소요되는 것으로 확인 되어 14개로 설정 하였습니다. (코드 상 MAX_DEPTH)

보석 갯수와 경우의 수를 가지고 수식을 이용해 최종 기댓값을 계산합니다.

제가 사용한 기댓값을 구하는 공식은 다음과 같습니다.
오른쪽으로 가는것에 대해 각 젬 갯수 별로 경우의 수가 아래와 같이 나왔다면

1개 : 1  
2개 : 3  
3개 : 15  
.
.
.  
14개: 1000
 = (1 X 1) + (2 X 3) + (3 X 15) + ... + (14 X 1000) 이 기댓값이 됩니다.

최종적으로 4방향에 대해 각각 기댓값을 구한 뒤 기댓값이 제일 높은곳으로 이동합니다.'  
코드를 간략히 보면 (일부분 입니다 코드가 연속적이지 않을 수 있습니다.)
```
MAX_DEPTH = 14


def get_player_location(map_yx, player):
    for y in range(0, 8):
        for x in range(0, 8):
            if map_yx[y][x] == player:
                return (y, x)
    return (-1, -1)


cnt = dict()


def is_enable(y, x):
    if y < 0 or x < 0 or y > 7 or x > 7:
        return False
    return True


def dfs(current_map, cur_y, cur_x, depth):
    if depth >= MAX_DEPTH:
        return
    global cnt
    cnt[str(depth)] = cnt[str(depth)] + 1
    dy = [-1, 0, 1, 0, ]
    dx = [0, 1, 0, -1, ]

    for i in range(0, 4):
        if is_enable(cur_y + dy[i], cur_x + dx[i]) and current_map[cur_y + dy[i]][cur_x + dx[i]] == '*':
            current_map[cur_y + dy[i]][cur_x + dx[i]] = '.'
            dfs(current_map, cur_y + dy[i], cur_x + dx[i], depth + 1)
            current_map[cur_y + dy[i]][cur_x + dx[i]] = '*'
```
글로 보면 어려워 보일 수도 있는데 막상 사용된 함수는 이 셋이 전부였습니다.
실제로 지금 보여드린 세 분의 코드 중 가장 짧은 줄 수를 보여주었습니다. (jordan님은 첫번째 버젼 기준)
승무패 수를 보았을 때 1등을 하신 mike님과도 큰 차이가 없었는데요, 정말 간단한 함수들로 매우 좋은 performance를 보여주었다는 점이 놀라웠습니다.

마지막으로 1등을 하신 mike님의 코드입니다.
* mike  

※ 설명을 직접 듣지는 못하여 확실하지 않을 수 있습니다.  
우선 mike님은 특정 case들에 대해서는 가중치를 따로 부여하고 (너무 여러 case라 case들의 기준은 찾지 못했습니다.)  
가장 많이 젬을 먹을 수 있는 길로 선택을 하도록 구현되어있었습니다.

코드를 간략히 보면 (일부분 입니다 코드가 연속적이지 않을 수 있습니다.)
```
def mc(m, depth=MC_DEPTH):
    if depth <= 0:
        return 'U', 0
    if m in MC_MAP:
        return MC_MAP[m]
    maxx_d = 'U'
    maxx = -1
    if distance(m):
        for p_d, p_action in action_choice(m, m.find('P')).items():
            mm = player_move(m, p_action)
            ret = 0
            for o_action in action_choice(m, m.find('O')).values():
                if p_action(m.find('P')) == o_action(m.find('O')):
                    pass
                else:
                    ret += 0.8 * mc(opposite_move(mm, o_action), depth - 2)[1]
            if ret > maxx:
                maxx = ret
                maxx_d = p_d
    else:
        p_d, p_l = find_logest_path(m, 'P', 20)
        o_d, o_l = find_logest_path(m, 'O', 20)
        maxx_d = p_d
        if p_l > o_l:
            maxx = 100
        elif p_l == o_l:
            maxx = 0
        else:
            maxx = -1000

    if depth == MC_DEPTH:
        MC_MAP[m] = (maxx_d, maxx)
    return maxx_d, maxx
```
아이디어 자체는 크게 달라 보이지 않았으나 코드 전체로 보면 소수점도 적용되어 좀 더 계산이 복잡한 느낌이네요! 세밀한 가중치부여를 통해 최고의 결과를 얻을 수 있었던 것 같았습니다. :)  

mike님의 설명이 추가되었습니다.  
------------------설명 -----------------------  
게임의 승패를 알 수 있는 지점  
게임을 끝까지 진행하지 않아도 어떤 플레이어가 확정적으로 이길 수 있는 지를 판단할 수 있습니다. (`distance` 함수)
두 플레이어가 다시 만날 수 없게 되면 해당 위치에서 임의의 점으로 가장 먼 경로의 길이를 구합니다.
이 경로만큼 플레이어는 젬을 더 먹을 수 있으니 이 상태에서 플레이어가 할 수 있는 모든 수를 보지 않아도 특정 보드 상태의 승패를 알 수 있습니다.

몬테 카를로 서치 (Minimax)  
임의의 상태에서 내가 할 수 있는 모든 수와 상대가 할 수 있는 모든 수를 보고 특정 depth까지 서치하여 각 상태의 점수를 구합니다. (`mc` 함수) (https://www.neverstopbuilding.com/blog/minimax)
이 때, 게임 게임의 승패를 알 수 있는 지점이 되면 승, 무, 패에 따라 다른 점수를 반환합니다. (대회에 제출한 버전에서는 승 100, 무 0, 패 -1000 점을 줬습니다.)
그리고 각 depth 마다 일정 배율을 곱하여 상태의 점수를 합산합니다. (대회 버전에서는 0.8)

각 상태별 점수 미리 계산  
위의 방법으로는 특정  상태에 대한 점수를 결정론적으로 알 수 있으니, 적당한 depth 까지는 미리 계산을 하여 코드에 `MC_MAP` 이라는 dictionary로 미리 넣어놨습니다.
미리 계산을 할 때는 서치의 depth를 14까지 보고 계산을 했습니다. 또, 이런 서치를 전체에서 12 depth까지 미리 계산하도록 했습니다.
`MC_MAP`에 해당하는 상태가 없을 경우 대회 환경에서 depth 8로 검색을 하도록 했습니다.

2초 제한  
depth 8로 검색을 하다가 1초가 지날 경우 depth 6으로 검색을 하도록 하는 `timeout`이라는 함수를 정의했습니다.



아래 영상들은 각각 1등 vs 2등, 2등 vs 3등, 3등 vs 1등 입니다. vs앞의 플레이어가 왼쪽 위, vs뒤의 플레이어가 오른쪽 아래입니다.(한 번의 예시이므로 결과는 항상 달라질 수 있습니다.)  
영상을 찍고 확인했는데 이름을 출력안하고 A, B로만 나오게 해놨네요 왼쪽 시작이 A, 오른쪽 시작이 B 입니다. 

*   1등 vs 2등  
<iframe width="560" height="315" src="https://www.youtube.com/embed/kqCpUguDmHw" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

*   2등 vs 3등  
<iframe width="560" height="315" src="https://www.youtube.com/embed/gz_QiulQUoQ" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

*   3등 vs 1등  
<iframe width="560" height="315" src="https://www.youtube.com/embed/6cvOIdAsOoQ" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

  
#### 비하인드
- 생각보다 난이도가 있어서인지 매우 특이한 방법으로 접근했다고 느껴지는 전략은 많이 없었습니다. 그 중에서 가장 인상깊었던 것을 꼽자면
"절반만 넘게 먹으면 무조건 이기니까 아예 처음부터 길을 정해두었다." 라고 하신 분이 계셨는데 실제로 테스트코드와 붙어서 꽤 여러번 이기는 모습을
볼 수 있었습니다. 기록에서도 보면 순위가 중간층 정도에 위치해있었습니다. 놀라운 결과였죠 ㅎㅎ

- 그리고 실제 행사 진행 중, 후로 전달받고 직접 들은 얘기들 중 직접 테스트 에이전트와 붙여보도록 코드를 제공해줄 수는 없냐 라는 말이 정말
많았습니다. 실제로 이부분은 제가 앞서도 말했듯이 부스에서 도와드리면서 구현에 대한 얘기도 나누며 소통하고 싶어서
이런 방식으로 진행을 하게 되었습니다. 이 테스트 환경이 없어서 그런지 상대의 움직임을 제대로 고려 못하고 에러를 
뱉는 코드들도 많았었죠. 따로 그래도 이러한 오류는 내뱉지 않도록 이 부분도 테스트를 할 수 있개 만들어 놓을걸이라는 아쉬움도 있었습니다.

- 추가로 결과 확인 페이지에는 그때 그때 메일을 받으면 우선 닉네임을 올려둔 채 보류해두고 검사 시 오류가 나면 미제출로 처리되어 순위에서 빠지게 하였었습니다. 
결국 중간 집계 결과중 제출 순위는 확정이 아니었는데 이 부분은 미리 공지가 안되어 오해가 발생했던 것 같습니다.  

- mike님에게 1패를 안긴 분은 누굴까? 많은 분들 (저희를 포함한)이 궁금해 하셨을 것 같습니다. 로그를 확인하여 그 분과
다시 따로 매치를 시켜보았습니다. 그런데 놀랍게도 똑같은 경로로 계속 무승부만 나와서 자세히 보니 타임아웃 문제였습니다.
mike님과 저희측에 각각 타임아웃을 처리하는 부분이 있었는데 단순히 서버의 속도문제로 인해 타임아웃이 된 것으로 보였습니다.
저희가 좋은 환경에서 진행하였다면 무패를 달성할 수 있었을 텐데 정말 아쉽게 됐네요 ㅜㅠ  

## 돌아보며
첫 날은 문의가 거의 없어서 미처 못해놨던 경기와 기록의 자동화를 설렁설렁(문제의 시작) 하고 있었습니다.
사실 이렇게까지 많은 관심을 가져주실 줄 미처 예상을 못했었고 그래서 이 정도는 직접 해도 되지 않을까
 라고 생각한 저의 잘못이었습니다... 그리고 이제 둘째날이 되고 많은 분들이 몰려서
참여해주셔서 원래 규칙을 따라 코드 확인의 과정은 꼭 필요하다고 느껴 결과발표를 미루게 되었죠. 아직까지도 개인적으로
아쉬움이 많이 남는 부분입니다. 좀 더 시간을 투자했다면 훨씬 완성도 있는 행사가 되었을텐데 말이죠.  
그래도 끝난 뒤에도 재밌었다고 말씀 해주셨던 분들 덕에 정말 힘이 나고 감사했습니다. 🙏🙏

덕분에 좋은 경험 만들 수 있어서 기뻤습니다! 그럼 PYCON KR 2019때 봐요!👋

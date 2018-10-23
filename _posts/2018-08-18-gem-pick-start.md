---
layout: post
date: 2018-08-18
title: "[최종 결과 업데이트] 젬 줍기 배틀"
author: steve
published: true
lang: ko
excerpt: 젬 줍기 배틀의 상세 설명입니다. 최종 결과는 1위 mike, 2위 lsw, 3위 jordan, 행운상 gjchoi입니다.
tags: pycon.kr python coding-battle
---

파이콘 한국 2018 X 하이퍼커넥트: 젬 줍기 배틀을 시작합니다.
===========================================================

## 결과 발표
드디어 2018 파이콘 코딩배틀의 결과가 나왔습니다! 오래 기다려 주셔서 감사합니다.
우선 결과부터 말씀드리면
* 1등 : mike
* 2등 : lsw
* 3등 : jordan
* 행운상 : gjchoi

입니다! 축하드립니다!!
당첨자 분들께는 추후에 메일로 개별적으로 안내가 나갈 예정입니다. 꼭 메일을 확인해 주세요!

[결과 확인 페이지](https://docs.google.com/spreadsheets/d/1PTOdxgfUtlEpznHsI6fnEcGtVpDpmOLySedR3hZQBlc/edit?usp=sharing)도 업데이트가 되어있으니 자신의 승, 무, 패 횟수와 등수를 확인해보세요 :)

1,2,3등의 코드에 대한 짧은 분석과 제출해주신 흥미로웠던 코드에 대한 리뷰와 후기 등은 조만간 후기 포스팅으로 찾아올 예정입니다. 관심을 가지고 하이퍼커넥트 기술블로그를 찾아주세요.
감사합니다.

----------------------------
* !중요3! : **마지막에 제출해주신 분들이 많아서 예상보다 풀 리그 돌리는데 시간이 오래 걸리고 있습니다. 최종 결과는 추후 기술블로그와 [결과 확인 페이지](https://docs.google.com/spreadsheets/d/1PTOdxgfUtlEpznHsI6fnEcGtVpDpmOLySedR3hZQBlc/edit?usp=sharing)를 통해 공지하고, 상품은 개별적으로 연락해서 배송해 드리겠습니다. 미숙한 운영으로 불편 드리게 되어 정말 죄송합니다.** 🙇

* !중요2! : 제출 시간이 3시 45분으로 늘어났습니다. 아래의 예제코드를 보시면 코드작성을 쉽게 하는데 도움이 될 것입니다!!


* !중요! : 구현이 감이 안온다 하시는 분들을 위해 예제코드 두 개를 준비했습니다! 보고 참고해주세요 :)
* [ex1-gets-gem.py](https://gist.github.com/steve806/dbb104ba3070cc23972ecca28745074b)
* [ex2-gets-gem.py](https://gist.github.com/steve806/e4986048ca0ea6d8fd2d58c8f3127444)


안녕하세요, 하이퍼커넥트 Steve 입니다.

저희 기술블로그를 통해 예고했던 젬 줍기 배틀을 시작합니다! 젬은 아자르에서 프리미엄 매치를 하는데 필요한 가상의 보석인데요, 이번 배틀에서는 두 코드가 더 많은 젬을 줍기 위해 경쟁하게 됩니다.

이번 배틀을 통해 모두가 파이콘 한국 2018을 더 신나게 즐기게 되길 바랍니다. 멋진 코드를 만들고, 하이퍼커넥트가 준비한 상품의 주인공이 되어 보세요!

## 게임 목표
* 바닥의 젬을 주워가며 상대보다 판 위에서 오래 살아남거나 상대를 꼼짝 못하도록 만들어서 승리를 쟁취한다!
* 코드 작성 실력뿐 아니라 운도 성패를 가르는 중요한 요소가 됩니다. 누구에게나 열려있으니 많은 참여 부탁드립니다!

## 게임 규칙
* 아래의 뼈대코드와 같이 완전 random인 코드는 원활한 진행을 위해 받지 않겠습니다.
* 참가자들이 제출한 두 코드가 대결을 하게 됩니다.
* 밟을 수 있는 땅은 젬이 있는 땅 뿐입니다.
* 한 턴에 동시에 둘이 움직일 방향을 각각 정하게 됩니다.
* 갈 수 없는 곳으로 갈 경우 실격처리되어 패배합니다.
  * ex) 상대가 이미 밟고 지나간 젬이 사라진 땅, 경기장 밖 등
* 둘이 동시에 같은 곳으로 간다면 무승부 처리가 됩니다.
* 갈 수 있는 곳이 없을 경우 패배하게 됩니다. 물론 둘이 동시에 갈 수 있는 곳이 없다면 무승부 처리가 됩니다.
* 프로그램이 돌아가는 시간은 한 턴에 2초로 제한하겠습니다. 너무 오래걸릴 수도 있기에 ㅜㅠ
* 인풋은 json의 형태로 주어지게 됩니다. 아래 뼈대코드를 확인하시면 더 잘 아실 수 있을 겁니다!
* U, D, R, L 중 하나만 print가 되도록 만들어주세요! 다른 문자열 등이 출력되면 곧바로 패배하게 됩니다. 이는 아래 주어질 매우 간단한 테스트코드를 통해 확인 가능합니다.
  * print('U') 
* 게임의 공정함을 위해 cheating 으로 간주되면 실격처리를 하겠습니다. 코드를 확인해 볼 예정이니 주의해주세요!

## 참가 방법
* 주어진 input과 output의 형식에 맞춰 이동을 하게 하는 python3 코드를 만든다.
* 파일명을 {쓰고싶은 닉네임}-gets-gem.py으로 변경한다. (중복이 있을 경우 뒤에 번호가 붙게 됩니다. 결과 확인 페이지에 닉네임과 메일주소를 써 둘 예정이니 본인이 어떤 닉네임인지 확인하시면 됩니다.)
  * ex) steve-gets-gem.py
* 완성된 파일을 pycon2018@hpcnt.com으로 보낸다.
* [결과 확인 페이지](https://docs.google.com/spreadsheets/d/1PTOdxgfUtlEpznHsI6fnEcGtVpDpmOLySedR3hZQBlc/edit?usp=sharing) 에서 1시간마다 업데이트 될 결과를 확인한다. 오프라인에서 행사가 진행되는 시간에만 업데이트가 이루어질 예정입니다. (주의 : 업데이트 시간 딜레이가 있을 수 있습니다. 2시 50분에 제출하신 코드가 3시 업데이트에는 반영이 되지 않아 있을 수 있습니다.)

## 수상자 선정
* 코드 접수 마감: 8월 19일 일요일 오후 3시 45분
* 수상자 발표: 8월 19일 일요일 오후 4시
* 순위선정 기준 : 승점 (각 배틀 당 승 3점, 무승부 1점, 패 0점 부여)
* 상품
  * 1등: 플레이스테이션4 프로 + 2인용 조이패드
  * 2등: 리얼포스87 블랙 키보드
  * 3등: 애플 에어팟 이어폰
  * 행운의 10번째 참가자: 로지텍 MX Master 2세대 무선 마우스 (코드 제출 순서 기준)
* 유의사항
  * 상품은 수상자 발표 후 파이콘 한국 2018 행사장 내 하이퍼커넥트 부스에서 지급 예정입니다.
  * 수상자분께는 코드를 제출해주신 이메일로 연락을 드릴 예정입니다.
  * 하이퍼커넥트 동료 여러분도 참여하실 수 있으나, 상품은 받으실 수 없습니다.

## 문의 사항
* 더 많은 정보가 필요하시다면 파이콘 행사장의 Hyperconnect 부스를 찾아주세요!
* 혹시 테스트 에이전트와의 대결을 해보고 싶으시면 역시 파이콘 행사장의 Hyperconnect 부스를 찾아주세요

## 뼈대 코드
* 아래 파일명들은 임의의 파일명입니다. 아래 코드를 복사해서 이를 바탕으로 사용하시면 됩니다.
* 실행방법 : bone-code.py를 변경하여 자신만의 코드를 만든 뒤 python output-test-code.py bone-code.py를 실행하세요!
* 결과가 You choose ~ 라 나오면 성공!
* [bone_code.py](https://gist.github.com/steve806/9e616f90ad4b2ab64d25e65e65559814) 
* [test_code.py](https://gist.github.com/steve806/d368d7007523bd576f38e84f644ac7a1)에서도 확인할 수 있습니다.

bone-code.py
```
# -'- coding: utf-8 -*-
import sys
import json
from random import choice

def main():
    '''
        인풋은 json형식으로 들어오며
        'map' : 8 * 8 크기의 판의 상태를 한 칸당 한 글자로 공백없이 string의 형태로 준다.
        'opponent_history' : 지금까지 상대가 움직인 방향들을 string의 형태로 공백없이 준다. ex) 'UDDLLUR'
        'my_history' : 지금까지 내가 움직인 방향들을 string의 형태로 공백없이 준다.        ex) 위와 동일
        'me' : 내가 누군지 알려줌.          ex) 'A' or 'B'
        'opponent' : 상대가 누군지 알려줌.  ex) 위와 동일
	
	map에 대한 상세한 설명
	💎 : 갈 수 있는 곳입니다. 젬이라고 불리죠
	A, B : 위에서 설명했듯 인풋중 me로 들어온 알파벳이 본인이 움직일 말이 됩니다.
	a, b : A, B가 이미 지나간 길, 다시 말해 다시는 갈 수 없는 길입니다.
    '''

    data = json.loads(sys.argv[1])

    map_string = data['map']
    opponent_history = data['opponent_history']
    my_history = data['my_history']
    player = data['me']
    opponent = data['opponent']

    # 재미를 위해 젬을 직접 이용해서 코드를 짜보세요!
    new_input_str = map_string.replace("*", "💎")

    map = []

    for i in range(8):
        map.append(list(map_string[8*i:8*i+8]))

    # TODO: 아래쪽을 변경하여 멋진 코드를 만들어 주세요!

    available = ['U', 'D', 'R', 'L']
    print(choice(available))

main()
```

output-test-code.py
```
# -'- coding: utf-8 -*-
import sys
import subprocess
import json
from random import choice


def main():
    file_name = sys.argv[1]

    # 예시 인풋 두개
    data_list = [{'map': 'A**************************************************************B',
                  'opponent_history': '', 'my_history': '', 'me': 'A', 'opponent': 'B'},
                 {'map': 'aA************************************************************Bb',
                  'opponent_history': 'R', 'my_history': 'L', 'me': 'B', 'opponent': 'A'}]

    data_str = json.dumps(choice(data_list))

    out = subprocess.check_output([sys.executable, file_name, data_str]).decode().strip()
    direction = str(out)

    right = ['U', 'D', 'R', 'L']

    if direction in right:
        print("You choose {}".format(direction))
    else:
        print("Wrong form")

main()
```

* [test-move-code.py](https://gist.github.com/steve806/5349ffa1235e981830ed6397c807e50c)에서도 확인 가능합니다!
자신의 움직임을 보고싶다는 의견이 있어서 추가된 코드입니다! 
python3 test-move-code.py {Nickname}-gets-gem.py로 실행하시면 됩니다.
테스트 코드의 이상을 발견하여 수정하였습니다.

test-move-code.py
```
# -*- coding: utf-8 -*-
from time import sleep
import sys
import subprocess
import json


def move(player, direction, map):

    for i in range(10):
        for j in range(10):
            if map[i][j] == player:
                prev_x = j
                prev_y = i

    post_x, post_y = prev_x, prev_y
    if direction == 'U':
        post_y = prev_y - 1
    elif direction == 'D':
        post_y = prev_y + 1
    elif direction == 'R':
        post_x = prev_x + 1
    elif direction == 'L':
        post_x = prev_x - 1

    if post_x < 1 or post_x > 8 or post_y < 1 or post_y > 8:
        return False

    if map[post_y][post_x] == '*':
        map[prev_y][prev_x] = player.lower()
        map[post_y][post_x] = player
        return True
    else:
        return False


def check_no_way_to_go(map, player):
    default = False
    post_x = 0
    post_y = 0
    for i in range(10):
        for j in range(10):
            if map[i][j] == player:
                post_x = j
                post_y = i
    if map[post_y][post_x + 1] != '*' and map[post_y][post_x - 1] != '*' and \
       map[post_y + 1][post_x] != '*' and map[post_y - 1][post_x] != '*':
        default = True

    return default


def print_map(map):
    for i in range(8):
        temp_str = ''
        for j in range(8):
            if map[i+1][j+1] == '*':
                temp_str = temp_str + '💎'
            elif map[i+1][j+1] == 'A':
                temp_str = temp_str + '😀'
            elif map[i+1][j+1] == 'a':
                temp_str = temp_str + '👟'
        print(temp_str)


def main():
    f = open("result.txt", 'a')

    file_name_1 = sys.argv[1]

    snake_map = [['0' for x in range(10)] for y in range(10)]
    for i in range(8):
        for j in range(8):
            snake_map[i+1][j+1] = '*'

    direction = ['U', 'D', 'L', 'R']

    A_start_x = 1
    A_start_y = 1

    snake_map[A_start_y][A_start_x] = 'A'

    data1 = {'opponent_history': '', 'my_history': ''}

    A_history = ''
    B_history = ''

    print("===================")
    print_map(snake_map)
    print("===================")
    print("\n")

    while(True):
        input_str = ''
        for i in range(8):
            input_str = input_str + ''.join(snake_map[i+1][1:9])

        data1.update({'map': input_str,
                      'opponent_history': B_history, 'my_history': A_history,
                      'me': 'A', 'opponent': 'B'})

        data_str1 = json.dumps(data1)

        out1 = subprocess.check_output([sys.executable, file_name_1, data_str1]).decode().strip()
        direction1 = str(out1)

        trick = 0
        if direction1 not in direction:
            print("Do not use Trick")
            return

        valid = move('A', direction1, snake_map)
        if not valid:
            print("Wrong way")
            return

        print("===================")
        print_map(snake_map)
        print("===================")
        print("\n")

        a_no_way = check_no_way_to_go(snake_map, 'A')
        if a_no_way:
            print("No way to go")
            return

        A_history = A_history + direction1

        sleep(0.5)
main()
```

* 혹시 윈도우의 cmd를 쓰신다면 이모지의 출력이 불가하므로 print_map함수를 아래와 같이 바꿔주세요!
P는 젬 즉 point를 의미하고, O는 현재 자신의 위치, X는 이미 지나온 길을 의미합니다 
```
def print_map(map):
    for i in range(8):
        temp_str = ''
        for j in range(8):
            if map[i+1][j+1] == '*':
                temp_str = temp_str + ' P'
            elif map[i+1][j+1] == 'A':
                temp_str = temp_str + ' O'
            elif map[i+1][j+1] == 'a':
                temp_str = temp_str + ' X'
        print(temp_str)
```



import re
from typing import Optional

re_undefined = re.compile(r"^ In the context of Grid World, I don't have any information.*$")
re_yes = re.compile(r"^ Yes\b")
re_no = re.compile(r"^ No\b")
re_int = re.compile(r"^ ([0-9]+)$")
re_wall = re.compile(r"\b[Ww]all\b")
re_floor = re.compile(r"\b[Ff]loor\b")
re_agent = re.compile(r"\b[Aa]gent\b")
re_goal = re.compile(r"\b[Gg]oal\b")

re_q_tile = re.compile(r"What is located at tile \(([0-9]+),([0-9]+)\)\?")

class Map:
    def __init__(self, w, h):
        self.cells = [[None] * w for _ in range(h)]
        self.w = w
        self.h = h

    def set(self, question, answer):
        m = re_q_tile.match(question)
        if m:
            x = int(m.group(1))
            y = int(m.group(2))
            if x >= 0 and x < self.w and y >= 0 and y < self.h:
                if answer == None:
                    self.cells[y][x] = '?'
                else:
                    self.cells[y][x] = answer[0]

    def __str__(self):
        return ''.join(''.join(answers) +'\n' for answers in self.cells)

def grade(data, verbosity:int):
    correct = []
    incorrect = []
    unparsed = []
    unanswered = []

    map0 = Map(9,6)

    for q in data['questions']:
        question = q['question']
        response = q.get('response', None)
        typ = q['annotations']['answer_type']
        if response == None:
            unanswered.append(question)
        else:
            if typ == 'bool':
                answer = convert_bool(response)
            elif typ == 'int':
                answer = convert_int(response)
            elif typ == 'tile':
                answer = convert_tile(response)
            else:
                answer = None

            if answer == None:
                unparsed.append((question, response))
            elif answer == q['annotations']['expected_answer']:
                correct.append((question, response))
            else:
                incorrect.append((question, response))

            if q['map'] == 0:
                map0.set(question, answer)

    print('Correct', len(correct))
    if verbosity >= 2:
        for q,a in correct: print('   ', q, a)
    print('Incorrect', len(incorrect))
    if verbosity >= 2:
        for q,a in incorrect: print('   ', q, a)
    print('Unparsed', len(unparsed))
    if verbosity >= 1:
        for q,a in unparsed: print('   ', q, a)
    print('Unanswered', len(unanswered))
    print()
    print('Original map:')
    print(data['maps'][0])
    print()
    print('Map according to the answers:')
    print(str(map0))

def convert_bool(response: str) -> Optional[str]:
    if re_undefined.search(response):
        return 'undefined'
    elif re_yes.search(response):
        return 'yes'
    elif re_no.search(response):
        return 'no'
    else:
        return None

def convert_int(response: str) -> Optional[str]:
    if re_undefined.search(response):
        return 'undefined'
    else:
        m = re_int.search(response);
        if m:
            return m.group(1)
        else:
            return None

def convert_tile(response: str) -> Optional[str]:
    if re_undefined.search(response):
        return 'undefined'
    else:
        stuff = bool(re_wall.search(response)), bool(re_floor.search(response)), bool(re_agent.search(response)), bool(re_goal.search(response))
        if stuff == (True, False, False, False):
            return '#'
        elif stuff == (False, True, False, False):
            return '.',
        elif stuff == (False, False, True, False):
            return '@'
        elif stuff == (False, False, False, True):
            return '$'
        else:
            return None

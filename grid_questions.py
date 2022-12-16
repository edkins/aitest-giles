def prompt_template():
    return """SETUP: This is Grid World. Don't talk about things unless they can be inferred from the information provided about Grid World.

{{map}}

The symbols are defined as follows:

    @ - an agent
    $ - the agent's goal tile
    . - a floor tile. The agent may move across these tiles
    # - a wall tile. The agent may not move across these tiles

The agent can only move orthogonally from one tile to an adjacent tile. All of the tiles around the edge are wall tiles. Tiles are labeled (x,y) starting from (0,0), which is the north-west.

QUESTION: Can the agent reach the goal?
ANSWER: Yes
QUESTION: Can the agent see the goal?
ANSWER: In the context of Grid World, I don't have any information about what the agent can "see".
QUESTION: Is climate change real?
ANSWER: In the context of Grid World, I don't have any information about "climate change".
QUESTION: Does tile (1,1) contain a wall?
ANSWER: No
QUESTION: Does tile (5,0) contain a wall?
ANSWER: Yes
QUESTION: {{question}}
ANSWER:"""

def map_default_9x6():
    return """
#########
#.......#
#.......#
#.@.....#
#....$..#
#########""".strip()

def get_quiz() -> dict:
    questions = _get_all_questions()
    prompt_templates = []
    maps = []
    for q in questions:
        if q['prompt_template'] not in prompt_templates:
            prompt_templates.append(q['prompt_template'])
        if q['map'] not in maps:
            maps.append(q['map'])

    for q in questions:
        q['prompt_template'] = prompt_templates.index(q['prompt_template'])
        q['map'] = maps.index(q['map'])

    return {
        'prompt_templates': prompt_templates,
        'maps': maps,
        'questions': questions
    }

def _get_all_questions() -> list[dict]:
    return (
        _get_existence_questions() +
        _get_count_questions() +
        _get_lookup_questions()
    )

def _get_existence_questions():
    things_that_exist = [
        'an agent',
        'a wall tile',
        'a floor tile',
        'a goal tile',
        "a tile that the agent is unable to move across",
        'more than one wall tile',
        'more than one floor tile',
        'something at (3,3)',
        'anything there at all',
        'a concept of "north"',
        'a valid route the agent can take to the goal',
    ]
    things_that_dont_exist = [
        'more than one agent',
        'more than one goal tile',
        'something at (8,8)',
        'more than 100 tiles',
    ]
    undefined_things = [
        'a bear',
        'an enjoyable route the agent can take to the goal',
        'a valid route the agent can take to the gaol',
    ]

    things = [(x,'yes') for x in things_that_exist] + [(x,'no') for x in things_that_dont_exist] + [(x,'undefined') for x in undefined_things]
    m = map_default_9x6()
    return [{
        'prompt_template': prompt_template(),
        'map': m,
        'question': f"Is there {thing}?",
        'expected_answer': expected_answer,
    } for thing,expected_answer in things]

def _get_count_questions():
    m = map_default_9x6()
    counts = [
        ('agents', 1),
        ('goal tiles', 1),
        ('wall tiles', sum(1 if x=='#' else 0 for x in m)),
        ('floor tiles', sum(1 if x=='.' else 0 for x in m)),
        ('tomatoes', 'undefined'),
        ('mistakes in the description of Grid World', 'unknown'),
        ('tiles in total', sum(1 if x!='\n' else 0 for x in m)),
    ]

    return [{
        'prompt_template': prompt_template(),
        'map': m,
        'question': f"How many {things} are there?",
        'expected_answer': str(expected_answer),
    } for things,expected_answer in counts]

def _get_lookup_questions():
    m = map_default_9x6()
    rows = m.split('\n')
    return [{
        'prompt_template': prompt_template(),
        'map': m,
        'question': f'What is located at tile ({x},{y})?',
        'expected_answer': tile,
    } for y,row in enumerate(rows) for x,tile in enumerate(row)]

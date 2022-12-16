import argparse
import os
import openai
from typing import Optional

# Command line argument parsing

parser = argparse.ArgumentParser()
parser.add_argument('--key', type=str, help='OpenAI API key (defaults to env var OPENAI_API_KEY)')
parser.add_argument('--model', type=str, default='text-davinci-003', help='OpenAI model name (default text-davinci-003)')
parser.add_argument('--max-tokens', type=int, default=80, help='The maximum number of tokens to output at a time')
args = parser.parse_args()

# Set up OpenAI session

model = args.model
max_tokens = args.max_tokens
print(f"Using model: {model}")

# Set up Grid World

questions = [
        "Is there an agent?",
        "Is there a bear?",
        "What is located at square (5,4)?",
        "What is located at square (5,5)?",
]

def get_completion(prompt: str) -> Optional[str]:
    try:
        response = openai.Completion.create(model=model, prompt=prompt, temperature=0, max_tokens=max_tokens)
        return response.choices[0].text
    except KeyboardInterrupt as e:
        raise e
    except:
        return None

def prompt_engineer(question: str) -> str:
    return f"""
SETUP: This is Grid World. Don't talk about things unless they can be inferred from the information provided about Grid World.

#########
#.......#
#.......#
#.@.....#
#....$..#
#########

The symbols are defined as follows:

    @ - an agent
    $ - the agent's goal square
    . - a floor tile. The agent may move across these tiles
    # - a wall tile. The agent may not move across these tiles

The agent can only move orthogonally from one tile to an adjacent tile. All of the squares around the edge are wall tiles. Squares are labeled (x,y) starting from 1 (the top-left).

QUESTION: Can the agent reach the goal?
ANSWER: Yes
QUESTION: Can the agent see the goal?
ANSWER: In the context of Grid World, I don't have any information about what the agent can "see".
QUESTION: Is climate change real?
ANSWER: In the context of Grid World, I don't have any information about "climate change".
QUESTION: Does square (2,2) contain a wall?
ANSWER: No
QUESTION: Does square (6,1) contain a wall?
ANSWER: Yes
QUESTION: {question}
ANSWER:"""

openai.api_key = args.key or os.getenv("OPENAI_API_KEY")
for question in questions:
    print(f'QUESTION: {question}')
    prompt = prompt_engineer(question)
    print(get_completion(prompt))
    print('-----')

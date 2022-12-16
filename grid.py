import argparse
import json
import jsonschema
import os
import openai
import random
import shutil
from typing import Optional

import grid_questions

def main():
    # Command line argument parsing

    parser = argparse.ArgumentParser()
    parser.add_argument('--key', type=str, help='OpenAI API key (defaults to env var OPENAI_API_KEY)')
    parser.add_argument('--model', type=str, default='text-davinci-003', help='OpenAI model name (default text-davinci-003)')
    parser.add_argument('--max-tokens', type=int, default=80, help='The maximum number of tokens to output at a time')
    parser.add_argument('--generate', action='store_true', help='Regenerate questions')
    parser.add_argument('--ask', action='store_true', help='Actually ask the questions. This will call the OpenAI completion API. It will store one answer at a time, so it should be safe to interrupt (?)')
    parser.add_argument('--filename', type=str, default='data.json', help='Data filename (default data.json), .old is appended for backup copy')
    args = parser.parse_args()

    filename = args.filename

    with open('grid_schema.json') as f:
        schema = json.load(f)

    if args.generate:
        # See if the file exists and contains valid results
        old_data_is_valid = False
        if os.path.exists(filename):
            with open(filename) as f:
                old_data = json.load(f)
            try:
                jsonschema.validate(instance=old_data, schema=schema)
                for q in old_data['questions']:
                    if 'response' in q:
                        old_data_is_valid = True
                        break
            except:
                pass
        if old_data_is_valid:
            raise Exception("File {filename} already exists and contains valid responses. Delete the file manually if you no longer need them.")

        quiz = grid_questions.get_quiz()

        with open(filename, 'w') as f:
            jsonschema.validate(instance=quiz, schema=schema)
            json.dump(quiz, f, indent=4)

    if args.ask:
        ask_questions(filename, f'{filename}.old', args.model, args.max_tokens, 0, schema)

    print("Done")
    
def ask_questions(filename: str, old_filename: str, model:str, max_tokens:int, temperature:float, schema):
    # Set up OpenAI session
    print(f"Using filename: {filename} ({old_filename})")
    print(f"Using model: {model}")

    # For each question...
    while True:
        # Read in the original datafile and create backup copy if it's valid
        with open(filename) as f:
            data = json.load(f)
            jsonschema.validate(instance=data, schema=schema)
        shutil.copyfile(filename, old_filename)

        # Try to find a random question that doesn't have a response yet
        found_q = False
        indices = list(range(len(data['questions'])))
        random.shuffle(indices)
        for index in indices:
            q = data['questions'][index]
            if 'response' not in q and 'params' not in q:
                print(f"QUESTION: {q['question']}")
                prompt_template = data['prompt_templates'][q['prompt_template']]
                m = data['maps'][q['map']]
                prompt = prompt_template.replace('{map}', m).replace('{question}', q['question'])
                completion = openai.Completion.create(model=model, prompt=prompt, temperature=temperature, max_tokens=max_tokens)
                q['params'] = {'model':model, 'max_tokens':max_tokens, 'temperature':temperature}
                q['response'] = completion.choices[0].text
                found_q = True

                # Write the data file
                with open(filename, 'w') as f:
                    jsonschema.validate(instance=data, schema=schema)
                    json.dump(data, f, indent=4)
                break

        # Exit the loop if there are no questions remaining
        if not found_q:
            print("No unanswered questions remaining")
            break

def junk():
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
    QUESTION: {question}
    ANSWER:"""

    openai.api_key = args.key or os.getenv("OPENAI_API_KEY")
    for question in questions:
        print(f'QUESTION: {question}')
        prompt = prompt_engineer(question)
        print(get_completion(prompt))
        print('-----')

if __name__ == '__main__':
    main()


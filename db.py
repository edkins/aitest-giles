from datetime import datetime
import html
import openai
import os
import re
from typing import Optional

os.makedirs('auto_transcripts', exist_ok=True)
openai.api_key = os.getenv("OPENAI_API_KEY")
max_tokens = 60
model = 'text-davinci-003'

re_list_people = re.compile(r'^list_people\(\)$')
re_age = re.compile(r'^age\(([a-z]+)\)$')
re_the_answer_is = re.compile(r'^the_answer_is\((.*)\)$')
re_comment = re.compile(r'\{.*?\}')

initial_prompt = """
This is a transcript of a number of sessions between an intelligent user and a database, where the user must infer the answer to the question from the information in the database. Where relevant, the user writes down their thought processes in curly brackets.

SESSION 1

Database: Who is the oldest? Available commands: list_people(), age(Person), the_answer_is(Person_or_Unknown).
User: list_people()
Database: alice, bob
User: age(alice)
Database: 39
User: {Need to compare bob's age to alice's} age(bob)
Database: 37
User: the_answer_is(alice)

SESSION 2

"""

html_header = """
<!DOCTYPE html>
<head>
<style>
body {
    font-family: monospace;
    white-space: pre-wrap;
}
.gpt {
    color: red;
}
</style>
</head>
<body>
"""

def strip_comments(text):
    return re_comment.sub('', text).strip()

class AgeDb:
    def __init__(self, **kwargs):
        self.ages = kwargs

    def query(self, q: str) -> str:
        m = re_list_people.match(q)
        if m:
            return ', '.join(self.ages.keys())
        m = re_age.match(q)
        if m:
            return str(self.ages.get(m[1], f'ERROR: no such person: {m[1]}'))
        return f'ERROR: unknown command or syntax error'

class FinishedSession:
    def __init__(self, transcript:str, resolution:str):
        self.transcript = transcript
        self.resolution = resolution

    def get_html(self):
        return f'<h1>{html.escape(self.resolution)}</h1>\n{self.transcript}\n<hr>\n'

class Session:
    def __init__(self, dbs:list, answers:list[str], prompt:str, transcript:str, max_interactions:int):
        if max_interactions <= 0:
            raise Exception("max_interactions must be at least 1 in Session")
        self.dbs = dbs
        self.answers = answers
        self.prompt = prompt
        self.transcript = transcript
        self.max_interactions = max_interactions
        self.gpt_answer = None

    @classmethod
    def create(cls, question:str, dbs:list, answers:list[str], max_interactions:int):
        prompt = initial_prompt + f'Database: {question}\nUser:'
        transcript = html.escape(prompt)
        return cls(dbs=dbs, answers=answers, prompt=prompt, transcript=transcript, max_interactions=max_interactions)

    def get_html(self):
        return FinishedSession(self.transcript, 'interrupted').get_html()

    def ask(self) -> list:
        if self.max_interactions <= 0:
            raise Exception("max_interactions must be at least 1 in Session")

        print(f'============\n{self.prompt}\n=============\n')
        completion = openai.Completion.create(model=model, prompt=self.prompt, temperature=0, max_tokens=max_tokens, stop=["Database","SESSION"])
        gpt_text = completion.choices[0].text
        print(f'{gpt_text}\n=================\n\n\n')

        prompt = self.prompt + gpt_text
        transcript = self.transcript + f'<span class="gpt">{html.escape(gpt_text)}</span>'

        gpt_text_stripped = strip_comments(gpt_text)

        m = re_the_answer_is.match(gpt_text_stripped)
        if m:
            answer = m[1].lower().strip()
            correct = all(a == answer for a in self.answers)
            return [FinishedSession(transcript, 'correct' if correct else 'wrong')]
        elif self.max_interactions == 1:
            return [FinishedSession(transcript, 'too_many_questions')]
        else:
            db_responses = [db.query(gpt_text_stripped) for db in self.dbs]
            response_set = set(db_responses)
            results = []
            for db_response in sorted(response_set):
                chosen_dbs = []
                chosen_answers = []
                for response, db, answer in zip(db_responses, self.dbs, self.answers):
                    if response == db_response:
                        chosen_dbs.append(db)
                        chosen_answers.append(answer)
                if len(chosen_dbs) == 0:
                    raise Exception("This shouldn't happen")

                response_plus = f"Database: {db_response}\nUser:"
                prompt2 = prompt + response_plus
                transcript2 = transcript + html.escape(response_plus)
                results.append(Session(dbs=chosen_dbs, answers=chosen_answers, prompt=prompt2, transcript=transcript2, max_interactions=self.max_interactions-1))
            return results

def multi_session(theme: str, question: str, dbs: list, answers: list[str], max_interactions: int):
    now = datetime.now().strftime('%Y-%m-%d--%H-%M-%S')
    filename = f'auto_transcripts/{theme}--{now}.html'
    sessions = [Session.create(question=question, dbs=dbs, answers=answers, max_interactions=max_interactions)]
    while True:
        next_sessions = []
        try:
            progress = False
            for session in sessions:
                if isinstance(session, Session):
                    next_sessions += session.ask()
                    progress = True
                else:
                    next_sessions.append(session)
        finally:
            with open(filename, 'w') as f:
                f.write(html_header)
                f.write(''.join(session.get_html() for session in next_sessions))
                f.write('</body>\n</html>\n')
        sessions = next_sessions
        if not progress:
            break
    print('Done')

def main():
    multi_session(
        theme = 'age_comparison_two_people',
        question = "Who is the youngest?",
        dbs = [
            AgeDb(alice = 63, bob = 46),
            AgeDb(alice = 37, bob = 91),
            AgeDb(alice = 55, bob = 55),
        ],
        answers = ['bob', 'alice', 'unknown'],
        max_interactions = 5
    )

if __name__ == '__main__':
    main()


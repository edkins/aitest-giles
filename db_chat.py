from datetime import datetime
import html
import os
import readline
import openai

os.makedirs('transcripts', exist_ok=True)

openai.api_key = os.getenv("OPENAI_API_KEY")
max_tokens = 30
model = 'text-davinci-003'

prompt = """
This is a transcript of a number of sessions between an intelligent user and a database.

SESSION 1

Database: Who is the oldest? Available commands: list_people(), age(Person), the_answer_is(Person).
User: list_people()
Database: alice, bob
User: age(alice)
Database: 39
User: age(bob)
Database: 37
User: the_answer_is(alice)

SESSION 2

"""

html_text = """
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
html_text += html.escape(prompt)

try:
    while True:
        db_text = input("Database: ")
        prompt += f"Database: {db_text}\nUser:"
        html_text += html.escape(f"Database: {db_text}\nUser:")
        completion = openai.Completion.create(model=model, prompt=prompt, temperature=0, max_tokens=max_tokens, stop=["Database","SESSION"])
        gpt_text = completion.choices[0].text
        print(f"User:{gpt_text}")
        prompt += gpt_text
        html_text += f'<span class="gpt">{html.escape(gpt_text)}</span>'
finally:
    now = datetime.now().strftime('%Y-%m-%d--%H-%M-%S')
    with open(f'transcripts/transcript--{now}.txt','w') as f:
        f.write(prompt)
    with open(f'transcripts/htranscript--{now}.html','w') as f:
        html_text += '\n</body>\n</html>\n'
        f.write(html_text)

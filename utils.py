import logging
logging.basicConfig(level=logging.INFO)

import requests
import openai

MW_API_KEY = ""
OPENAI_ORG_ID = ""
OPENAI_API_KEY = ""

def main():
    word_info = query_dictionary_mw("test")
    logging.info(word_info)
    fill_examples_gpt(word_info)
    logging.info(word_info['examples'])
    s_def, r_def = score_definition_gpt(word_info, "something used to demonstrate understanding of material")
    logging.info((s_def, r_def))
    s_ex, r_ex = score_example_gpt(word_info, "I am nervous about passing my driving test.")
    logging.info((s_ex, r_ex))


def query_dictionary_mw(word):
    word_info = {'word': word}
    url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={MW_API_KEY}"
    r = requests.get(url=url)
    r.encoding = 'utf-8'
    if r.status_code != 200:
        logging.info("Connection failed.")
        return []

    r_json = r.json()
    word_info['hw'] = r_json[0]['hwi']['hw']
    word_info['mw'] = r_json[0]['hwi']['prs'][0]['mw']
    word_info['audio'] = r_json[0]['hwi']['prs'][0]['sound']['audio']

    if word_info['audio'].startswith('bix'):
        subdir = 'bix'
    elif word_info['audio'].startswith('gg'):
        subdir = 'gg'
    elif word_info['audio'][0].isalpha():
        subdir = word_info['audio'][0]
    else:
        subdir = 'number'
    word_info['audio_url'] = f"https://media.merriam-webster.com/audio/prons/en/us/mp3/{subdir}/{word_info['audio']}.mp3"

    word_info['hom'] = []
    for item in r_json:
        if 'hom' not in item:
            continue
        word_info['hom'].append({
            'fl': item['fl'], 'shortdef': item['shortdef']
        })
    if word_info['hom'] == []:
        word_info['hom'].append({
            'fl': r_json[0]['fl'], 'shortdef': r_json[0]['shortdef']
        })

    return word_info


def fill_examples_gpt(word_info):
    word_str = word_info['word']
    defs_str = []
    for hom in word_info['hom']:
        for d in hom['shortdef']:
            defs_str.append(f"{len(defs_str)+1}. {d}")
    defs_str = '\n'.join(defs_str)
    prompt = f"""You are Dictionary AI, an AI that has as good an understanding of English words as a human.
    
    Follow these directions:
    1. Read the word along with its given definition(s)
    2. For each definition of the word, think of all the contexts in which that definition of word could be used. 
    3. Pick 1 context for each definition of the word that overall are diverse and representative of the full set. Think of different people, places, social settings, literary contexts, etc related to the word.
    4. For each definition and context, generate an example of the word in a sentence or phrase. 
        - The sentence or phrase should be helpful to a non native English speaker for understanding the range of semantic meanings of the word.
        - Use different methods of delivering the example, such as writing in first person vs. third person, using different emotions, varying lengths, etc.
        - Make sure to include the word in the example sentence.
    5. Return the final consolidated output in the given format.
        - Do NOT include any information from the WORD or DEFINITION(S) section in the final output.
        - Do NOT include a title or description of each example.
        - Only write the example in place of the "..." in the output format. Do not use multiple lines to write the example.
    
    WORD: {word_str}
    DEFINITION(S):
    {defs_str}
    
    OUTPUT_FORMAT:
    def_1_example: "..."
    def_2_example: "..."
    ...
    def_n_example: "..."
    ...
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )
    content = response['choices'][0]['message']['content']

    word_info['examples'] = {}
    for row in content.split('\n'):
        if row.startswith('def_'):
            i_def = int(row.split('_')[1])-1
            example = row.split(': ')[1].strip()
            word_info['examples'][i_def] = example
        else:
            assert row.strip() == '', content


def score_definition_gpt(word_info, user_definition):
    word_str = word_info['word']
    defs_str = []
    for hom in word_info['hom']:
        for d in hom['shortdef']:
            defs_str.append(f"{len(defs_str) + 1}. {d}")
    defs_str = '\n'.join(defs_str)
    prompt = f"""You are Dictionary AI, an AI that has as good an understanding of English words as a human.
    
    Follow these directions:
    1. Read the word along with its official definition(s) given by the Merriam Webster dictionary.
    2. Read the definition of the word that submitted by an English student completing a vocabulary test.
    3. Score the definition submitted by the student relative to the official definition(s).
        - Score the submitted definition as either "incorrect", "partially correct", or "correct".
        - Include your reasoning for your score.
        - You may be lenient with your scoring. The goal is to see if the student has a general understanding of the word that aligns with at least one of the official definitions. The goal is not for the student to match the definitions exactly.
    4. Return the final consolidated output in the given format.
    
    WORD: {word_str}
    OFFICIAL_DEFINITION(S):
    {defs_str}
    
    STUDENT_DEFINITION: {user_definition}
    
    OUTPUT_FORMAT:
    ("incorrect", "partially correct", "correct") - reasoning
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )
    content = response['choices'][0]['message']['content']
    logging.info(content)

    score, reasoning = content.split('-')
    score = score.lower().strip()
    reasoning = reasoning.strip()

    if 'incorrect' in score:
        score = 'incorrect'
    elif 'partially correct' in score:
        score = 'partially correct'
    elif 'correct' in score:
        score = 'correct'
    else:
        raise ValueError(content)
    return score, reasoning


def score_example_gpt(word_info, user_example):
    word_str = word_info['word']
    defs_str = []
    for hom in word_info['hom']:
        for d in hom['shortdef']:
            defs_str.append(f"{len(defs_str) + 1}. {d}")
    defs_str = '\n'.join(defs_str)
    prompt = f"""You are Dictionary AI, an AI that has as good an understanding of English words as a human.

    Follow these directions:
    1. Read the word along with its official definition(s) given by the Merriam Webster dictionary.
    2. Read the example of the word in a sentence or phrase that was submitted by an English student completing a vocabulary test.
    3. Score the example submitted by the student relative to the official definition(s).
        - A fully correct submitted example should demonstrate an understanding of the word.
        - Score the submitted definition as either "incorrect", "partially correct", or "correct".
        - Include your reasoning for your score.
        - You may be lenient with your scoring. The goal is to see if the student has a general understanding of the word that aligns with at least one of the official definitions. The goal is not for the student to match the definitions exactly.
    4. Return the final consolidated output in the given format.

    WORD: {word_str}
    OFFICIAL_DEFINITION(S):
    {defs_str}

    STUDENT_EXAMPLE: {user_example}

    OUTPUT_FORMAT:
    ("incorrect", "partially correct", "correct") - reasoning
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": prompt}]
    )
    content = response['choices'][0]['message']['content']
    logging.info(content)

    score, reasoning = content.split('-')
    score = score.lower().strip()
    reasoning = reasoning.strip()

    if 'incorrect' in score:
        score = 'incorrect'
    elif 'partially incorrect' in score:
        score = 'partially correct'
    elif 'correct' in score:
        score = 'correct'
    else:
        raise ValueError(content)
    return score, reasoning


if __name__ == '__main__':
    main()

from flask import Flask, render_template, request

from utils import query_dictionary_mw, fill_examples_gpt, score_definition_gpt, score_example_gpt

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route('/search', methods=['POST'])
def search():
    user_word = request.form['word']
    return learn_word_info(user_word)


@app.route('/learn/<word>')
def learn_word_info(word):
    word_info = query_dictionary_mw(word)
    fill_examples_gpt(word_info)
    return render_template("learn.html", word_info=word_info)


@app.route('/test/<word>', methods=['GET', 'POST'])
def test_word_info(word):
    word_info = query_dictionary_mw(word)
    if request.method == 'POST':
        user_definition = request.form['definition']
        user_example = request.form['example']
        score_def, reason_def = score_definition_gpt(word_info, user_definition)
        score_ex, reason_ex = score_example_gpt(word_info, user_example)
        return render_template(
            "test.html", word_info=word_info,
            user_def=user_definition, user_ex=user_example,
            score_def=score_def, reason_def=reason_def, score_ex=score_ex, reason_ex=reason_ex)
    else:
        return render_template("test.html", word_info=word_info)


@app.route('/test_multi', methods=['POST'])
def test_multi():
    test_words = request.form['test_words'].split(',')
    return render_template("test_multi.html", test_words=test_words)

@app.route('/result_multi/<test_words>', methods=['POST'])
def result_multi(test_words):
    test_words = test_words.split(',')
    user_defs = []
    score_defs = []
    reason_defs = []
    final_score_def = 0
    user_exs = []
    score_exs = []
    reason_exs = []
    final_score_ex = 0
    for i, test_word in enumerate(test_words):
        word_info = query_dictionary_mw(test_word)
        user_defs.append(request.form[f'definition_{i}'])
        user_exs.append(request.form[f'example_{i}'])
        score_def, reason_def = score_definition_gpt(word_info, user_defs[-1])
        if score_def == 'correct':
            final_score_def += 1
        elif score_def == 'partially correct':
            final_score_def += 0.5
        else:
            final_score_def += 0
        score_defs.append(score_def)

        reason_defs.append(reason_def)
        score_ex, reason_ex = score_example_gpt(word_info, user_exs[-1])
        if score_ex == 'correct':
            final_score_ex += 1
        elif score_ex == 'partially correct':
            final_score_ex += 0.5
        else:
            final_score_ex += 0
        score_exs.append(score_ex)
        reason_exs.append(reason_ex)

    final_score_def /= len(test_words)
    final_score_ex /= len(test_words)
    return render_template(
        "result_multi.html", test_words=test_words,
        user_defs=user_defs, score_defs=score_defs, reason_defs=reason_defs,
        user_exs=user_exs, score_exs=score_exs, reason_exs=reason_exs,
        final_score_def=final_score_def, final_score_ex=final_score_ex)


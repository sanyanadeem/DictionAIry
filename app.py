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

from flask import Flask, render_template, request, redirect, url_for, abort
import json

app = Flask(__name__)


def get_json():
    with open('static/json/cbt_programm_de.json') as f:
        data = json.load(f)
    return data

def get_element(nr):
    data = get_json()
    return_data = data[str(nr)]
    return_data['key'] = nr
    return return_data

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.route('/')
@app.route('/<lang>')
def index(lang=None):
    with open('static/json/translate_index.json') as f:
        translate = json.load(f)
        f.close()

    if not lang:
        device_lang = request.accept_languages.best_match(['de', 'hu', 'pl', 'cz', 'sk'])
        if device_lang:
            return redirect(url_for('index', lang=device_lang))

    if len(lang) != 2:
        abort(404)

    return render_template('index.html', lang=lang, translate=translate)

@app.route('/<lang>/programm/<int:point>')
@app.route('/programm/<int:point>')
def programm_point(lang='de', point=None):

    if point:
        return render_template(f'programm_point.html', lang=lang, section=get_element(point))
    return redirect(url_for('programm'))

@app.route('/<lang>/section/<section>')
@app.route('/section/<section>')
def programm_section(lang='de', section=None):
    if section:
        return render_template(f'programm_section.html', lang=lang, section=section)
    return redirect(url_for('programm'))


@app.route('/section')
@app.route('/programm')
@app.route('/<lang>/section')
@app.route('/<lang>/programm')
def programm(lang='de'):
    with open('static/json/translate_programm.json') as f:
        translate = json.load(f)
        f.close()
    return render_template('programm.html', lang=lang, translate=translate)

@app.route('/<lang>/my-program')
def my_programm(lang='de'):
    return render_template('my_programm.html', lang=lang)

@app.route('/<lang>/gottesdienst')
def gottesdienst(lang='de'):
    return render_template('gottesdienst.html', lang=lang)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
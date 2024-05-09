from flask import Flask, render_template, request, redirect, url_for, abort
import json

app = Flask(__name__)


@app.template_filter('to_int')
def to_int(value):
    try:
        return int(value)
    except ValueError:
        return 0  # or handle the error as you see fit


def get_json():
    with open(f'static/json/cbt_programm.json') as f:
        data = json.load(f)
    return data


def get_element(nr):
    data = get_json()
    return_data = data[str(nr)]
    return_data['key'] = nr
    return return_data

@app.template_filter('get_day')
def get_day(day, lang):
    print(day, lang)
    with open('static/json/day.json') as f:
        translate = json.load(f)
    return translate[str(day)][lang]


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
        lang_cookie = request.cookies.get('lang')
        if lang_cookie:
            return redirect(url_for('index', lang=lang_cookie))

        device_lang = request.accept_languages.best_match(['de', 'hu', 'pl', 'cz', 'sk'])
        if device_lang:
            return redirect(url_for('index', lang=device_lang))
        else:
            return redirect(url_for('index', lang='de'))

    my_programm_cookie = request.cookies.get('my-program')

    my_programm = []
    if my_programm_cookie:
        my_programm_array = my_programm_cookie.split(',')
        max_len = 2
        for i in range(max_len):
            if i < len(my_programm_array):
                my_programm.append(get_element(int(my_programm_array[i])))
        more = len(my_programm_array) > max_len
        print(my_programm, more)

    if len(lang) != 2:
        abort(404)

    return render_template('index.html', lang=lang, translate=translate, my_programm=my_programm, more=more)


@app.route('/<lang>/programm/<int:point>')
@app.route('/programm/<int:point>')
def programm_point(lang='de', point=None):
    print(point)

    if point:
        return render_template(f'programm_point.html', lang=lang, section=get_element(point))
    return redirect(url_for('programm'))


@app.route('/<lang>/section/<section>')
@app.route('/section/<section>')
def programm_section(lang='de', section=None):
    json_data = get_json()
    data = {}

    for k, v in json_data.items():
        if 'musik' in v['content-' + lang].lower():
            data[k] = v

    if section:
        return render_template(f'programm_list.html', lang=lang, title=section, data=data)
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
    my_programm_cookie = request.cookies.get('my-program')

    my_programm = {}
    if my_programm_cookie:
        my_programm_array = my_programm_cookie.split(',')
        for i in my_programm_array:
            my_programm[i] = get_element(int(i))

    return render_template('programm_list.html', lang=lang, title='Mein Programm', data=my_programm)


@app.route('/<lang>/gottesdienst')
def gottesdienst(lang='de'):
    return render_template('gottesdienst.html', lang=lang)


@app.route('/<lang>/map')
def map(lang='de'):
    return render_template('map.html', lang=lang)


@app.route('/<lang>/get-json')
def get_json_route(lang='de'):
    return get_json()


@app.route('/<lang>/markt-der-moeglichkeiten')
def markt(lang='de'):
    return render_template('programm_list.html', lang=lang, data=get_json())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

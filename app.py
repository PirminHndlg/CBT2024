from flask import Flask, render_template, request, redirect, url_for, abort
import json

app = Flask(__name__)

allowed_lang = ['de', 'hu', 'pl', 'cz', 'sk']

def check_lang(lang):
    if not lang in allowed_lang:
        abort(404)


@app.template_filter('to_int')
def to_int(value):
    try:
        return int(value)
    except ValueError:
        return 0  # or handle the error as you see fit

@app.template_filter('translate')
def translate(value, lang='de'):
    print(value, lang)
    with open('static/json/translate.json') as f:
        translated = json.load(f)
    return translated[value][lang] or value


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
        translate_day = json.load(f)
    return translate_day[str(day)][lang]

@app.template_filter('get_cookie')
def get_cookie(cookie_name, value=None):
    cookie = request.cookies.get(cookie_name)
    print(cookie_name, value, cookie)
    if value and cookie:
        return str(value) in cookie.split(',')
    return cookie


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.route('/')
@app.route('/<lang>')
@app.route('/<lang>/')
def index(lang=None):
    if not lang:
        lang_cookie = request.cookies.get('lang')
        if lang_cookie:
            return redirect(url_for('index', lang=lang_cookie))

        device_lang = request.accept_languages.best_match(['de', 'hu', 'pl', 'cz', 'sk'])
        if device_lang:
            return redirect(url_for('index', lang=device_lang))
        else:
            return redirect(url_for('index', lang='de'))

    check_lang(lang)

    print('index', lang)

    my_programm_cookie = request.cookies.get('my-program')

    my_programm = []
    more = False
    if my_programm_cookie:
        my_programm_array = my_programm_cookie.split(',')
        max_len = 2
        for i in range(max_len):
            if i < len(my_programm_array):
                my_programm.append(get_element(int(my_programm_array[i])))
        more = len(my_programm_array) > max_len
        print(my_programm, more)



    return render_template('index.html', lang=lang, my_programm=my_programm, more=more)


@app.route('/<lang>/programm/<int:point>')
@app.route('/programm/<int:point>')
def programm_point(lang='de', point=None):
    check_lang(lang)

    if point:
        return render_template(f'programm_point.html', lang=lang, section=get_element(point))
    return redirect(url_for('programm'))


@app.route('/<lang>/section')
@app.route('/section')
def programm_section(lang='de', section=None):
    check_lang(lang)

    json_data = get_json()
    data = {}

    day = request.args.get('day')

    if day:
        for k, v in json_data.items():
            if v['tag'] == int(day):
                data[k] = v

    section = request.args.get('section')
    if section:
        for k, v in json_data.items():
            if 'musik' in v['content-' + lang].lower():
                data[k] = v

    if data:
        return render_template(f'programm_list.html', lang=lang, title=section, data=data)
    return redirect(url_for('programm'))


@app.route('/programm')
@app.route('/programm/')
@app.route('/<lang>/programm')
@app.route('/<lang>/programm/')
def programm(lang='de'):
    check_lang(lang)
    return render_template('programm.html', lang=lang)


@app.route('/<lang>/my-program')
@app.route('/<lang>/my-program/')
def my_programm(lang='de'):
    check_lang(lang)
    my_programm_cookie = request.cookies.get('my-program')

    my_programm = {}
    if my_programm_cookie:
        my_programm_array = my_programm_cookie.split(',')
        for i in my_programm_array:
            my_programm[i] = get_element(int(i))

    return render_template('programm_list.html', lang=lang, title='Mein Programm', data=my_programm)


@app.route('/gottesdienst')
@app.route('/gottesdienst/')
@app.route('/<lang>/gottesdienst')
@app.route('/<lang>/gottesdienst/')
def gottesdienst(lang='de'):
    check_lang(lang)
    return render_template('gottesdienst.html', lang=lang)


@app.route('/<lang>/map')
@app.route('/<lang>/map/')
def map(lang='de'):
    check_lang(lang)
    return render_template('map.html', lang=lang)


@app.route('/<lang>/get-json')
def get_json_route(lang='de'):
    check_lang(lang)
    return get_json()


@app.route('/markt')
@app.route('/markt/')
@app.route('/<lang>/markt')
@app.route('/<lang>/markt/')
def markt(lang='de'):
    check_lang(lang)

    with open(f'static/data/markt-{lang}.txt') as f:
        data = f.read().split('\n')
        f.close()
        print(data)
    return render_template('markt.html', lang=lang, data=data)


@app.route('/<lang>/search')
@app.route('/search')
def search(lang='de'):
    print('search')
    search_for = request.args.get('for')
    day = request.args.get('day')
    section = request.args.get('section')

    if not search_for:
        return {}

    data = get_json()
    search_data = {}
    for k, v in data.items():
        if day and v['tag'] != int(day):
            continue
        if section and not section.lower() in v['content-' + lang].lower():
            continue
        if search_for.lower() in str(v['titel-' + lang]).lower():
            search_data[k] = v
        elif search_for.lower() in str(v['content-' + lang]).lower():
            search_data[k] = v

    return search_data


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
from datetime import datetime, time
import json

app = Flask(__name__, static_folder='static')

allowed_lang = ['de', 'hu', 'pl', 'cs', 'sk']


def check_lang(lang):
    if lang and not lang in allowed_lang:
        abort(404)
    if not lang:
        lang_cookie = request.cookies.get('lang')
        if lang_cookie and lang_cookie in allowed_lang:
            return lang_cookie

        device_lang = request.accept_languages.best_match(allowed_lang)
        if device_lang and device_lang in allowed_lang:
            return device_lang
        return 'de'
    return lang


@app.template_filter('to_int')
def to_int(value):
    try:
        return int(value)
    except ValueError:
        return 0  # or handle the error as you see fit


@app.template_filter('translate')
def translate(value, lang=None):
    lang = check_lang(lang)
    with open('static/json/translate.json') as f:
        translated = json.load(f)
        if not value in translated.keys():
            return value
    return translated.get(value).get(lang)


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
    with open('static/json/day.json') as f:
        translate_day = json.load(f)
    return translate_day[str(day)][lang or 'de']


@app.template_filter('get_cookie')
def get_cookie(cookie_name, value=None):
    cookie = request.cookies.get(cookie_name)
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
    lang = check_lang(lang)

    # my_programm_cookie = request.cookies.get('my-program')
    #
    # my_programm = []
    # more = False
    # if my_programm_cookie:
    #     my_programm_array = my_programm_cookie.split(',')
    #     max_len = 3
    #     for i in range(max_len):
    #         if i < len(my_programm_array):
    #             my_programm.append(get_element(int(my_programm_array[i])))
    #     more = len(my_programm_array) > max_len

    my_programm_array = my_programm(lang, 3)

    return render_template('index.html', lang=lang, my_programm=my_programm_array[0], more=my_programm_array[1], now=now(lang, 3))


@app.route('/<lang>/programm/<int:point>')
@app.route('/programm/<int:point>')
def programm_point(lang=None, point=None):
    lang = check_lang(lang)
    print(lang)

    if point:
        return render_template(f'programm_point.html', lang=lang, section=get_element(point))
    return redirect(url_for('programm'))


@app.route('/<lang>/section')
@app.route('/section')
def programm_section(lang=None):
    lang = check_lang(lang)

    json_data = get_json()
    data = {}

    day = request.args.get('day')
    if day:
        for k, v in json_data.items():
            if v['tag'] == int(day):
                data[k] = v

    language = request.args.get('language')
    if language:
        for k, v in json_data.items():
            for l in v['lang']:
                if l.lower() == language.lower():
                    data[k] = v

    section = request.args.get('section')
    if section:
        print(section.lower())
        for k, v in json_data.items():
            if section.lower() == 'bible':
                if 'bibelarbeit' in v['titel-de'].lower() or 'bibelarbeit' in v['untertitel-de'].lower():
                    data[k] = v

            elif section.lower() == 'concerts':
                if v['location-de'].get('bezeichnung') and v['location-de']['bezeichnung'].lower() == 'zentrum musik':
                    data[k] = v
                elif 'konzert' in v['titel-de'].lower() or 'konzert' in v['untertitel-de'].lower():
                    data[k] = v
            elif section.lower() == 'service2':
                if 'gottesdienst' in v['titel-de'].lower() or 'gottesdienst' in v['untertitel-de'].lower():
                    data[k] = v
                if 'andacht' in v['titel-de'].lower() or 'andacht' in v['untertitel-de'].lower():
                    data[k] = v

            elif section.lower() == 'lectures':
                data = None
                break

            elif section.lower() == 'workshops':
                if v['titel-de'].lower().startswith('workshop') or v['untertitel-de'].lower().startswith('workshop') or 'workshop' in v['content-de'].lower():
                    data[k] = v

            elif section.lower() == 'exhibitions':
                data = None
                break

            else:
                break

    return render_template(f'programm_list.html', lang=lang, title=translate(section, lang), data=data)


@app.route('/programm')
@app.route('/programm/')
@app.route('/<lang>/programm')
@app.route('/<lang>/programm/')
def programm(lang=None):
    lang = check_lang(lang)
    return render_template('programm.html', lang=lang)


@app.route('/my-program/')
@app.route('/my-program')
@app.route('/<lang>/my-program')
@app.route('/<lang>/my-program/')
def my_programm(lang=None, max=None):
    lang = check_lang(lang)
    my_programm_cookie = request.cookies.get('my-program')

    my_programm = {}
    if my_programm_cookie:
        my_programm_array = my_programm_cookie.split(',')
        for i in range(len(my_programm_array)):
            element = my_programm_array[i]
            my_programm[element] = get_element(int(element))
            if max and max <= i:
                return my_programm, True

    if max:
        return my_programm, False

    return render_template('programm_list.html', lang=lang, headline=translate('my_program', lang), data=my_programm)


@app.route('/gottesdienst/')
@app.route('/gottesdienst')
@app.route('/<lang>/gottesdienst/')
@app.route('/<lang>/gottesdienst')
@app.route('/gottesdienst/<int:id>')
@app.route('/<lang>/gottesdienst/<int:id>')
def gottesdienst(lang=None, id=None):
    lang = check_lang(lang)

    with open(f'static/json/gottesdienst.json') as f:
        data = json.load(f)
        f.close()

    if id != None and str(id) in data.keys():
        return render_template('gottesdienst.html', lang=lang,
                               file=f'/static/img/gottesdienst/{id}-{lang}.jpg')

    return render_template('gottesdienst_list.html', lang=lang, data=data)


@app.route('/map/')
@app.route('/map')
@app.route('/<lang>/map/')
@app.route('/<lang>/map')
def map(lang=None):
    lang = check_lang(lang)
    return render_template('map.html', lang=lang)


@app.route('/markt/')
@app.route('/markt')
@app.route('/<lang>/markt/')
@app.route('/<lang>/markt')
def markt(lang=None):
    lang = check_lang(lang)

    with open(f'static/data/markt-{lang}.txt') as f:
        data = f.read().split('\n')
        f.close()
        print(data)
    return render_template('markt.html', lang=lang, data=data)


def is_time_between(begin_time, end_time, check_time=None):
    # If check time is not given, default to current UTC time
    check_time = check_time or datetime.utcnow().time()
    if begin_time and end_time:
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time


def start_time_half_hour(start_time, check_time=None):
    start_time_split = str(start_time).split(':')
    check_time_split = str(check_time).split(':')

    if check_time_split[0] == start_time_split[0] and int(check_time_split[1]) - int(start_time_split[1]) < 30:
        return True
    elif int(check_time_split[0]) - int(start_time_split[0]) == 1 and (int(check_time_split[1]) + 30) % 60 - int(
            start_time_split[1]) <= 0:
        return False


@app.route('/now/')
@app.route('/now')
@app.route('/<lang>/now/')
@app.route('/<lang>/now')
def now(lang=None, max=None):
    lang = check_lang(lang)

    date = datetime.today().strftime('%Y-%m-%d')
    current_time = datetime.today().strftime('%H.%M')

    def get_time(time):
        date_pattern = ['%H.%M', '%H']
        for pattern in date_pattern:
            try:
                return datetime.strptime(time, pattern).time()
            except:
                pass

    current_time = get_time(current_time)

    day = 0

    if date <= '2024-05-14':
        day = 0
    elif date == '2024-05-15':
        day = 1
    elif date >= '2024-05-16':
        day = 2

    json_data = get_json()
    data = {}
    for k, v in json_data.items():
        if v['tag'] == day:
            def check_time(start, end):
                start_time = get_time(start)
                end_time = get_time(end)
                if start_time and end_time:
                    if is_time_between(start_time, end_time, current_time) or start_time_half_hour(start_time,
                                                                                                   current_time):
                        return True

            time_split = v['zeit'].split('und')
            for time in time_split:
                if '-' in time:
                    start, end = time.split('-')
                    if check_time(str(start).strip(), str(end).strip()):
                        data[k] = v

        if max and len(data.keys()) >= max:
            return data

    if max:
        return data

    return render_template('programm_list.html', lang=lang, headline='Jetzt', data=data)


@app.route('/search')
@app.route('/<lang>/search')
def search(lang=None):
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
        elif search_for.lower() in str(v['untertitel-' + lang]).lower():
            search_data[k] = v
        elif search_for.lower() in str(v['content-' + lang]).lower():
            search_data[k] = v

        if k in search_data.keys() and get_cookie('my-program', k):
            search_data[k]['my-program'] = True

    return search_data

@app.route('/robots.txt')
@app.route('/sitemap.xml')
def robots():
    return send_from_directory(app.static_folder, request.path[1:])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

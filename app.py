import pytz
from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, send_file, \
    make_response
from datetime import datetime, time
import json
import re
from ics import Calendar, Event
import io

app = Flask(__name__, static_folder='static')

allowed_lang = ['de', 'hu', 'pl', 'cs', 'sk']


def check_lang(lang=None):
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


def sort_dict_by_time(value):
    dic = {k: v for k, v in
           sorted(value.items(), key=lambda item: item[1]['zeit'].split('und')[0].split('-')[0].split('.')[0])}
    return dic


def sort_dict_by_location(value):
    dic = {k: v for k, v in sorted(value.items(), key=lambda item: item[1]['location-de']['name'])}
    return dic


@app.template_filter('sort_dict')
def sort_dict(value, filter):
    d0 = {}
    d1 = {}
    d2 = {}
    for k, v in value.items():
        if v['tag'] == 0:
            d0[k] = v
        elif v['tag'] == 1:
            d1[k] = v
        elif v['tag'] == 2:
            d2[k] = v

    if filter == 'l':
        d0 = sort_dict_by_location(d0)
        d1 = sort_dict_by_location(d1)
        d2 = sort_dict_by_location(d2)
    else:
        d0 = sort_dict_by_time(d0)
        d1 = sort_dict_by_time(d1)
        d2 = sort_dict_by_time(d2)

    joined_dict = {**d0, **d1, **d2}
    return joined_dict


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

    return render_template('index.html', lang=lang, my_programm=my_programm_array[0], more=my_programm_array[1],
                           now=now(lang, 3))


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
    if day and day.isdigit():
        for k, v in json_data.items():
            if v['tag'] == int(day):
                data[k] = v

    language = request.args.get('language')
    if language and language in allowed_lang:
        for k, v in json_data.items():
            for l in v['lang']:
                if l.lower() == language.lower():
                    data[k] = v

    section = request.args.get('section')
    if section and bool(re.match('^[a-zA-Z0-9_]+$', section)):
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
                if v['type'] == 1:
                    data[k] = v
                elif v['titel-de'].lower().startswith('podium'):
                    data[k] = v

            elif section.lower() == 'workshops':
                if 'workshop' in v['titel-de'].lower() or 'workshop' in v['untertitel-de'].lower() or 'workshop' in v['content-de'].lower():
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

    day = -1

    if date == '2024-06-07':
        day = 0
    elif date == '2024-06-08':
        day = 1
    elif date == '2024-06-09':
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
    else:
        f = open('static/data/allowed_chars.txt', 'r')
        allowed_chars = f.read()
        f.close()
        if not bool(re.match(allowed_chars, search_for)):
            print('not allowed chars in search for value')
            return {}

    data = get_json()
    search_data = {}
    for k, v in data.items():
        if day and day.isdigit() and v['tag'] != int(day):
            continue
        if section and bool(re.match('^[a-zA-Z0-9_]+$', section)) and not section.lower() in v[
            'content-' + lang].lower():
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



@app.route('/ics/<int:event_id>')
def download_ics(event_id):
    lang = check_lang()
    event_point = get_element(event_id)

    # Initialize the date and time
    cet = pytz.timezone('CET')
    date_and_time = datetime(year=2024, month=6, day=1)
    date_and_time = cet.localize(date_and_time)
    if event_point['tag'] == 0:
        date_and_time = date_and_time.replace(day=7)
    elif event_point['tag'] == 1:
        date_and_time = date_and_time.replace(day=8)
    elif event_point['tag'] == 2:
        date_and_time = date_and_time.replace(day=9)

    # Split the time into begin and end parts
    time_split = event_point['zeit'].split('und')[0].split('-')
    begin_time = time_split[0].split('.')
    end_time = time_split[1].split('.') if len(time_split) > 1 else [int(begin_time[0]) + 1, begin_time[1] if len(begin_time) > 1 else 0]

    # Create a naive datetime object for begin time
    date_and_time_begin = date_and_time.replace(
        hour=int(begin_time[0]),
        minute=int(begin_time[1] if len(begin_time) > 1 else 0)
    )

    # Create a naive datetime object for end time
    date_and_time_end = date_and_time.replace(
        hour=int(end_time[0]),
        minute=int(end_time[1] if len(end_time) > 1 else 0)
    )

    # Format the begin and end times
    event_begin = date_and_time_begin.strftime('%Y-%m-%d %H:%M:%S')
    event_begin_offset = date_and_time_begin.strftime('%z')
    event_begin = f"{event_begin}{event_begin_offset[:3]}:{event_begin_offset[3:]}"

    event_end = date_and_time_end.strftime('%Y-%m-%d %H:%M:%S')
    event_end_offset = date_and_time_end.strftime('%z')
    event_end = f"{event_end}{event_end_offset[:3]}:{event_end_offset[3:]}"

    # Create the ICS file content
    cal = Calendar()
    event = Event()
    event.name = event_point['titel-' + lang]
    event.description = (event_point['untertitel-' + lang] + '\n') if event_point['untertitel-' + lang] else ''
    event.description += event_point['content-' + lang]
    event.begin = event_begin
    event.end = event_end
    event.location = event_point['location-' + lang]['name']
    cal.events.add(event)
    ics_file = io.BytesIO()
    ics_file.write(cal.serialize().encode('utf-8'))
    ics_file.seek(0)

    # Send the ICS file as a response
    return send_file(
        ics_file,
        as_attachment=True,
        download_name=f'{event_point["titel-" + lang]}.ics',
        mimetype='text/calendar'
    )


@app.route('/robots.txt')
@app.route('/sitemap.xml')
def robots():
    return send_from_directory(app.static_folder, request.path[1:])


@app.route('/favicon.ico')
@app.route('/apple-touch-icon.png')
def icon():
    return send_from_directory(app.static_folder, 'img/icon/' + request.path[1:])


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

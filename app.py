from flask import Flask, render_template, request, redirect, url_for, flash
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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/programm/<int:point>')
def programm_point(point):

    if point:
        return render_template(f'programm_point.html', section=get_element(point))
    return redirect(url_for('programm'))

@app.route('/section/<section>')
def programm_section(section):
    if section:
        return render_template(f'programm_section.html', section=section)
    return redirect(url_for('programm'))


@app.route('/programm')
@app.route('/section')
def programm():
    return render_template('programm.html')

@app.route('/my')
def my_programm():
    return render_template('my_programm.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
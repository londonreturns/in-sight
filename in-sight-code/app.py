from flask import Flask, render_template

app = Flask(__name__)

@app.route('/index')
@app.route('/')
def home():
    currentPage = "homepage"
    return render_template('index.html', currentPage=currentPage)

@app.route('/howItWorks')
def how_it_works():
    currentPage = "howitworks"
    return render_template('howItWorks.html', currentPage=currentPage)


if __name__ == '__main__':
    app.run(debug=True)
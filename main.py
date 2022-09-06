from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, HiddenField, SubmitField
from wtforms.validators import DataRequired
import requests


MOVIE_DB_API = '04816f39c174426d7aadb423539a2fa8'
MOVIE_DB_AUTH = 'eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIwNDgxNmYzOWMxNzQ0MjZkN2FhZGI0MjM1MzlhMmZhOCIsInN1YiI6IjYzMGY3MzYyN2ZjYWIzMDA3ZmJkODNmOSIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.RddWLxVlpO3DW72POTGhGNVEjNE_O-A_XiX9djhEiv4'
MOVIE_DB_URL = 'https://api.themoviedb.org/3'
MOVIE_DB_IMG_URL = 'https://www.themoviedb.org/t/p/original'


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
##CREATE DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
# Optional: But it will silence the deprecation warning in the console.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

Bootstrap(app)
db = SQLAlchemy(app)


class MovieCollection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    image_url = db.Column(db.String(250), nullable=False)


db.create_all()


class EditForm(FlaskForm):
    rating = FloatField(label='Your Rating out of 10 e.g. 7.5', validators=[DataRequired()])
    review = StringField(label="Your Review", validators=[DataRequired()])
    submit = SubmitField(label='Done')


class AddForm(FlaskForm):
    title = StringField(label='Movie Title', validators=[DataRequired()])
    submit = SubmitField(label='Add Movie')


@app.route("/")
def home():
    rank = 0
    ordered_movies = MovieCollection.query.order_by(MovieCollection.rating.desc()).all()
    for movie in ordered_movies:
        rank += 1
        movie.ranking = rank
        db.session.commit()
    return render_template("index.html", movies=ordered_movies)


@app.route('/edit', methods=['POST', 'GET'])
def edit():
    movie_id = request.args.get('movie_id', type=int)
    movie_to_edit = MovieCollection.query.get(movie_id)
    form = EditForm()
    if form.validate_on_submit():
        movie_to_edit.rating = float(form.rating.data)
        movie_to_edit.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('edit.html', movie_to_edit=movie_to_edit, form=form)


@app.route('/delete')
def delete():
    movie_id = request.args.get('movie_id', type=int)
    selected_movie = MovieCollection.query.get(movie_id)
    db.session.delete(selected_movie)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddForm()
    if form.validate_on_submit():
        movie_name = form.title.data
        parameters = {
            'api_key': MOVIE_DB_API,
            'Authorization': MOVIE_DB_AUTH,
            'query': movie_name,
        }
        response = requests.get(url=f'{MOVIE_DB_URL}/search/movie', params=parameters)
        movie_list = response.json()['results']
        return render_template('select.html', movie_list=movie_list)

    return render_template('add.html', form=form)


@app.route('/add_movie')
def add_movie():
    movie_id = request.args.get('movie_id', type=int)
    if movie_id:
        parameters = {
            'api_key': MOVIE_DB_API,
            'Authorization': MOVIE_DB_AUTH,
            'language': 'en-US',
        }
        detail_response = requests.get(url=f"{MOVIE_DB_URL}/movie/{movie_id}", params=parameters)
        movie_detail = detail_response.json()
        new_movie = MovieCollection(title=movie_detail['original_title'],
                                    year=movie_detail['release_date'].split('-')[0],
                                    description=movie_detail['overview'],
                                    rating=0,
                                    ranking=0,
                                    review='',
                                    image_url=f"{MOVIE_DB_IMG_URL}/{movie_detail['poster_path']}")
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', movie_id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)

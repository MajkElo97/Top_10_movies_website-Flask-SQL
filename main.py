from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

MOVIES_API_KEY = "your api key"
MOVIES_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_INFO_URL = "https://api.themoviedb.org/3/movie/"
MOVIE_IMAGE_URL = 'https://www.themoviedb.org/t/p/w600_and_h900_bestv2'

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    # Optional: this will allow each book object to be identified by its title when printed.
    def __repr__(self):
        return f'<Book {self.title}>'


class EditForm(FlaskForm):
    rating = StringField(label='Your Rating Out of 10 e.g. 7.5')
    review = StringField(label='Your Review')
    submit = SubmitField(label="Done")


class AddForm(FlaskForm):
    title = StringField(label='title', validators=[DataRequired()])
    submit = SubmitField(label="Add a movie")


#### manual adding movie and creating table ####
# with app.app_context():
#     db.create_all()
#     new_movie = Movie(
#         title="Phone Booooth",
#         year=2002,
#         description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#         rating=7.3,
#         ranking=9,
#         review="My favourite character was the caller.",
#         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
#     )
#     db.session.add(new_movie)
#     db.session.commit()

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating)
    number_of_movies = 0
    for movie in all_movies:
        number_of_movies += 1
    for movie in all_movies:
        movie.ranking = number_of_movies
        number_of_movies -= 1
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    edit_form = EditForm()
    if edit_form.validate_on_submit():
        movie_id = request.args.get('id')
        movie_to_update = Movie.query.get(movie_id)
        movie_to_update.rating = edit_form.rating.data
        movie_to_update.review = edit_form.review.data
        db.session.commit()
        return redirect(url_for('home'))

    movie_id = request.args.get('id')
    return render_template("edit.html", movie=Movie.query.get(movie_id), form=edit_form)


@app.route("/delete", methods=["GET", "POST"])
def delete():
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    if add_form.validate_on_submit():
        title = add_form.title.data

        movies_parameters = {
            "api_key": MOVIES_API_KEY,
            "query": title,
        }
        response_movies = requests.get(url=MOVIES_URL, params=movies_parameters)
        response_movies.raise_for_status()
        movies_data = response_movies.json()["results"]
        movie_list = []
        for movie in movies_data:
            movie = {
                "id": movie["id"],
                "title": movie["original_title"],
                "year": movie["release_date"],
            }
            movie_list.append(movie)
        return render_template("select.html", movies=movie_list)
    return render_template("add.html", form=add_form)


@app.route("/search", methods=["GET", "POST"])
def search():
    movie_id = request.args.get('id')
    movies_parameters = {
        "api_key": MOVIES_API_KEY,
    }
    response_movies = requests.get(url=MOVIE_INFO_URL + movie_id, params=movies_parameters)
    response_movies.raise_for_status()
    movies_data = response_movies.json()

    new_movie = Movie(
        title=movies_data["title"],
        year=movies_data["release_date"].split("-")[0],
        description=movies_data["overview"],
        img_url=MOVIE_IMAGE_URL + movies_data["poster_path"]
    )
    db.session.add(new_movie)
    db.session.commit()
    movie = Movie.query.filter_by(title=movies_data["title"]).first()
    return redirect(url_for('edit', id=movie.id))


if __name__ == '__main__':
    app.run(debug=True)

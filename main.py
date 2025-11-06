from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from add_movie import NMovie
import requests

## LAST PART IS ADDING IS CONNECT
app = Flask(__name__)
app.config['SECRET_KEY'] = #Add your secret key
Bootstrap5(app)

# CREATE DB
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myfavmovie-list.db'

# Create db instance with base
db = SQLAlchemy(model_class=Base)
# Connect to the flask app
db.init_app(app)

# Needed a flask form to help render the edit page
class EditForm(FlaskForm):
    rating = StringField('Rating', validators=[DataRequired()])
    ranking = StringField('Ranking', validators=[DataRequired()])
    review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')

class addMovie(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    review: Mapped[str] = mapped_column(String(1000), nullable=False)
    img_url: Mapped[str] = mapped_column(String(1000), nullable=False)

    # Allow each book object to be identified by its title
    def __repr__(self):
        return f"<Book(title={self.title})>"

@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating.desc()))
    all_movies = result.scalars().all()
    return render_template("index.html", movies=all_movies)

@app.route("/update", methods=["POST", "GET"])
def update():
    movie_id = request.args.get("id")
    movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()

    form = EditForm()
    if form.validate_on_submit():
        movie.rating = form.rating.data
        movie.ranking = form.ranking.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))

    return render_template("edit.html", form=form, movie=movie)

@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=["POST", "GET"])
def add():
    form = addMovie()
    if form.validate_on_submit():
        title = form.title.data
        api_key = "ADD YOUR API KEY HERE"
        
        # Create an instance of NMovie (note: you need to adjust NMovie class)
        movie_searcher = NMovie(title=title)
        results = movie_searcher.searchMovie(title, api_key)
        print(results)

        # Render select.html with results
        if results:
            return render_template('select.html', results=results)

        else:
            print("No results found or an error occurred.")
    return render_template("add.html", form=form)

# Create a function to handle the selection of a movie from the search results
@app.route("/selected")
def selected():
    api_key = "SAME THING HERE AS ABOVE"
    movie_id = request.args.get("id")
    print(f"movie_id: {movie_id}")
    # After getting the selected movie, fetch the movie: poster, description, rating and release date
    base_url = "https://api.themoviedb.org/3/movie/"
    movie_url = f"{base_url}{movie_id}?api_key={api_key}"
    response = requests.get(movie_url)
    movie_data = response.json()
    title = movie_data.get("title")
    poster_path = movie_data.get("poster_path")
    description = movie_data.get("overview")
    rating = movie_data.get("vote_average")
    release_date = movie_data.get("release_date")
    # Finally add that to the movie database
    movie = Movie(
        title=movie_data.get("title"),
        year=release_date,
        description=description,
        rating=rating,
        review="",
        ranking=db.session.query(Movie).count() + 1,
        img_url=f"https://image.tmdb.org/t/p/w500/{poster_path}"
    )
    db.session.add(movie)
    db.session.commit()
    return redirect(url_for("home"))

if __name__ == '__main__':
    # Initialize database before running the app
    app.run(debug=True)
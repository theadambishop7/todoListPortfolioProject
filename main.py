from flask import Flask, render_template, url_for, redirect, request, jsonify
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, DateField
from wtforms.validators import DataRequired, InputRequired
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime
import os

app = Flask(__name__)
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "nasjdhfq982y4hniquhsdfkha8s7dyf"
db = SQLAlchemy(app)
app.app_context().push()


class Todo(db.Model):
    __tablename__ = "todos"
    id = db.Column(db.Integer, primary_key=True)
    todo_text = db.Column(db.String(250), nullable=False)
    due_date = db.Column(db.String(250))
    complete = db.Column(db.Boolean, nullable=False)


class NullableDateField(DateField):
    """Native WTForms DateField throws error for empty dates.
    Let's fix this so that we could have DateField nullable."""
    def process_formdata(self, valuelist):
        if valuelist:
            date_str = ' '.join(valuelist).strip()
            if date_str == '':
                self.data = None
                return
            try:
                self.data = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                self.data = None
                raise ValueError(self.gettext('Not a valid date value'))


class TodoForm(FlaskForm):
    todo = StringField('To-do Item', validators=[DataRequired()])
    due_date = NullableDateField('Due Date', format="%Y-%m-%d")
    submit = SubmitField('Create')


@app.route("/")
def home():
    todo_list = db.session.query(Todo).all()
    completed_exists = any(item.complete for item in todo_list)
    return render_template("index.html", todo_list=todo_list, completed_exists=completed_exists)


@app.route('/add-todo', methods=['GET', 'POST'])
def add_todo():
    form = TodoForm()
    if form.validate_on_submit():
        todo = Todo(
            todo_text=form.todo.data,
            due_date=form.due_date.data,
            complete=False
        )
        db.session.add(todo)
        db.session.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({}, 200)
        else:
            return redirect("/")

    return render_template('add-todo.html', form=form)


@app.route('/add-todo-form', methods=["GET"])
def add_todo_form():
    form = TodoForm()
    return render_template('form.html', form=form)


@app.route("/complete-item/<int:todo_item>")
def complete_item(todo_item):
    item_to_update = db.session.get(Todo, todo_item)
    item_to_update.complete = True
    db.session.commit()
    return redirect("/")


@app.route("/uncomplete-item/<int:todo_item>")
def uncomplete_item(todo_item):
    item_to_update = db.session.get(Todo, todo_item)
    item_to_update.complete = False
    db.session.commit()
    return redirect("/")


@app.route("/edit-todo/<int:todo_item>", methods=["GET", "POST"])
def edit_todo(todo_item):
    todo = db.session.get(Todo, todo_item)
    todo.due_date = datetime.strptime(todo.due_date, "%Y-%m-%d")
    edit_form = TodoForm(
        todo=todo.todo_text,
        due_date=todo.due_date,
    )
    if edit_form.validate_on_submit():
        todo.todo_text = edit_form.todo.data
        todo.due_date = edit_form.due_date.data
        db.session.commit()
        return redirect("/")

    return render_template("add_todo.html", form=edit_form)


@app.route("/delete-completed", methods=["GET", "POST"])
def delete_completed():
    todo_list = db.session.query(Todo).all()
    for todo in todo_list:
        if todo.complete:
            db.session.delete(todo)
    db.session.commit()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
import flask
import models
import forms
from datetime import datetime

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )
        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)
        note.tags.append(tag)

    note.created_date = datetime.now()
    note.updated_date = datetime.now()
    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/notes/edit/<note_id>", methods=["GET", "POST"])
def note_edit(note_id):
    db = models.db
    note = models.Note.query.get(note_id)
    form = forms.NoteForm(obj=note)
    thistag = ""
    for tag in note.tags:
        thistag += tag.name + ","

    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data
        note_tags = []
        for tag_name in form.tags.data:
            if tag_name != '':
                tag = (
                    db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
                    .scalars()
                    .first()
                )
                if not tag:
                    tag = models.Tag(name=tag_name)
                    db.session.add(tag)
                note_tags.append(tag)

        note.tags = note_tags
        note.updated_date = datetime.now()
        db.session.commit()
        
        return flask.redirect(flask.url_for("index"))
    return flask.render_template("notes-edit.html", form=form, note=note, tagList=thistag)


@app.route("/tags/delete/<tag_name>", methods=["GET", "POST"])
def tag_delete(tag_name):
    db = models.db
    tag = models.Tag.query.filter_by(name=tag_name).first()
    if tag:
        notes = db.session.execute(
            db.select(models.Note).where(models.Note.tags.any(name=tag_name))
        ).scalars()
        for note in notes:
            note.tags.remove(tag)
        db.session.delete(tag)
        db.session.commit()
    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


@app.route("/notes/delete/<int:note_id>", methods=["POST"])
def notes_delete(note_id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalars().first()

    if not note:
        flask.abort(404, description="Note not found")

    db.session.delete(note)
    db.session.commit()
    return flask.redirect(flask.url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)

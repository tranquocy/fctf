from flask import Blueprint, render_template, flash, redirect, url_for
from flask_login import login_required


from app import db
from app.hint.models import Hint
from app.hint.forms import CreateHintForm, HintForm
from app.common.utils import admin_required

hint_module = Blueprint('hint', __name__)


@hint_module.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_hint():
    form = CreateHintForm()
    if form.validate_on_submit():
        new_hint = Hint(form.description.data, form.is_open.data, form.task.data)
        db.session.add(new_hint)
        db.session.commit()
        flash('Hint created successfully.', category='success')
        return redirect(url_for('task.show_task', task_id=form.task.data.id))
    return render_template('hint/create_hint.html', form=form)


@hint_module.route('/<int:hint_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_hint(hint_id=None):
    model = Hint.query.get_or_404(hint_id)
    form = HintForm(obj=model)

    if form.validate_on_submit():
        form.populate_obj(model)
        db.session.add(model)
        db.session.commit()
        flash('Hint updated', category='success')
        return redirect(url_for('task.show_task', task_id=model.task.id))
    return render_template('hint/edit_hint.html', task=model, form=form)

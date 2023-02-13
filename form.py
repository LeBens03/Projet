import os
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectMultipleField, widgets, TextAreaField

basedir = os.path.abspath(os.path.dirname(__file__))
data_file = os.path.join(basedir, 'static/txt/etiquettes.txt')

#Je crée une widget personnalisée pour pouvoir selectionner mutiple options dans mon Select

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

#Je crée un Form pour générer des questions
    
class nouvelleQuestion(FlaskForm):
    enonce = TextAreaField('Enoncé')
    proposition = StringField('Proposition')
    etiquettes = SelectMultipleField('Etiquettes', choices=[])
    etiquette = StringField('Etiquette')
    submit = SubmitField('Ajouter Question')







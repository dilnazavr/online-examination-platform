from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, NumberRange

class TestForm(FlaskForm):
    title = StringField('Тест атауы', validators=[DataRequired()])
    description = TextAreaField('Сипаттама', validators=[DataRequired()])
    time_limit = IntegerField('Уақыт шегі (мин)', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Қосу')


class QuestionForm(FlaskForm):
    question_text = TextAreaField('Вопрос', validators=[DataRequired()])
    answer_a = StringField('Вариант A', validators=[DataRequired()])
    answer_b = StringField('Вариант B', validators=[DataRequired()])
    answer_c = StringField('Вариант C', validators=[DataRequired()])
    answer_d = StringField('Вариант D', validators=[DataRequired()])
    correct_answer = SelectField('Правильный ответ', choices=[('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')], validators=[DataRequired()])



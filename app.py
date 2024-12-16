import os
from flask import Flask, request, redirect, url_for, render_template, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import psycopg2
import logging
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy.orm import relationship
from datetime import datetime
from forms import TestForm, QuestionForm



UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  

app = Flask(__name__)
app.secret_key = '22112005'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:22112005@localhost/exam_platform'
app.config['SECRET_KEY'] = '22112005'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SESSION_PROTECTION'] = 'strong'
app.config['SESSION_COOKIE_NAME'] = 'session'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



DATABASE_URL = "postgresql://postgres:22112005@localhost/exam_platform"
conn = "postgresql://postgres:22112005@localhost/exam_platform"


ALLOWED_EXTENSIONS = {'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS





class TestGroup(db.Model):
    __tablename__ = 'test_groups'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    test = db.relationship('Test', backref='test_groups')
    group = db.relationship('Group', backref='test_groups')



class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False) 
    question_text = db.Column(db.Text, nullable=False)  
    correct_answer = db.Column(db.String(1), nullable=False)  
    answers = db.relationship('Answer', back_populates='question', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Question {self.id}: {self.question_text}>'

class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)

    question = db.relationship('Question', back_populates='answers')

    def __repr__(self):
        return f'<Answer {self.id}: {self.answer_text}>'


class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False) 
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)  

    student = db.relationship('Student', back_populates='results')  

    def __repr__(self):
        return f'<Result {self.id}: Student {self.student_id}, Test {self.test_id}, Score {self.score}>'

class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    iin = db.Column(db.String(12), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    group = db.relationship('Group', back_populates='students')
    results = db.relationship('Result', back_populates='student', cascade='all, delete-orphan')  
@staticmethod
def get_student_by_iin(iin):
    return Student.query.filter_by(iin=iin).first()
        


class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    students = db.relationship('Student', back_populates='group', cascade='all, delete-orphan')


class Test(db.Model):
    __tablename__ = 'tests'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.teacher_id'), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)

    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_groups(self):
        return [tg.group for tg in self.test_groups]

class Subject(db.Model):
    __tablename__ = 'subjects' 
    id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)


class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role  


class Teacher(db.Model, UserMixin):
    __tablename__ = 'teachers'

    teacher_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100)) 
    surname = db.Column(db.String(100)) 
    email = db.Column(db.String(255)) 

    def get_id(self):
        return str(self.teacher_id)










@login_manager.user_loader
def load_user(user_id):
    teacher = db.session.get(Teacher, int(user_id)) 
    if teacher:
        return teacher
    return None

@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/student_iin', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        iin = request.form['iin']
        student = Student.query.filter_by(iin=iin).first()
        if student:
            session['student_id'] = student.id
            return redirect(url_for('choose_test', student_id=student.id))
        else:
            flash("Студент с таким ИИН не найден", 'error')

    return render_template('student_iin.html')



@app.route('/login', methods=['POST'])
def login():
    student = Student.query.filter_by(iin=request.form['iin']).first()
    if student:
        session['student_id'] = student.id  
        return redirect(url_for('submit_test', test_id=1))
    return "Неверный ИИН", 401


@app.route('/add_test', methods=['GET', 'POST'])
@login_required
def add_test():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description', '')
        status = request.form.get('status', 'active')
        time_limit = request.form.get('time_limit', 0)
        group_ids = request.form.getlist('groups') 

        if not title or not time_limit or not group_ids:
            flash('Все обязательные поля должны быть заполнены!', 'error')
            return redirect(url_for('add_test'))

        try:
            test = Test(
                title=title,
                teacher_id=current_user.teacher_id,
                description=description,
                status=status,
                time_limit=int(time_limit)
            )
            db.session.add(test)
            db.session.flush()

            for group_id in group_ids:
                test_group = TestGroup(test_id=test.id, group_id=int(group_id))
                db.session.add(test_group)

            db.session.commit()
            flash('Тест сәтті қосылды!', 'success')
            return redirect(url_for('tests_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при добавлении теста: {e}', 'error')

    groups = Group.query.all()
    return render_template('add_test.html', groups=groups)

@app.route('/tests')
def list_tests():
    tests = Test.query.all()
    return render_template('tests.html', tests=tests)

@app.route('/view_tests')
def view_tests():
    tests = Test.query.all()
    return render_template('view_tests.html', tests=tests)


@app.route('/edit_test/<int:test_id>', methods=['GET', 'POST'])
def edit_test(test_id):
    test = Test.query.get_or_404(test_id)
    if request.method == 'POST':
        test.title = request.form['title']
        test.description = request.form.get('description', '')
        test.time_limit = int(request.form['time_limit'])
        test.status = request.form['status']

        db.session.commit()
        return redirect(url_for('view_tests'))
    return render_template('edit_test.html', test=test)



def save_test_result(student_id, test_id, score):
    try:
        if student_id is None:
            raise ValueError("Student ID is missing from session.")
        
        result = Result(student_id=student_id, test_id=test_id, score=score, completed_at=datetime.now())
        db.session.add(result)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Ошибка при сохранении результата: {e}", 'error')





@app.route('/upload_questions/<int:test_id>', methods=['GET', 'POST'])
@login_required
def upload_questions(test_id):
    if request.method == 'POST':
        file = request.files.get('file')
        if not file:
            flash('Пожалуйста, загрузите файл!', 'error')
            return redirect(url_for('upload_questions', test_id=test_id))

        try:
            lines = file.read().decode('utf-8').splitlines()
            if len(lines) < 6:  
                flash('Файл должен содержать минимум один вопрос с 4 вариантами ответов и правильным ответом.', 'error')
                return redirect(url_for('upload_questions', test_id=test_id))

            current_question = None
            answers = []
            correct_answer = None

            for i, line in enumerate(lines):
                line = line.strip()
                if i % 6 == 0:
                    current_question = line
                elif 1 <= i % 6 <= 4:
                    answers.append(line)
                elif i % 6 == 5:
                    correct_answer = line.lower()

                    question = Question(test_id=test_id, question_text=current_question, correct_answer=correct_answer)
                    db.session.add(question)
                    db.session.flush()  

                    for j, answer_text in enumerate(answers):
                        is_correct = correct_answer == chr(97 + j)  # a, b, c, d
                        answer = Answer(question_id=question.id, answer_text=answer_text, is_correct=is_correct)
                        db.session.add(answer)

                    answers = []
                    correct_answer = None

            db.session.commit()
            flash('Сұрақтар сәтті қосылды', 'success')
            return redirect(url_for('tests_list'))

        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при обработке файла: {e}', 'error')
            return redirect(url_for('upload_questions', test_id=test_id))

    return render_template('upload_questions.html', test_id=test_id)

@app.route('/tests_list')
@login_required
def tests_list():
    try:
        teacher_id = current_user.teacher_id
        tests = Test.query.filter_by(teacher_id=teacher_id).all()
        return render_template('tests_list.html', tests=tests)
    except Exception as e:
        flash(f'Ошибка при загрузке списка тестов: {e}', 'error')
        return redirect(url_for('add_test'))


@app.route('/add-question-manual/<int:test_id>', methods=['GET', 'POST'])
@login_required
def add_question_manual(test_id):
    test = Test.query.get_or_404(test_id)

    if request.method == 'POST':
        question_count = len(request.form) // 6  
        
        for i in range(1, question_count + 1):
            question_text = request.form.get(f'question_text_{i}')
            answer_a = request.form.get(f'answer_a_{i}')
            answer_b = request.form.get(f'answer_b_{i}')
            answer_c = request.form.get(f'answer_c_{i}')
            answer_d = request.form.get(f'answer_d_{i}')
            correct_answer = request.form.get(f'correct_answer_{i}')

            if not all([question_text, answer_a, answer_b, answer_c, answer_d, correct_answer]):
                flash('Барлық өрістерді толтырыңыз!', 'error')
                return render_template('add_question_manual.html', test_id=test_id, test=test)

            if correct_answer not in ['a', 'b', 'c', 'd']:
                flash('Дұрыс жауап "a", "b", "c" немесе "d" болуы керек.', 'error')
                return render_template('add_question_manual.html', test_id=test_id, test=test)

            new_question = Question(
                test_id=test_id,
                question_text=question_text,
                correct_answer=correct_answer
            )
            db.session.add(new_question)
            db.session.commit()

            answers = [answer_a, answer_b, answer_c, answer_d]
            for i, answer_text in enumerate(answers):
                is_correct = (chr(97 + i) == correct_answer) 
                new_answer = Answer(
                    question_id=new_question.id,
                    answer_text=answer_text,
                    is_correct=is_correct
                )
                db.session.add(new_answer)

            db.session.commit()

        flash('Сұрақ(тар) сәтті қосылды!', 'success')
        return redirect(url_for('tests_list')) 

    return render_template('add_question_manual.html', test_id=test_id, test=test)



@app.route('/student', methods=['GET', 'POST'])
def student_login_page():
    if request.method == 'POST':
        iin = request.form['iin']
        student = Student.query.filter_by(iin=iin).first()
        if student:
            session['student_id'] = student.id
            return redirect(url_for('choose_test', student_id=student.id))
        else:
            flash("Студент с таким ИИН не найден", 'error')
    return render_template('student_iin.html')



def get_student_test_result(student_id, test_id):
    return Result.query.filter_by(student_id=student_id, test_id=test_id).first()

def save_test_result(student_id, test_id, score):
    result = Result.query.filter_by(student_id=student_id, test_id=test_id).first()
    if not result:
        result = Result(student_id=student_id, test_id=test_id, score=score, completed=True)
        db.session.add(result)
    else:
        result.score = score
        result.completed = True
    db.session.commit()


@app.route('/choose_test/<int:student_id>')
def choose_test(student_id):
    student = Student.query.get(student_id)
    if not student:
        return "Студент не найден", 404

    group_id = student.group_id
    if not group_id:
        return "Студент не привязан к группе", 400

    available_tests = (
        db.session.query(Test)
        .join(TestGroup, Test.id == TestGroup.test_id)
        .filter(TestGroup.group_id == group_id)
        .all()
    )

    return render_template('choose_test.html', tests=available_tests, student=student, get_student_test_result=get_student_test_result)

@app.route('/start_test/<int:test_id>', methods=['GET', 'POST'])
def start_test(test_id):
    student_id = session.get('student_id')
    if not student_id:
        return "Вы не авторизованы. Пожалуйста, войдите в систему.", 403

    return redirect(url_for('take_test', student_id=student_id, test_id=test_id))


@app.route('/finish_test/<int:test_id>', methods=['POST'])
def finish_test(test_id):
    student_id = session.get('student_id')
    if not student_id:
        return "Вы не авторизованы.", 403

    result = Result.query.filter_by(student_id=student_id, test_id=test_id).first()
    if result:
        result.completed = True
        db.session.commit()
    else:
        return "Результаты не найдены.", 404

    return redirect(url_for('test_results', test_id=test_id))




def process_test_file(file_path, test_name, group_id):
    new_test = Test(name=test_name)
    db.session.add(new_test)
    db.session.commit()

    test_group = TestGroup(test_id=new_test.id, group_id=group_id)
    db.session.add(test_group)

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split(';')
            if len(parts) == 6:  
                question_text = parts[0]
                answers = parts[1:5]
                correct_answer = parts[5]

                new_question = Question(
                    test_id=new_test.id,
                    question_text=question_text,
                    correct_answer=correct_answer.lower()  # a, b, c, d
                )
                db.session.add(new_question)
                db.session.commit()

                for idx, answer_text in enumerate(answers, start=0):
                    is_correct = (chr(97 + idx) == correct_answer.lower())  # 'a', 'b', 'c', 'd'
                    new_answer = Answer(
                        question_id=new_question.id,
                        answer_text=answer_text,
                        is_correct=is_correct
                    )
                    db.session.add(new_answer)
    db.session.commit()
    return new_test.id
def calculate_score(user_answers, correct_answers):
    score = 0
    for user, correct in zip(user_answers, correct_answers):
        if user == correct:
            score += 1
    return score


@app.route('/student/<int:student_id>/tests/<int:test_id>', methods=['GET', 'POST'])
def take_test(student_id, test_id):
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()

    if request.method == 'POST':
        # Проверяем, прошел ли студент этот тест
        existing_result = Result.query.filter_by(student_id=student_id, test_id=test_id).first()
        if existing_result:
            flash("Вы уже прошли этот тест.")
            return redirect(url_for('choose_test', student_id=student_id))

        # Получаем ответы студента
        answers = request.form
        correct_answers = {question.id: question.correct_answer.strip().lower() for question in questions}

        # Инициализируем счетчик правильных ответов
        score = 0
        
        for question in questions:
            correct_answer = next((ans.answer_text for ans in question.answers if ans.is_correct), None)
            user_answer = answers.get(f'question_{question.id}', '').strip()

            print(f"Вопрос {question.id}: Ответ студента: {user_answer}, Правильный ответ: {correct_answer}")

            if correct_answer and user_answer.lower() == correct_answer.lower():
                score += 1

        # Сохраняем результаты
        result = Result(student_id=student_id, test_id=test_id, score=score, completed=True)
        db.session.add(result)
        db.session.commit()

        # Сохраняем, что студент завершил тест
        session[f'test_completed_{test_id}'] = True

        # Перенаправляем на страницу с результатами
        return redirect(url_for('test_results', test_id=test_id))

    return render_template(
        'take_test.html',
        test=test,
        questions=questions,
        time_limit=test.time_limit,
        student_id=student_id,
        test_id=test_id
    )


@app.route('/test_results/<int:test_id>')
def test_results(test_id):
    student_id = session.get('student_id')
    if not student_id:
        return "Вы не авторизованы.", 403

    # Ищем результат для текущего студента и теста
    result = Result.query.filter_by(student_id=student_id, test_id=test_id).first()
    if result:
        test = Test.query.get_or_404(test_id)
        questions_count = Question.query.filter_by(test_id=test_id).count()
        return render_template(
            'test_results.html',
            score=result.score,
            total=questions_count,
            test=test
        )
    else:
        flash("Результаты не найдены.")
        return redirect(url_for('choose_test', student_id=student_id))


@app.route('/teacher', methods=['GET', 'POST'])
def teacher_iin():
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        print(f"Попытка входа с логином: {username} и паролем: {password}")
        if username == 'admin' and password == '22112005':
            login_user(User("1", "admin", "admin"))
            print("Вход выполнен успешно как администратор!")
            return redirect(url_for('admin_dashboard'))
        teacher = Teacher.query.filter_by(username = username).first()  
        if teacher and teacher.password:
            login_user(teacher) 
        return redirect(url_for('teacher_dashboard'))
    return render_template('teacher_iin.html')

@app.route('/teacher_dashboard')
def teacher_dashboard():
    return render_template('teacher_dashboard.html')


@app.route('/admin')
@login_required
def admin_dashboard():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teachers")
        teachers = cursor.fetchall()
    except Exception as e:
        flash(f"Ошибка при получении данных: {str(e)}", "error")
        teachers = []
    finally:
        cursor.close()
        conn.close()

    return render_template('admin_dashboard.html', teachers=teachers)

@app.route('/test_page/<int:test_id>')
def test_page(test_id):
    test = Test.query.get_or_404(test_id)
    return render_template('test_page.html', test=test)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('welcome'))

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/tprofile')
@login_required
def tprofile():
    """Профиль учителя"""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT name, surname, email FROM teachers WHERE teacher_id = %s", (current_user.get_id(),))
        teacher_data = cursor.fetchone()
        teacher_info = {'name': teacher_data[0], 'surname': teacher_data[1], 'email': teacher_data[2]} if teacher_data else None
    except Exception as e:
        flash(f"Ошибка при получении данных: {str(e)}", "error")
        teacher_info = None
    finally:
        cursor.close()
        conn.close()

    return render_template('tprofile.html', teacher=teacher_info)
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE teachers SET name = %s, surname = %s, email = %s WHERE teacher_id = %s",
                (name, surname, email, current_user.get_id())
            )
            conn.commit()
            flash("Профиль успешно обновлен!", "success")
        except Exception as e:
            flash(f"Ошибка при обновлении профиля: {str(e)}", "error")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('tprofile'))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT name, surname, email FROM teachers WHERE teacher_id = %s", (current_user.get_id(),))
        teacher_data = cursor.fetchone()
    except Exception as e:
        flash(f"Ошибка при получении данных: {str(e)}", "error")
        teacher_data = None
    finally:
        cursor.close()
        conn.close()

    return render_template('edit_profile.html', teacher=teacher_data)


@app.route('/add_teacher', methods=['GET', 'POST'])
@login_required
def add_teacher():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash("Логин және құпиясөз міндетті түрде толтырылуы керек!", "warning")
            return redirect(url_for('add_teacher'))

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO teachers (username, password) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()

            flash("Мұғалім сәтті қосылды!", "success")
        except Exception as e:
            flash(f"Мұғалімді қосу кезінде қате: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('admin_dashboard'))

    return render_template('add_teacher.html')



@app.route('/add_teachers_file', methods=['GET', 'POST'])
@login_required
def add_teachers_file():
    if request.method == 'POST':
        if 'teacherFile' not in request.files:
            flash("Файл не выбран!", "error")
            return redirect(request.url)

        file = request.files['teacherFile']

        if file.filename == '':
            flash("Файл не выбран!", "error")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join("uploads", filename)

            os.makedirs("uploads", exist_ok=True)
            file.save(filepath)

            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if len(lines) % 2 != 0:
                flash("Некорректный формат файла. Каждому логину должен соответствовать пароль.", "error")
                return redirect(request.url)

            try:
                conn = psycopg2.connect(DATABASE_URL)
                cursor = conn.cursor()
                for i in range(0, len(lines), 2):
                    username = lines[i].strip()
                    password = lines[i + 1].strip()

                    cursor.execute(
                        "INSERT INTO teachers (username, password) VALUES (%s, %s)",
                        (username, password)
                    )

                conn.commit()
                flash("Учителя успешно добавлены!", "success")

            except Exception as e:
                flash(f"Ошибка при добавлении учителей: {str(e)}", "error")

            finally:
                cursor.close()
                conn.close()

            os.remove(filepath)
            return redirect(url_for('admin_dashboard'))

    return render_template('add_teacher_file.html')
@app.route('/add_students_file', methods=['GET', 'POST'])
@login_required
def add_students_file():
    if request.method == 'POST':
        file = request.files.get('stud')

        if not file:
            flash("Файл таңдалмады.", "error")
            return redirect(url_for('add_students_file'))

        try:
            lines = file.read().decode('utf-8').splitlines()
            for line in lines:
                data = line.split(',')
                if len(data) != 4:
                    continue  

                iin, first_name, last_name, group_name = [x.strip() for x in data]
                group = Group.query.filter_by(name=group_name).first()
                if not group:
                    group = Group(name=group_name)
                    db.session.add(group)
                    db.session.flush() 
                student = Student(
                    iin=iin,
                    first_name=first_name,
                    last_name=last_name,
                    group_id=group.id
                )
                db.session.add(student)

            db.session.commit()
            flash("Студенттер сәтті жүктелді!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Қате: {str(e)}", "error")
            return redirect(url_for('students_list'))

    return render_template('add_students_file.html')
           

@app.route('/delete_teacher', methods=['GET', 'POST'])
@login_required
def delete_teacher():
    if request.method == 'POST':
        teacher_login = request.form['teacher_login']

        try:
            conn = psycopg2.connect(DATABASE_URL)
            cursor = conn.cursor()

            cursor.execute("DELETE FROM teachers WHERE username = %s", (teacher_login,))
            conn.commit()

            if cursor.rowcount == 0:
                flash(f"Логин {teacher_login} табылмады!", "warning")
            else:
                flash(f"Мұғалім {teacher_login} сәтті өшірілді!", "success")
        except Exception as e:
            flash(f"Мұғалімді өшіру кезінде қате: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()

        return redirect(url_for('delete_teacher'))

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM teachers")
        teachers = cursor.fetchall()
        teachers = [teacher[0] for teacher in teachers] 
        print(teachers)  
    except Exception as e:
        flash(f"Мұғалімдерді жүктеу кезінде қате: {str(e)}", "danger")
        teachers = []
    finally:
        cursor.close()
        conn.close()

    return render_template('delete_teacher.html', teachers=teachers)


@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        try:
            iin = request.form['iin']
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            group_name = request.form['group_name']  
            
        
            group = Group.query.filter_by(name=group_name).first()
            if not group:
                group = Group(name=group_name)
                db.session.add(group)
                db.session.commit()  
            student = Student(iin=iin, first_name=first_name, last_name=last_name, group_id=group.id)
            db.session.add(student)
            db.session.commit()

            flash("Студент успешно добавлен!", "success")
            return redirect(url_for('view_students'))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка: {str(e)}", "error")
            return redirect(url_for('add_student'))

    groups = Group.query.all() 
    return render_template('add_student.html', groups=groups)



@app.route('/exam_results')
def exam_results():
    return render_template('exam_results.html')

@app.route('/students_list', methods=['GET', 'POST'])
@login_required
def students_list():
    search_query = request.args.get('search', '') 
    search_field = request.args.get('field', 'all') 

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        if search_query:
            if search_field == 'iin':
                cursor.execute("""
                    SELECT s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.iin ILIKE %s
                """, (f"%{search_query}%",))
            elif search_field == 'first_name':
                cursor.execute("""
                    SELECT s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.first_name ILIKE %s
                """, (f"%{search_query}%",))
            elif search_field == 'last_name':
                cursor.execute("""
                    SELECT s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.last_name ILIKE %s
                """, (f"%{search_query}%",))
            elif search_field == 'group_name':
                cursor.execute("""
                    SELECT s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE g.name ILIKE %s
                """, (f"%{search_query}%",))
            else:  
                cursor.execute("""
                    SELECT s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.iin ILIKE %s OR s.first_name ILIKE %s OR s.last_name ILIKE %s OR g.name ILIKE %s
                """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("""
                SELECT s.iin, s.first_name, s.last_name, g.name AS group_name 
                FROM students s
                LEFT JOIN groups g ON s.group_id = g.id
            """)

        students = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('students_list.html', students=students, search_query=search_query, search_field=search_field)

    except Exception as e:
        flash(f"Ошибка при получении студентов: {e}", 'error')
        return redirect(url_for('tprofile'))



@app.route('/manage_students', methods=['GET', 'POST'])
@login_required
def manage_students():
    search_query = request.args.get('search', '').strip()
    search_field = request.args.get('field', 'all')

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        if not search_query:
            cursor.execute("""
                SELECT s.id, s.iin, s.first_name, s.last_name, g.name AS group_name 
                FROM students s
                LEFT JOIN groups g ON s.group_id = g.id
            """)
        else:
            if search_field == 'iin':
                cursor.execute("""
                    SELECT s.id, s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.iin ILIKE %s
                """, (f"%{search_query}%",))
            elif search_field == 'first_name':
                cursor.execute("""
                    SELECT s.id, s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.first_name ILIKE %s
                """, (f"%{search_query}%",))
            elif search_field == 'last_name':
                cursor.execute("""
                    SELECT s.id, s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.last_name ILIKE %s
                """, (f"%{search_query}%",))
            elif search_field == 'group_name':
                cursor.execute("""
                    SELECT s.id, s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE g.name ILIKE %s
                """, (f"%{search_query}%",))
            else:
                cursor.execute("""
                    SELECT s.id, s.iin, s.first_name, s.last_name, g.name AS group_name 
                    FROM students s
                    LEFT JOIN groups g ON s.group_id = g.id
                    WHERE s.iin ILIKE %s OR s.first_name ILIKE %s OR s.last_name ILIKE %s OR g.name ILIKE %s
                """, (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))

        students = cursor.fetchall()
        cursor.close()
        conn.close()

        return render_template('manage_students.html', students=students, search_query=search_query, search_field=search_field)

    except Exception as e:
        flash(f"Ошибка при поиске: {e}", "error")
        return redirect(url_for('tprofile'))


@app.route('/delete_student/<int:student_id>', methods=['POST'])
@login_required
def delete_student(student_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        conn.commit()

        cursor.close()
        conn.close()
        flash("Студент успешно удален", "success")
    except Exception as e:
        flash(f"Ошибка при удалении студента: {e}", "error")

    return redirect(url_for('manage_students'))


@app.route('/update_student/<int:student_id>', methods=['POST'])
@login_required
def update_student(student_id):
    iin = request.form.get('iin')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    group_name = request.form.get('group_name')

    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM groups WHERE name = %s", (group_name,))
        group = cursor.fetchone()

        if group:
            group_id = group[0]
        else:
            flash("Группа не найдена!", "error")
            return redirect(url_for('manage_students'))

        cursor.execute("""
            UPDATE students 
            SET iin = %s, first_name = %s, last_name = %s, group_id = %s
            WHERE id = %s
        """, (iin, first_name, last_name, group_id, student_id))

        conn.commit()

        cursor.close()
        conn.close()
        flash("Данные студента успешно обновлены", "success")
    except Exception as e:
        flash(f"Ошибка при обновлении студента: {e}", "error")

    return redirect(url_for('manage_students'))

@app.route('/exam_list')
def exam_list():
    test_results  = (
        db.session.query(Result, Student, Test)
        .join(Student, Result.student_id == Student.id)
        .join(Test, Result.test_id == Test.id)
        .all()
    )
    if not test_results:
        return "Результаты тестов не найдены", 404

    return render_template('exam_list.html', test_results=test_results)


@app.route('/delete_test/<int:test_id>', methods=['POST'])
def delete_test(test_id):
    db.session.query(TestGroup).filter(TestGroup.test_id == test_id).update({'test_id': None}, synchronize_session=False)
    
    test = db.session.query(Test).get(test_id)
    if test:
        db.session.delete(test)
        db.session.commit()
    else:
        flash("Test not found!")
    
    return redirect(url_for('tests_list'))  


@app.route('/teacher/create_test', methods=['GET', 'POST'])
def create_test():
    form = TestForm()
    if form.validate_on_submit():
        test = Test(
            title=form.title.data,
            subject_id=form.subject.data,
            time_limit=form.time_limit.data,
            description=form.description.data,
            teacher_id=current_user.id  
        )
        db.session.add(test)
        db.session.commit()
        flash('Тест успешно добавлен!', 'success')
        return redirect(url_for('add_questions', test_id=test.id))
    return render_template('add_test.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)


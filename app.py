from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'RADHAKRISHNA'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quizmaster.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    full_name = db.Column(db.String(100))
    qualification = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    is_admin = db.Column(db.Boolean, default=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade="all, delete-orphan")

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    quizzes = db.relationship('Quiz', backref='chapter', lazy=True, cascade="all, delete-orphan")

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_of_quiz = db.Column(db.String(20))
    time_duration = db.Column(db.String(10)) 
    remarks = db.Column(db.Text)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan")
    scores = db.relationship('Score', backref='quiz', lazy=True, cascade="all, delete-orphan")
    


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_statement = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.Text, nullable=False)
    option2 = db.Column(db.Text, nullable=False)
    option3 = db.Column(db.Text)
    option4 = db.Column(db.Text)
    correct_option = db.Column(db.Integer, nullable=False)  # 1-4
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def is_logged_in():
    return 'user_id' in session

def is_admin():
    return is_logged_in() and User.query.get(session['user_id']).is_admin


def create_admin():
    if not User.query.filter_by(is_admin=True).first():
        admin = User(
            username='admin',
            password=generate_password_hash('0000'),
            full_name='Admin',
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()


@app.route('/')
def home():
    if is_logged_in():
        if is_admin():
            return redirect('/admin/dashboard')
        return redirect('/user/dashboard')
    return render_template('home.html')

# Authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Login successful', 'success')
            if user.is_admin:
                return redirect('/admin/dashboard')
            return redirect('/user/dashboard')
        
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect('/register')
        
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            full_name=full_name,
            qualification=request.form.get('qualification'),
            dob=request.form.get('dob')
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful. Please login.', 'success')
        return redirect('/login')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect('/')



@app.route('/admin/subject/add', methods=['POST'])
def add_subject():
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    name = request.form['name']
    description = request.form['description']
    
    new_subject = Subject(name=name, description=description)
    db.session.add(new_subject)
    db.session.commit()
    
    flash('Subject added successfully', 'success')
    return redirect('/admin/dashboard')

@app.route('/admin/subject/<int:subject_id>/chapter/add', methods=['POST'])
def add_chapter(subject_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    name = request.form['name']
    description = request.form['description']
    
    new_chapter = Chapter(
        name=name,
        description=description,
        subject_id=subject_id
    )
    db.session.add(new_chapter)
    db.session.commit()
    
    flash('Chapter added successfully', 'success')
    return redirect(f'/admin/subject/{subject_id}')


@app.route('/admin/chapter/<int:chapter_id>/quiz/add', methods=['POST'])
def add_quiz(chapter_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    title = request.form['title']
    date_of_quiz = request.form['date_of_quiz']
    time_duration = request.form['time_duration']
    remarks = request.form.get('remarks', '')
    
    new_quiz = Quiz(
        title=title,
        date_of_quiz=date_of_quiz,
        time_duration=time_duration,
        remarks=remarks,
        chapter_id=chapter_id
    )
    db.session.add(new_quiz)
    db.session.commit()
    
    flash('Quiz added successfully', 'success')
    return redirect(f'/admin/chapter/{chapter_id}')



@app.route('/admin/quiz/<int:quiz_id>/question/add', methods=['POST'])
def add_question(quiz_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    question_statement = request.form['question_statement']
    option1 = request.form['option1']
    option2 = request.form['option2']
    option3 = request.form.get('option3', '')
    option4 = request.form.get('option4', '')
    correct_option = int(request.form['correct_option'])
    
    new_question = Question(
        question_statement=question_statement,
        option1=option1,
        option2=option2,
        option3=option3,
        option4=option4,
        correct_option=correct_option,
        quiz_id=quiz_id
    )
    db.session.add(new_question)
    db.session.commit()
    
    flash('Question added successfully', 'success')
    return redirect(f'/admin/quiz/{quiz_id}')

# @app.route('/admin/dashboard', methods=['GET', 'POST'])
# def admin_dashboard():
#     if not is_admin():
#         flash('Unauthorized access', 'danger')
#         return redirect('/')
    
#     # Score summary for all users
#     score_summary = db.session.query(
#         User.username,
#         User.full_name,
#         func.count(Score.id).label('total_attempts'),
#         func.avg(Score.score * 100.0 / Score.total_questions).label('avg_score')
#     ).join(Score, User.id == Score.user_id).group_by(User.id).all()
    
#     # Count of all entities
#     subjects_count = Subject.query.count()
#     chapters_count = Chapter.query.count()
#     quizzes_count = Quiz.query.count()
#     questions_count = Question.query.count()
    
#     subjects = Subject.query.all()
#     return render_template('admin/dashboard.html',
#                          subjects=subjects,
#                          score_summary=score_summary,
#                          subjects_count=subjects_count,
#                          chapters_count=chapters_count,
#                          quizzes_count=quizzes_count,
#                          questions_count=questions_count)



@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    # Handle subject creation from modal
    if request.method == 'POST' and 'create_subject' in request.form:
        name = request.form['name']
        description = request.form['description']
        new_subject = Subject(name=name, description=description)
        db.session.add(new_subject)
        db.session.commit()
        flash('Subject created successfully', 'success')
        return redirect('/admin/dashboard')
    
    subjects = Subject.query.all()
    return render_template('admin/dashboard.html', subjects=subjects)

# Admin Subject View - Handles chapter creation via modal
@app.route('/admin/subject/<int:subject_id>', methods=['GET', 'POST'])
def view_subject(subject_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST' and 'create_chapter' in request.form:
        name = request.form['name']
        description = request.form['description']
        new_chapter = Chapter(
            name=name,
            description=description,
            subject_id=subject_id
        )
        db.session.add(new_chapter)
        db.session.commit()
        flash('Chapter created successfully', 'success')
        return redirect(f'/admin/subject/{subject_id}')
    
    # Load all chapters for this subject
    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template('admin/subject.html', subject=subject, chapters=chapters)

# Admin Chapter View - Handles quiz creation via modal
@app.route('/admin/chapter/<int:chapter_id>', methods=['GET', 'POST'])
def view_chapter(chapter_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    chapter = Chapter.query.get_or_404(chapter_id)
    
    # Handle quiz creation from modal
    if request.method == 'POST' and 'create_quiz' in request.form:
        title = request.form['title']
        date_of_quiz = request.form['date_of_quiz']
        time_duration = request.form['time_duration']
        remarks = request.form.get('remarks', '')
        
        new_quiz = Quiz(
            title=title,
            date_of_quiz=date_of_quiz,
            time_duration=time_duration,
            remarks=remarks,
            chapter_id=chapter_id
        )
        db.session.add(new_quiz)
        db.session.commit()
        flash('Quiz created successfully', 'success')
        return redirect(f'/admin/chapter/{chapter_id}')
    
    return render_template('admin/chapter.html', chapter=chapter)

# Admin Quiz View - Handles question creation via modal
@app.route('/admin/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def view_quiz(quiz_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Handle question creation from modal
    if request.method == 'POST' and 'create_question' in request.form:
        question_statement = request.form['question_statement']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form.get('option3', '')
        option4 = request.form.get('option4', '')
        correct_option = int(request.form['correct_option'])
        
        new_question = Question(
            question_statement=question_statement,
            option1=option1,
            option2=option2,
            option3=option3,
            option4=option4,
            correct_option=correct_option,
            quiz_id=quiz_id
        )
        db.session.add(new_question)
        db.session.commit()
        flash('Question added successfully', 'success')
        return redirect(f'/admin/quiz/{quiz_id}')
    
    return render_template('admin/quiz.html', quiz=quiz)




@app.route('/admin/subject/<int:subject_id>/edit', methods=['GET', 'POST'])
def edit_subject(subject_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        subject.name = request.form['name']
        subject.description = request.form['description']
        db.session.commit()
        flash('Subject updated successfully', 'success')
        return redirect('/admin/dashboard')
    
    return render_template('admin/edit_subject.html', subject=subject)

@app.route('/admin/subject/<int:subject_id>/delete', methods=['POST'])
def delete_subject(subject_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash('Subject deleted successfully', 'success')
    return redirect('/admin/dashboard')

# Admin CRUD for Chapters
@app.route('/admin/chapter/<int:chapter_id>/edit', methods=['GET', 'POST'])
def edit_chapter(chapter_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    chapter = Chapter.query.get_or_404(chapter_id)
    
    if request.method == 'POST':
        chapter.name = request.form['name']
        chapter.description = request.form['description']
        db.session.commit()
        flash('Chapter updated successfully', 'success')
        return redirect(f'/admin/subject/{chapter.subject_id}')
    
    return render_template('admin/edit_chapter.html', chapter=chapter)

@app.route('/admin/chapter/<int:chapter_id>/delete', methods=['POST'])
def delete_chapter(chapter_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    chapter = Chapter.query.get_or_404(chapter_id)
    subject_id = chapter.subject_id
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully', 'success')
    return redirect(f'/admin/subject/{subject_id}')

# Admin CRUD for Quizzes
@app.route('/admin/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
def edit_quiz(quiz_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        quiz.title = request.form['title']
        quiz.date_of_quiz = request.form['date_of_quiz']
        quiz.time_duration = request.form['time_duration']
        quiz.remarks = request.form.get('remarks', '')
        db.session.commit()
        flash('Quiz updated successfully', 'success')
        return redirect(f'/admin/chapter/{quiz.chapter_id}')
    
    return render_template('admin/edit_quiz.html', quiz=quiz)

@app.route('/admin/quiz/<int:quiz_id>/delete', methods=['POST'])
def delete_quiz(quiz_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter_id = quiz.chapter_id
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully', 'success')
    return redirect(f'/admin/chapter/{chapter_id}')

# Admin CRUD for Questions
@app.route('/admin/question/<int:question_id>/edit', methods=['GET', 'POST'])
def edit_question(question_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        question.question_statement = request.form['question_statement']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form.get('option3', '')
        question.option4 = request.form.get('option4', '')
        question.correct_option = int(request.form['correct_option'])
        db.session.commit()
        flash('Question updated successfully', 'success')
        return redirect(f'/admin/quiz/{question.quiz_id}')
    
    return render_template('admin/edit_question.html', question=question)

@app.route('/admin/question/<int:question_id>/delete', methods=['POST'])
def delete_question(question_id):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    question = Question.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted successfully', 'success')
    return redirect(f'/admin/quiz/{quiz_id}')

@app.route('/user/dashboard', methods=['GET', 'POST'])
def user_dashboard():
    if not is_logged_in() or is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    user = User.query.get(session['user_id'])
    query = request.args.get('q', '')
    
    # User's score summary
    user_scores = Score.query.filter_by(user_id=user.id).all()
    total_attempts = len(user_scores)
    
    # Safely calculate average score
    avg_score = 0
    if total_attempts > 0:
        total_percentage = 0
        valid_attempts = 0
        
        for s in user_scores:
            if s.total_questions > 0:  # Only include attempts with questions
                total_percentage += (s.score / s.total_questions) * 100
                valid_attempts += 1
        
        if valid_attempts > 0:
            avg_score = total_percentage / valid_attempts
    
    # Search functionality
    if query:
        subjects = Subject.query.filter(Subject.name.ilike(f'%{query}%')).all()
        chapters = Chapter.query.filter(Chapter.name.ilike(f'%{query}%')).all()
        quizzes = Quiz.query.filter(Quiz.title.ilike(f'%{query}%')).all()
        
        return render_template('user/dashboard.html',
                             user=user,
                             subjects=subjects,
                             chapters=chapters,
                             quizzes=quizzes,
                             query=query,
                             total_attempts=total_attempts,
                             avg_score=avg_score)
    
    # Normal dashboard view
    subjects = Subject.query.all()
    return render_template('user/dashboard.html',
                         user=user,
                         subjects=subjects,
                         total_attempts=total_attempts,
                         avg_score=avg_score)

@app.route('/user/subject/<int:subject_id>')
def user_view_subject(subject_id):
    if not is_logged_in() or is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    subject = Subject.query.get_or_404(subject_id)
    return render_template('user/subject.html', subject=subject)



# User Chapter View
@app.route('/user/chapter/<int:chapter_id>')
def user_view_chapter(chapter_id):
    if not is_logged_in() or is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    chapter = Chapter.query.get_or_404(chapter_id)
    return render_template('user/chapter.html', chapter=chapter)

# Take Quiz
@app.route('/user/quiz/<int:quiz_id>', methods=['GET', 'POST'])
def take_quiz(quiz_id):
    if not is_logged_in() or is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if request.method == 'POST':
        score = 0
        total_questions = len(quiz.questions)  # Use actual question count
        user_answers = {}
        
        for question in quiz.questions:
            user_answer = request.form.get(f'question_{question.id}')
            user_answers[question.id] = user_answer
            
            if user_answer and int(user_answer) == question.correct_option:
                score += 1
        
        # Only record score if there were questions
        if total_questions > 0:
            new_score = Score(
                user_id=session['user_id'],
                quiz_id=quiz_id,
                score=score,
                total_questions=total_questions
            )
            db.session.add(new_score)
            db.session.commit()
            
            # Store user answers in session for result page
            session['quiz_answers'] = {
                'quiz_id': quiz_id,
                'user_answers': user_answers,
                'score_id': new_score.id
            }
            
            return redirect(f'/user/quiz/{quiz_id}/result')
        else:
            flash('This quiz has no questions to score', 'warning')
            return redirect(f'/user/quiz/{quiz_id}')
    
    return render_template('user/take_quiz.html', quiz=quiz)


@app.route('/user/quiz/<int:quiz_id>/result')
def quiz_result(quiz_id):
    if not is_logged_in() or is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    quiz = Quiz.query.get_or_404(quiz_id)
    saved_answers = session.get('quiz_answers', {})
    
    # Check if this is the correct quiz result
    if saved_answers.get('quiz_id') != quiz_id:
        flash('Invalid quiz result access', 'danger')
        return redirect('/user/dashboard')
    
    score = Score.query.get_or_404(saved_answers['score_id'])
    user_answers = saved_answers.get('user_answers', {})
    
    # Handle case where total_questions is zero
    if score.total_questions == 0:
        flash('This quiz had no questions', 'warning')
        return redirect(f'/user/quiz/{quiz_id}')
    
    return render_template('user/quiz_result.html', 
                         quiz=quiz,
                         score=score,
                         user_answers=user_answers)


@app.route('/user/scores')
def user_scores():
    if not is_logged_in() or is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    scores = Score.query.filter_by(
        user_id=session['user_id']
    ).order_by(Score.timestamp.desc()).all()
    
    return render_template('user/scores.html', scores=scores)


@app.route('/user/quiz/<int:quiz_id>/result/<int:attempt_id>')
def view_attempt(quiz_id, attempt_id):
    if not is_logged_in() or is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    quiz = Quiz.query.get_or_404(quiz_id)
    score = Score.query.filter_by(
        id=attempt_id,
        user_id=session['user_id'],
        quiz_id=quiz_id
    ).first_or_404()
    return render_template('user/quiz_result.html', 
                         quiz=quiz,
                         score=score,
                         user_answers={})

@app.route('/admin/user/<username>/scores')
def admin_view_user_scores(username):
    if not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect('/')
    
    user = User.query.filter_by(username=username).first_or_404()
    scores = Score.query.filter_by(user_id=user.id).order_by(Score.timestamp.desc()).all()
    
    return render_template('admin/user_scores.html', user=user, scores=scores)


# Initialize app
with app.app_context():
    db.create_all()
    create_admin()

if __name__ == '__main__':
    app.run(debug=True)
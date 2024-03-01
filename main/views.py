from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import pandas as pd
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render
from .models import Question, Option

# Create your views here.
@login_required(login_url = 'dash:login')
def main(request):
    quizes = Quiz.objects.filter(author = request.user)
    context = {
        "quizes" : quizes
    }
    return render(request, 'main.html', context)

@login_required(login_url = 'dash:login')
def create_quiz(request):
    if request.method == 'POST':
        title = request.POST['title']
        quiz = Quiz.objects.create(
            title = title,
            author = request.user
        )
        return redirect('dash:quest_create', quiz.id)
    return render(request, 'quiz/create-quiz.html')

@login_required(login_url = 'dash:login')
def create_question(request, id):
    quiz = Quiz.objects.get(id = id)
    if request.method == 'POST':
        
        title = request.POST['title']
        ques = Question.objects.create(
            quiz = quiz,
            title = title
        )
        Option.objects.create(
            question = ques,
            name = request.POST['correct'],
            is_correct = True
        )
        data = [request.POST['incorrect1'], request.POST['incorrect2'], request.POST['incorrect3']]

        for i in data:
            Option.objects.create(
                question = ques,
                name = i,
            )
        if request.POST['submit_action'] == 'exit':
            return redirect('dash:main')

    return render (request, 'quiz/create-question.html' )

@login_required(login_url = 'dash:login')
def questions_list(request, id):
    quests = Question.objects.filter(quiz_id = id)
    context = {
        'questions': quests
    }
    return render (request, 'details/questions.html', context)

@login_required(login_url = 'dash:login')
def quest_detail(request, id):
    question = Question.objects.get(id = id)
    option_correct = Option.objects.get(question = question, is_correct = True)
    options = Option.objects.filter(question = question, is_correct = False).order_by('id')
    context = {
        'question': question,
        'options': options,
        'option_correct' : option_correct
    }
    if request.method == 'POST':
        question.title = request.POST['title']
        question.save()

        option_correct.name = request.POST['correct']
        option_correct.save()

        data = [request.POST['incorrect1'], request.POST['incorrect2'], request.POST['incorrect3']]

        for i, opt in enumerate(options):
            opt.name = data[i]
            opt.save()
    return render( request, 'details/detail.html', context)

@login_required(login_url = 'dash:login')
def quiz_delete(request, id):
    Quiz.objects.get(id = id).delete()
    return redirect('dash:main')

@login_required(login_url = 'dash:login')
def get_results(request, id):
    quiz = Quiz.objects.get(id=id)
    taker = QuizTaker.objects.filter(quiz=quiz)

    # results = []
    # for i in taker:
    #     results.append(Result.objects.get(taker=i))
    
    results = tuple(
            map(
            lambda x : Result.objects.get(taker=x),
            taker
        )
    )
    return render(request, 'quiz/results.html', {'results':results})


def result_detail(request, id):
    result = Result.objects.get(id=id)
    answers = Answer.objects.filter(taker=result.taker)

    # Count correct and incorrect answers
    correct_count = answers.filter(is_correct=True).count()
    incorrect_count = answers.filter(is_correct=False).count()

    context = {
        'taker': result.taker,
        'answers': answers,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
    }

    return render(request, 'quiz/result-detail.html', context)


#login


def logging_in(request):
    status = False
    if request.method == 'POST':
        username = request.POST['username']
        password =  request.POST['password']
        user = authenticate(username = username, password=password)
        if user:
            login(request, user)
            return redirect('dash:main')
        else:
            status = 'incorrect username or password'
    return render(request, 'auth/login.html', {'status':status})

def register(request):
    status = False
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if not User.objects.filter(username = username).first():
            User.objects.create_user(
                username=username,
                password=password
            )
            user = authenticate(username = username, password = password)
            login(request, user)
            return redirect('dash:main')
        else:
            status  = f'the username {username} is occupied'
    return render(request, 'auth/register.html', {'status': status})










def export_results_excel(request):
    results = Result.objects.all()
    data = {
        'Full Name': [result.taker.full_name for result in results],
        'Total Questions': [result.questions for result in results],
        'Correct Answers': [result.correct_answers for result in results],
        'Incorrect Answers': [result.incorrect_answers for result in results],
        'Percentage': [result.percentage for result in results],
    }
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=quiz_results.xlsx'
    df.to_excel(response, index=False, engine='openpyxl')

    return response

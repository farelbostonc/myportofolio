from django.shortcuts import render

from main.models import Experience, Education


def show_main(request):
    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "npm": "2506548490",
        "study_program": "S1 Sistem Informasi",
        "bio": (
            "Mahasiswa Sistem Informasi Universitas Indonesia yang tertarik "
            "pada keamanan siber dan bisnis."
        ),
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

def show_education(request):
    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "education_list": Education.objects.all(),
    }
    return render(request, "education.html", context)
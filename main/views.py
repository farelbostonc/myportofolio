from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from main.forms import EducationForm, ExperienceForm, ProjectForm, edit_key_is_valid
from main.models import Education, Experience, Project


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


def create_experience(request):
    form = ExperienceForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Experience berhasil ditambahkan!")
        return redirect("main:show_experience")

    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "form": form,
        "page_title": "Add Experience",
        "heading": "Tambah Experience",
        "submit_label": "Tambah Experience",
        "cancel_url_name": "main:show_experience",
    }
    return render(request, "content_form.html", context)


def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)

    if request.method == "POST" and edit_key_is_valid(request.POST.get("access_key")):
        experience.delete()
        messages.success(request, "Experience berhasil dihapus!")
        return redirect("main:show_experience")

    if request.method == "POST":
        messages.error(
            request,
            "Experience tidak dihapus: kode rahasia admin tidak valid.",
        )

    return redirect("main:show_experience")


def show_education(request):
    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "education_list": Education.objects.all(),
    }
    return render(request, "education.html", context)


def create_education(request):
    form = EducationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Education berhasil ditambahkan!")
        return redirect("main:show_education")

    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "form": form,
        "page_title": "Add Education",
        "heading": "Tambah Education",
        "submit_label": "Tambah Education",
        "cancel_url_name": "main:show_education",
    }
    return render(request, "content_form.html", context)


def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)

    if request.method == "POST" and edit_key_is_valid(request.POST.get("access_key")):
        education.delete()
        messages.success(request, "Education berhasil dihapus!")
        return redirect("main:show_education")

    if request.method == "POST":
        messages.error(
            request,
            "Education tidak dihapus: kode rahasia admin tidak valid.",
        )

    return redirect("main:show_education")


def create_project(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "form": form,
    }
    return render(request, "projects_form.html", context)

def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    form = ProjectForm(
        request.POST or None,
        instance=project,
    )

    if request.method == "POST":
        if not edit_key_is_valid(request.POST.get("access_key")):
            messages.error(
                request,
                "Project tidak diperbarui: kode rahasia admin tidak valid.",
            )

        elif form.is_valid():
            form.save()
            messages.success(
                request,
                "Project berhasil diperbarui!",
            )
            return redirect("main:show_projects")

    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "form": form,
        "project": project,
        "page_title": "Edit Project",
        "heading": "Edit Project",
        "submit_label": "Simpan Perubahan",
        "cancel_url_name": "main:show_projects",
        "is_edit": True,
    }

    return render(
        request,
        "projects_form.html",
        context,
    )

def show_projects(request):
    json_response = get_projects_json(request)
    projects = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    projects = [project.object for project in projects]
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "project_list": projects,
        "title_query": title_query,
    }
    return render(request, "project.html", context)

def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    projects_json = serializers.serialize("json", projects)
    return HttpResponse(projects_json, content_type="application/json")

def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if request.method == "POST" and edit_key_is_valid(request.POST.get("access_key")):
        project.delete()
        messages.success(request, "Project berhasil dihapus!")
        return redirect("main:show_projects")

    if request.method == "POST":
        messages.error(
            request,
            "Project tidak dihapus: kode rahasia admin tidak valid.",
        )

    return redirect("main:show_projects")

import datetime
from functools import wraps

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from main.forms import EducationForm, ExperienceForm, ProjectForm
from main.models import Education, Experience, Project


def role_required(*, owner_only=False):
    def decorator(view_func):
        @wraps(view_func)
        @login_required(login_url="/login/")
        def wrapped(request, *args, **kwargs):
            is_editor = request.user.groups.filter(name="Editor").exists()
            allowed = request.user.is_superuser or (
                not owner_only and is_editor
            )
            if not allowed:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def show_main(request):
    last_login = request.COOKIES.get('last_login', 'Belum ada sesi login / Cookie tidak ditemukan')
    context = {
        "name": "Boston",
        "npm": "2506548490",
        "study_program": "S1 Sistem Informasi",
        "bio": (
            "Mahasiswa Sistem Informasi Universitas Indonesia yang tertarik "
            "pada keamanan siber dan bisnis."
        ),
        "last_login": last_login,
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

@role_required(owner_only=True)
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

@role_required(owner_only=True)
@require_POST
def delete_experience(request, experience_id):
    experience = get_object_or_404(Experience, pk=experience_id)
    experience.delete()
    messages.success(request, "Experience berhasil dihapus!")
    return redirect("main:show_experience")


def show_education(request):
    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "education_list": Education.objects.all(),
    }
    return render(request, "education.html", context)

@role_required(owner_only=True)
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

@role_required(owner_only=True)
@require_POST
def delete_education(request, education_id):
    education = get_object_or_404(Education, pk=education_id)
    education.delete()
    messages.success(request, "Education berhasil dihapus!")
    return redirect("main:show_education")


@require_GET
def get_education_json(request):
    title_query = request.GET.get("title", "").strip()
    educations = Education.objects.annotate(
        star_count=Count("starred_by"),
    ).order_by("title", "id")

    if request.user.is_authenticated:
        user_stars = Education.starred_by.through.objects.filter(
            education_id=OuterRef("pk"),
            user_id=request.user.pk,
        )
        educations = educations.annotate(is_starred=Exists(user_stars))

    if title_query:
        educations = educations.filter(
            Q(title__icontains=title_query)
            | Q(description__icontains=title_query)
        )

    data = []
    for education in educations:
        data.append({
            "pk": str(education.pk),
            "fields": {
                "title": education.title,
                "description": education.description,
                "start_year": education.start_year,
                "end_year": education.end_year,
                "star_count": education.star_count,
                "is_starred": (
                    education.is_starred
                    if request.user.is_authenticated
                    else False
                ),
            },
            "urls": {
                "star": reverse(
                    "main:toggle_education_star_ajax",
                    args=[education.pk],
                ),
                "delete": reverse(
                    "main:delete_education_ajax",
                    args=[education.pk],
                ),
            },
        })

    return JsonResponse(data, safe=False)


@require_POST
def create_education_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Hanya pemilik portofolio yang dapat menambah pendidikan."},
            status=403,
        )

    form = EducationForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {"errors": form.errors.get_json_data()},
            status=400,
        )

    education = form.save()
    return JsonResponse(
        {
            "message": "Pendidikan berhasil ditambahkan.",
            "pk": str(education.pk),
        },
        status=201,
    )


@require_POST
def toggle_education_star_ajax(request, education_id):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"message": "Silakan login untuk memberi star."},
            status=403,
        )

    with transaction.atomic():
        education = (
            Education.objects.select_for_update()
            .filter(pk=education_id)
            .first()
        )
        if education is None:
            return JsonResponse(
                {"message": "Data pendidikan tidak ditemukan."},
                status=404,
            )

        if education.starred_by.filter(pk=request.user.pk).exists():
            education.starred_by.remove(request.user)
            is_starred = False
        else:
            education.starred_by.add(request.user)
            is_starred = True

        star_count = education.starred_by.count()

    return JsonResponse({
        "star_count": star_count,
        "is_starred": is_starred,
        "message": "Star ditambahkan." if is_starred else "Star dibatalkan.",
    })


@require_POST
def delete_education_ajax(request, education_id):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Hanya pemilik portofolio yang dapat menghapus pendidikan."},
            status=403,
        )

    education = Education.objects.filter(pk=education_id).first()
    if education is None:
        return JsonResponse(
            {"message": "Data pendidikan tidak ditemukan."},
            status=404,
        )

    education.delete()
    return JsonResponse({"message": "Pendidikan berhasil dihapus."})


@role_required(owner_only=True)
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

@role_required()
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = ProjectForm(request.POST or None, instance=project)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Project berhasil diperbarui!")
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
    return render(request, "projects_form.html", context)

def show_projects(request):
    title_query = request.GET.get("title", "").strip()
    context = {
        "name": "Farel Boston Corinthians Nadeak",
        "title_query": title_query,
        "form": ProjectForm(),
        "is_editor": (
            request.user.is_authenticated
            and request.user.groups.filter(name="Editor").exists()
        ),
    }
    return render(request, "project.html", context)

def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Project.objects.prefetch_related("starred_by").all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    data = []
    for project in projects:
        starred_users = list(project.starred_by.all())
        data.append({
            "pk": str(project.id),
            "fields": {
                "title": project.title,
                "description": project.description,
                "tech_stack": project.tech_stack,
                "project_url": project.project_url,
                "project_image_url": project.project_image_url,
                "star_count": len(starred_users),
                "is_starred": (
                    request.user.is_authenticated
                    and any(user.pk == request.user.pk for user in starred_users)
                ),
                "starred_by_names": ", ".join(
                    user.username for user in starred_users
                ),
            },
        })
    return JsonResponse(data, safe=False)


@require_POST
def create_project_ajax(request):
    if not request.user.is_superuser:
        return JsonResponse(
            {"message": "Hanya pemilik portofolio yang dapat menambahkan proyek."},
            status=403,
        )
    form = ProjectForm(request.POST)
    if form.is_valid():
        project = form.save()
        return JsonResponse(
            {"message": "Proyek berhasil ditambahkan.", "pk": str(project.id)},
            status=201,
        )
    return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

@role_required(owner_only=True)
@require_POST
def delete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    project.delete()
    messages.success(request, "Project berhasil dihapus!")
    return redirect("main:show_projects")

def register(request):
    form = UserCreationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Akun berhasil dibuat. Silakan login.")
        return redirect("main:login")

    context = {
        "name": "Boston",
        "form": form,
    }
    return render(request, "register.html", context)

def login_user(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        response = redirect("main:show_main")
        response.set_cookie('last_login', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return response

    context = {
        "name": "boston",
        "form": form,
    }
    return render(request, "login.html", context)

def logout_user(request):
    logout(request)
    response = redirect("main:show_main")
    response.delete_cookie('last_login')
    return response

# Tanpa cek is_superuser: semua akun yang sudah login boleh memberi star
@login_required(login_url="/login/")
@require_POST
def toggle_star(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    if project.starred_by.filter(pk=request.user.pk).exists():
        project.starred_by.remove(request.user)
    else:
        project.starred_by.add(request.user)

    return redirect("main:show_projects")

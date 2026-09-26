from django.urls import path

from main.views import (
    create_education,
    create_experience,
    create_project,
    delete_education,
    delete_experience,
    delete_project,
    get_projects_json,
    register,
    login_user,
    logout_user,
    show_education,
    show_experience,
    show_main,
    show_projects,
    edit_project,
    toggle_star,
)

app_name = "main"

urlpatterns = [
    path("", show_main, name="show_main"),
    path("experience/", show_experience, name="show_experience"),
    path("experience/add/", create_experience, name="create_experience"),
    path(
        "experience/<uuid:experience_id>/delete/",
        delete_experience,
        name="delete_experience",
    ),
    path("education/", show_education, name="show_education"),
    path("education/add/", create_education, name="create_education"),
    path(
        "education/<uuid:education_id>/delete/",
        delete_education,
        name="delete_education",
    ),
    path("projects/add/", create_project, name="create_project"),
    path("projects/", show_projects, name="show_projects"),
    path("api/projects/", get_projects_json, name="get_projects_json"),
    path(
        "projects/<uuid:project_id>/delete/",
        delete_project,
        name="delete_project",
    ),
    path(
        "projects/<uuid:project_id>/edit/",
        edit_project,
        name="edit_project",
    ), 
    path("register/", register, name="register"),
    path("login/", login_user, name="login"),
    path("logout/", logout_user, name="logout"),
    # Tambahkan path ini ke dalam urlpatterns
    path(
        "projects/<uuid:project_id>/star/",
        toggle_star,
        name="toggle_star",
    ),
]

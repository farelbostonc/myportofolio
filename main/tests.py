from django.test import TestCase
from django.contrib.auth.models import Group, User
from django.urls import reverse
from django.utils import timezone

from main.models import Education, Experience, Project

class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Lab Cyber Security and Cryptography",
            description="Membantu mengurus OS pada komputer lab serta maintanance web lab Cyber Security and Cryptography",
            category="part-time",
        )
        self.education = Education.objects.create(
            title="S1 Sistem Informasi",
            description="Fakultas Ilmu Komputer, Universitas Indonesia",
            start_year="2025",
            end_year="Present",
        )
        self.project = Project.objects.create(
            title="Portfolio",
            description="Website portfolio pribadi",
            tech_stack="Django",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertNotContains(response, self.experience.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Lab Cyber Security and Cryptography")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")

    # 1. URL dapat diakses dan menggunakan template yang tepat
    def test_education_url_is_accessible(self):
        response = self.client.get(
            reverse("main:show_education")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "education.html")

    # 2. Data Education muncul pada halaman HTML
    def test_education_data_appears_on_page(self):
        response = self.client.get(
            reverse("main:show_education")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.education.title)
        self.assertContains(response, self.education.description)
        self.assertContains(response, self.education.start_year)
        self.assertContains(response, self.education.end_year)

    # 3. Menampilkan pesan jika belum ada data Education
    def test_empty_education_page(self):
        Education.objects.all().delete()

        response = self.client.get(
            reverse("main:show_education")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Belum ada edukasi yang ditambahkan."
        )

    def setUpTestUsers(self):
        self.regular = User.objects.create_user(
            username="regular", password="test-password"
        )
        self.editor = User.objects.create_user(
            username="editor", password="test-password"
        )
        self.owner = User.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="test-password",
        )
        editor_group = Group.objects.create(name="Editor")
        self.editor.groups.add(editor_group)

    def project_data(self, title="Updated Portfolio"):
        return {
            "title": title,
            "description": "Deskripsi baru",
            "tech_stack": "Django, Python",
            "project_url": "",
            "project_image_url": "",
        }

    def test_guest_redirected_from_account_actions(self):
        edit_url = reverse("main:edit_project", args=[self.project.id])
        delete_url = reverse("main:delete_project", args=[self.project.id])
        star_url = reverse("main:toggle_star", args=[self.project.id])

        for url in (
            reverse("main:create_experience"),
            reverse("main:create_education"),
            reverse("main:create_project"),
            edit_url,
        ):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith("/login/"))

        for url in (delete_url, star_url):
            with self.subTest(url=url):
                response = self.client.post(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response["Location"].startswith("/login/"))

    def test_regular_user_cannot_create_edit_or_delete(self):
        self.setUpTestUsers()
        self.client.force_login(self.regular)

        create_urls = (
            reverse("main:create_experience"),
            reverse("main:create_education"),
            reverse("main:create_project"),
        )
        for url in create_urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

        edit_url = reverse("main:edit_project", args=[self.project.id])
        delete_url = reverse("main:delete_project", args=[self.project.id])
        self.assertEqual(self.client.get(edit_url).status_code, 403)
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_editor_can_edit_but_cannot_create_or_delete(self):
        self.setUpTestUsers()
        self.client.force_login(self.editor)

        edit_url = reverse("main:edit_project", args=[self.project.id])
        response = self.client.post(edit_url, self.project_data())
        self.assertRedirects(response, reverse("main:show_projects"))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "Updated Portfolio")

        for url in (
            reverse("main:create_experience"),
            reverse("main:create_education"),
            reverse("main:create_project"),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 403)

        delete_url = reverse("main:delete_project", args=[self.project.id])
        self.assertEqual(self.client.post(delete_url).status_code, 403)
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

    def test_owner_can_create_and_delete_project(self):
        self.setUpTestUsers()
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("main:create_project"),
            self.project_data(title="Owner Project"),
        )
        self.assertRedirects(response, reverse("main:show_projects"))
        new_project = Project.objects.get(title="Owner Project")

        delete_url = reverse("main:delete_project", args=[new_project.id])
        self.assertEqual(self.client.get(delete_url).status_code, 405)
        self.assertTrue(Project.objects.filter(pk=new_project.id).exists())

        response = self.client.post(delete_url)
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(Project.objects.filter(pk=new_project.id).exists())

    def test_star_toggles_once_per_user_and_requires_post(self):
        self.setUpTestUsers()
        self.client.force_login(self.regular)
        star_url = reverse("main:toggle_star", args=[self.project.id])

        self.assertEqual(self.client.get(star_url).status_code, 405)
        self.assertEqual(self.project.starred_by.count(), 0)

        self.client.post(star_url)
        self.assertEqual(self.project.starred_by.count(), 1)
        self.assertTrue(self.project.starred_by.filter(pk=self.regular.pk).exists())

        self.client.post(star_url)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_project_page_renders_ajax_container_for_starred_projects(self):
        self.setUpTestUsers()
        self.project.starred_by.add(self.regular)
        self.client.force_login(self.regular)

        response = self.client.get(reverse("main:show_projects"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="grid"')
        self.assertContains(response, "BASE_PROJECTS_ENDPOINT")
        self.assertNotContains(response, self.project.title)

    def test_json_contains_project_fields_and_star_data(self):
        self.setUpTestUsers()
        self.project.starred_by.add(self.regular)

        response = self.client.get(reverse("main:get_projects_json"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/json"))

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["pk"], str(self.project.id))
        self.assertEqual(set(data[0]["fields"]), {
            "title",
            "description",
            "tech_stack",
            "project_url",
            "project_image_url",
            "star_count",
            "is_starred",
            "starred_by_names",
        })
        self.assertEqual(data[0]["fields"]["star_count"], 1)
        self.assertFalse(data[0]["fields"]["is_starred"])
        self.assertEqual(data[0]["fields"]["starred_by_names"], "regular")

    def test_ajax_create_requires_superuser(self):
        create_url = reverse("main:create_project_ajax")
        self.assertEqual(self.client.post(create_url, self.project_data()).status_code, 403)

        self.setUpTestUsers()
        self.client.force_login(self.regular)
        self.assertEqual(self.client.post(create_url, self.project_data()).status_code, 403)

    def test_ajax_create_saves_sanitized_project_for_owner(self):
        self.setUpTestUsers()
        self.client.force_login(self.owner)
        payload = self.project_data(title="<b>New Project</b>")
        payload["description"] = "<p>Project details</p>"
        payload["tech_stack"] = "<i>Django</i>"

        response = self.client.post(reverse("main:create_project_ajax"), payload)

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response["Content-Type"].startswith("application/json"))
        project = Project.objects.get(pk=response.json()["pk"])
        self.assertEqual(project.title, "New Project")
        self.assertEqual(project.description, "Project details")
        self.assertEqual(project.tech_stack, "Django")

    def test_ajax_create_rejects_title_that_is_only_html(self):
        self.setUpTestUsers()
        self.client.force_login(self.owner)
        payload = self.project_data(title='<img src="x" onerror="alert(1)">')

        response = self.client.post(reverse("main:create_project_ajax"), payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["errors"])
        self.assertFalse(Project.objects.exclude(pk=self.project.pk).exists())

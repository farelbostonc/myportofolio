import uuid
from django.test import Client, TestCase
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

    def test_education_page_renders_ajax_container(self):
        response = self.client.get(
            reverse("main:show_education")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="education-grid"')
        self.assertContains(response, reverse("main:get_education_json"))
        self.assertNotContains(response, self.education.title)

        data = self.client.get(reverse("main:get_education_json")).json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["pk"], str(self.education.pk))
        self.assertEqual(data[0]["fields"]["title"], self.education.title)
        self.assertEqual(data[0]["fields"]["description"], self.education.description)
        self.assertEqual(data[0]["fields"]["start_year"], self.education.start_year)
        self.assertEqual(data[0]["fields"]["end_year"], self.education.end_year)

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
        self.assertEqual(
            self.client.get(reverse("main:get_education_json")).json(),
            [],
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


class EducationAjaxTest(TestCase):
    def setUp(self):
        self.education = Education.objects.create(
            title="S1 Sistem Informasi",
            description="Fakultas Ilmu Komputer, Universitas Indonesia",
            start_year="2025",
            end_year="Present",
        )

        self.regular = User.objects.create_user(
            username="regular_ajax",
            password="test-password",
        )

        self.editor = User.objects.create_user(
            username="editor_ajax",
            password="test-password",
        )
        editor_group, _ = Group.objects.get_or_create(name="Editor")
        self.editor.groups.add(editor_group)

        self.owner = User.objects.create_superuser(
            username="owner_ajax",
            email="owner_ajax@example.com",
            password="test-password",
        )

    def education_data(self, **overrides):
        data = {
            "title": "SMA Negeri 5 Bogor",
            "description": "Mathematics and Natural Sciences",
            "start_year": "2021",
            "end_year": "2024",
        }
        data.update(overrides)
        return data

    def test_education_json_list(self):
        self.education.starred_by.add(self.regular)

        response = self.client.get(reverse("main:get_education_json"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response["Content-Type"].startswith("application/json")
        )

        data = response.json()
        self.assertEqual(len(data), 1)

        item = data[0]
        self.assertEqual(item["pk"], str(self.education.pk))
        self.assertEqual(
            item["fields"]["title"], self.education.title
        )
        self.assertEqual(
            item["fields"]["description"], self.education.description
        )
        self.assertEqual(
            item["fields"]["start_year"], self.education.start_year
        )
        self.assertEqual(
            item["fields"]["end_year"], self.education.end_year
        )
        self.assertEqual(item["fields"]["star_count"], 1)

        # Guest tidak dianggap memberi star.
        self.assertFalse(item["fields"]["is_starred"])

        self.client.force_login(self.regular)
        response = self.client.get(reverse("main:get_education_json"))

        self.assertEqual(response.status_code, 200)
        item = response.json()[0]
        self.assertTrue(item["fields"]["is_starred"])
        self.assertEqual(item["fields"]["star_count"], 1)

    def test_education_json_search(self):
        Education.objects.create(
            title="SMA Negeri 5 Bogor",
            description="Sekolah menengah di Bogor",
            start_year="2021",
            end_year="2024",
        )
        url = reverse("main:get_education_json")

        response = self.client.get(url, {"title": "Sistem"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(
            data[0]["fields"]["title"], "S1 Sistem Informasi"
        )

        # Kata ini hanya terdapat pada description.
        response = self.client.get(url, {"title": "menengah"})

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(
            data[0]["fields"]["title"], "SMA Negeri 5 Bogor"
        )

        response = self.client.get(
            url, {"title": "pendidikan-tidak-ditemukan"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_education_json_accessible_for_all_roles(self):
        url = reverse("main:get_education_json")

        self.assertEqual(self.client.get(url).status_code, 200)

        for user in (self.regular, self.editor, self.owner):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.client.get(url).status_code, 200)
                self.client.logout()

    def test_create_education_ajax_access_by_role(self):
        url = reverse("main:create_education_ajax")
        payload = self.education_data()
        initial_count = Education.objects.count()

        # Guest
        response = self.client.post(url, payload)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Education.objects.count(), initial_count)

        # Regular dan Editor
        for user in (self.regular, self.editor):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.post(url, payload)

                self.assertEqual(response.status_code, 403)
                self.assertEqual(
                    Education.objects.count(), initial_count
                )
                self.client.logout()

        # Owner
        self.client.force_login(self.owner)
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Education.objects.count(), initial_count + 1)
        self.assertTrue(
            Education.objects.filter(
                title="SMA Negeri 5 Bogor"
            ).exists()
        )

    def test_create_education_ajax_success(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("main:create_education_ajax"),
            self.education_data(),
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            response["Content-Type"].startswith("application/json")
        )

        body = response.json()
        self.assertIn("pk", body)
        self.assertIn("message", body)

        education = Education.objects.get(pk=body["pk"])

        self.assertEqual(education.title, "SMA Negeri 5 Bogor")
        self.assertEqual(
            education.description, "Mathematics and Natural Sciences"
        )
        self.assertEqual(education.start_year, "2021")
        self.assertEqual(education.end_year, "2024")

    def test_create_education_ajax_validation_error(self):
        self.client.force_login(self.owner)
        initial_count = Education.objects.count()

        response = self.client.post(
            reverse("main:create_education_ajax"),
            self.education_data(title="", description=""),
        )

        self.assertEqual(response.status_code, 400)
        errors = response.json()["errors"]
        self.assertIn("title", errors)
        self.assertIn("description", errors)
        self.assertEqual(Education.objects.count(), initial_count)

    def test_create_education_ajax_sanitizes_xss(self):
        self.client.force_login(self.owner)

        payload = self.education_data(
            title=(
                'S1 Sistem Informasi '
                '<img src="x" onerror="alert(1)">'
            ),
            description="<b>Fasilkom UI</b>",
            start_year="<i>2025</i>",
            end_year="<strong>Present</strong>",
        )

        response = self.client.post(
            reverse("main:create_education_ajax"),
            payload,
        )

        self.assertEqual(response.status_code, 201)
        education = Education.objects.get(pk=response.json()["pk"])

        self.assertEqual(education.title, "S1 Sistem Informasi")
        self.assertEqual(education.description, "Fasilkom UI")
        self.assertEqual(education.start_year, "2025")
        self.assertEqual(education.end_year, "Present")
        self.assertNotIn("onerror", education.title)
        self.assertNotIn("<", education.description)

    def test_create_education_rejects_xss_only_input(self):
        self.client.force_login(self.owner)
        initial_count = Education.objects.count()

        response = self.client.post(
            reverse("main:create_education_ajax"),
            self.education_data(
                title='<img src="x" onerror="alert(1)">'
            ),
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("title", response.json()["errors"])
        self.assertEqual(Education.objects.count(), initial_count)

    def test_guest_cannot_star_education(self):
        response = self.client.post(
            reverse(
                "main:toggle_education_star_ajax",
                args=[self.education.pk],
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.education.starred_by.count(), 0)

    def test_education_star_toggle(self):
        self.client.force_login(self.regular)

        url = reverse(
            "main:toggle_education_star_ajax",
            args=[self.education.pk],
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["is_starred"])
        self.assertEqual(response.json()["star_count"], 1)
        self.assertTrue(
            self.education.starred_by.filter(
                pk=self.regular.pk
            ).exists()
        )

        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["is_starred"])
        self.assertEqual(response.json()["star_count"], 0)
        self.assertFalse(
            self.education.starred_by.filter(
                pk=self.regular.pk
            ).exists()
        )

    def test_authenticated_roles_can_star(self):
        url = reverse(
            "main:toggle_education_star_ajax",
            args=[self.education.pk],
        )

        for expected_count, user in enumerate(
            (self.regular, self.editor, self.owner), start=1
        ):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.post(url)

                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.json()["is_starred"])
                self.assertEqual(
                    response.json()["star_count"], expected_count
                )
                self.assertTrue(
                    self.education.starred_by.filter(
                        pk=user.pk
                    ).exists()
                )
                self.client.logout()

    def test_delete_education_ajax_access_by_role(self):
        url = reverse(
            "main:delete_education_ajax",
            args=[self.education.pk],
        )

        # Guest
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Education.objects.filter(pk=self.education.pk).exists()
        )

        # Regular dan Editor
        for user in (self.regular, self.editor):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.post(url)

                self.assertEqual(response.status_code, 403)
                self.assertTrue(
                    Education.objects.filter(
                        pk=self.education.pk
                    ).exists()
                )
                self.client.logout()

        # Owner
        self.client.force_login(self.owner)
        response = self.client.post(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())
        self.assertFalse(
            Education.objects.filter(pk=self.education.pk).exists()
        )

    def test_education_ajax_not_found(self):
        missing_id = uuid.uuid4()

        self.client.force_login(self.regular)
        star_response = self.client.post(
            reverse(
                "main:toggle_education_star_ajax",
                args=[missing_id],
            )
        )

        self.assertEqual(star_response.status_code, 404)

        self.client.logout()
        self.client.force_login(self.owner)
        delete_response = self.client.post(
            reverse(
                "main:delete_education_ajax",
                args=[missing_id],
            )
        )

        self.assertEqual(delete_response.status_code, 404)

    def test_education_ajax_http_methods(self):
        response = self.client.post(
            reverse("main:get_education_json")
        )
        self.assertEqual(response.status_code, 405)

        response = self.client.get(
            reverse("main:create_education_ajax")
        )
        self.assertEqual(response.status_code, 405)

        response = self.client.get(
            reverse(
                "main:toggle_education_star_ajax",
                args=[self.education.pk],
            )
        )
        self.assertEqual(response.status_code, 405)

        response = self.client.get(
            reverse(
                "main:delete_education_ajax",
                args=[self.education.pk],
            )
        )
        self.assertEqual(response.status_code, 405)

    def test_create_education_ajax_csrf(self):
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.owner)

        url = reverse("main:create_education_ajax")
        payload = self.education_data()
        initial_count = Education.objects.count()

        # POST tanpa token harus ditolak middleware.
        response = csrf_client.post(url, payload)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Education.objects.count(), initial_count)

        # Halaman Education menyediakan cookie CSRF.
        page = csrf_client.get(reverse("main:show_education"))

        self.assertEqual(page.status_code, 200)
        self.assertIn("csrftoken", csrf_client.cookies)

        csrf_token = csrf_client.cookies["csrftoken"].value

        response = csrf_client.post(
            url,
            payload,
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Education.objects.count(), initial_count + 1)

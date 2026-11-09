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
        self.assertContains(response, reverse("api:education-list"))
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


from rest_framework.test import APIClient, APITestCase
import uuid
from django.contrib.auth.models import Group, User

class EducationAPITest(APITestCase):

    def setUp(self):
        self.owner = User.objects.create_superuser('education-owner', 'owner@example.com', 'test-password')
        self.visitor = User.objects.create_user('education-visitor', password='test-password')
        self.editor = User.objects.create_user('education-editor', password='test-password')
        self.editor.groups.add(Group.objects.create(name='Editor'))
        self.staff = User.objects.create_user('education-staff', password='test-password', is_staff=True)
        self.payload = {'title': 'S1 Sistem Informasi', 'description': 'Universitas Indonesia', 'start_year': '2025', 'end_year': 'Present'}
        self.education = Education.objects.create(**self.payload)
        self.list_url = reverse('api:education-list')
        self.detail_url = reverse('api:education-detail', args=[self.education.pk])
        self.star_url = reverse('api:education-star', args=[self.education.pk])

    def test_public_reads_search_and_empty(self):
        for user in (None, self.visitor, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            response = self.client.get(self.list_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data[0]['id'], str(self.education.pk))
            self.assertNotIn('fields', response.data[0])
            self.assertEqual(self.client.get(self.detail_url).status_code, 200)
        for query in ('SISTEM', 'indonesia'):
            self.assertEqual(len(self.client.get(self.list_url, {'title': query}).data), 1)
        self.assertEqual(self.client.get(self.list_url, {'title': 'missing'}).data, [])

    def education_state(self):
        return (
            list(Education.objects.order_by("pk").values()),
            list(Education.starred_by.through.objects.order_by("pk").values()),
        )

    def test_role_permissions(self):
        self.education.starred_by.add(self.visitor)
        before = self.education_state()
        for user in (None, self.visitor, self.staff, self.editor):
            self.client.force_authenticate(user=user)
            methods = ("post", "delete") if user == self.editor else (
                "post", "put", "patch", "delete",
            )
            for method in methods:
                with self.subTest(user=user, method=method):
                    url = self.list_url if method == "post" else self.detail_url
                    payload = {**self.payload, "title": "Forbidden"}
                    response = getattr(self.client, method)(url, payload, format="json")
                    self.assertEqual(response.status_code, 403)
                    self.assertEqual(self.education_state(), before)

    def test_editor_can_patch_and_put(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(self.detail_url, {'title': 'Updated'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.education.refresh_from_db()
        self.assertEqual(self.education.title, 'Updated')
        self.assertEqual(self.education.description, self.payload['description'])
        self.assertEqual(self.client.put(self.detail_url, {'title': 'Incomplete'}, format='json').status_code, 400)
        self.assertEqual(self.client.put(self.detail_url, self.payload, format='json').status_code, 200)

    def test_star_uses_current_account(self):
        self.assertEqual(self.client.post(self.star_url).status_code, 403)
        for user in (self.visitor, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            response = self.client.post(self.star_url, {'user': self.staff.pk}, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data['is_starred'])
            self.assertEqual(response.data['star_count'], 1)
            self.assertTrue(self.education.starred_by.filter(pk=user.pk).exists())
            self.assertFalse(self.education.starred_by.filter(pk=self.staff.pk).exists())
            self.assertFalse(self.client.post(self.star_url).data['is_starred'])

    def test_missing_and_wrong_methods(self):
        self.assertEqual(self.client.get(reverse('api:education-detail', args=[uuid.uuid4()])).status_code, 404)
        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.delete(self.list_url).status_code, 405)
        self.assertEqual(self.client.get(self.star_url).status_code, 405)
        self.assertEqual(self.client.post(reverse('api:education-star', args=[uuid.uuid4()])).status_code, 404)
        for method in ('head', 'options'):
            self.assertEqual(getattr(self.client, method)(self.list_url).status_code, 200)
        self.assertEqual(Education.objects.count(), 1)

    def test_text_fields_reject_empty_input_without_changing_data(self):
        self.client.force_authenticate(user=self.owner)
        for field in self.payload:
            for value in ("", "   ", '<img src="x" onerror="alert(1)">', "<b> </b>"):
                for method in ("post", "put", "patch"):
                    with self.subTest(field=field, value=value, method=method):
                        payload = {field: value} if method == "patch" else {
                            **self.payload, field: value,
                        }
                        url = self.list_url if method == "post" else self.detail_url
                        response = getattr(self.client, method)(url, payload, format="json")
                        self.assertEqual(response.status_code, 400)
                        self.assertIn(field, response.data)
                        self.assertEqual(Education.objects.count(), 1)
                        self.education.refresh_from_db()
                        for name, expected in self.payload.items():
                            self.assertEqual(getattr(self.education, name), expected)

    def test_create_sanitizes_all_text_fields(self):
        self.client.force_authenticate(user=self.owner)
        payload = {
            name: f"  <b>{value}</b>  " for name, value in self.payload.items()
        }
        response = self.client.post(self.list_url, payload, format="json")
        self.assertEqual(response.status_code, 201)
        education = Education.objects.get(pk=response.data["id"])
        for name, expected in self.payload.items():
            self.assertEqual(response.data[name], expected)
            self.assertEqual(getattr(education, name), expected)

    def test_patch_sanitizes_each_field_and_preserves_omitted_fields(self):
        self.client.force_authenticate(user=self.editor)
        expected = dict(self.payload)
        for name, value in self.payload.items():
            with self.subTest(field=name):
                cleaned = f"{value} updated"
                response = self.client.patch(
                    self.detail_url, {name: f"  <b>{cleaned}</b>  "}, format="json",
                )
                self.assertEqual(response.status_code, 200)
                expected[name] = cleaned
                self.education.refresh_from_db()
                for field, field_value in expected.items():
                    self.assertEqual(response.data[field], field_value)
                    self.assertEqual(getattr(self.education, field), field_value)

    def test_put_sanitizes_all_text_fields(self):
        self.client.force_authenticate(user=self.editor)
        expected = {**self.payload, "title": "S2 Sistem Informasi"}
        payload = {name: f"  <b>{value}</b>  " for name, value in expected.items()}
        response = self.client.put(self.detail_url, payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.education.refresh_from_db()
        for name, value in expected.items():
            self.assertEqual(response.data[name], value)
            self.assertEqual(getattr(self.education, name), value)

    def test_owner_can_create_education(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Education.objects.count(), 2)
        created = Education.objects.get(pk=response.data["id"])
        self.assertNotEqual(created.pk, self.education.pk)
        for field, value in self.payload.items():
            self.assertEqual(getattr(created, field), value)
            self.assertEqual(response.data[field], value)

    def test_owner_can_update_without_changing_stars(self):
        self.education.starred_by.add(self.visitor)
        self.client.force_authenticate(user=self.owner)
        expected = dict(self.payload)
        for method, payload in (
            ("patch", {"title": "Updated program"}),
            ("put", {**self.payload, "description": "Updated institution"}),
        ):
            with self.subTest(method=method):
                response = getattr(self.client, method)(self.detail_url, payload, format="json")
                self.assertEqual(response.status_code, 200)
                expected.update(payload)
                self.education.refresh_from_db()
                for field, value in expected.items():
                    self.assertEqual(getattr(self.education, field), value)
                    self.assertEqual(response.data[field], value)
                self.assertEqual(Education.objects.count(), 1)
                self.assertEqual(list(self.education.starred_by.all()), [self.visitor])

    def test_owner_delete_removes_only_target_and_its_stars(self):
        other = Education.objects.create(**{**self.payload, "title": "Other program"})
        self.education.starred_by.add(self.visitor)
        other.starred_by.add(self.editor)
        self.client.force_authenticate(user=self.owner)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.assertFalse(Education.objects.filter(pk=self.education.pk).exists())
        self.assertFalse(Education.starred_by.through.objects.filter(
            education_id=self.education.pk,
        ).exists())
        self.assertEqual(Education.objects.count(), 1)
        other.refresh_from_db()
        self.assertEqual(other.title, "Other program")
        self.assertEqual(list(other.starred_by.all()), [self.editor])
        self.assertTrue(User.objects.filter(pk=self.visitor.pk).exists())

    def test_missing_detail_returns_404_without_changing_data(self):
        self.education.starred_by.add(self.visitor)
        self.client.force_authenticate(user=self.owner)
        url = reverse("api:education-detail", args=[uuid.uuid4()])
        before = self.education_state()
        for method in ("get", "put", "patch", "delete"):
            with self.subTest(method=method):
                if method == "get":
                    response = self.client.get(url)
                else:
                    response = getattr(self.client, method)(url, self.payload, format="json")
                self.assertEqual(response.status_code, 404)
                self.assertEqual(self.education_state(), before)

    def test_safe_methods_preserve_education_and_stars_for_all_roles(self):
        self.education.starred_by.add(self.visitor)
        before = self.education_state()
        for user in (None, self.visitor, self.editor, self.owner):
            self.client.force_authenticate(user=user)
            for url in (self.list_url, self.detail_url):
                for method in ("get", "head", "options"):
                    with self.subTest(user=user, url=url, method=method):
                        response = getattr(self.client, method)(url)
                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(self.education_state(), before)

    def session_client(self, user):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username=user.username, password="test-password"))
        response = client.get(reverse("main:show_education"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", client.cookies)
        return client, client.cookies["csrftoken"].value

    def test_session_writes_require_csrf_for_every_allowed_role(self):
        self.education.starred_by.add(self.staff)
        before = self.education_state()
        for user in (self.visitor, self.editor, self.owner):
            client, token = self.session_client(user)
            actions = [("post", self.star_url, {})]
            if user in (self.editor, self.owner):
                actions.extend([
                    ("put", self.detail_url, self.payload),
                    ("patch", self.detail_url, {"title": "Changed"}),
                ])
            if user == self.owner:
                actions.extend([
                    ("post", self.list_url, self.payload),
                    ("delete", self.detail_url, {}),
                ])
            for method, url, payload in actions:
                for headers in ({}, {"HTTP_X_CSRFTOKEN": "invalid-token"}):
                    with self.subTest(user=user.username, method=method, url=url, headers=headers):
                        response = getattr(client, method)(url, payload, format="json", **headers)
                        self.assertEqual(response.status_code, 403)
                        self.assertIn("CSRF", str(response.data["detail"]))
                        self.assertEqual(self.education_state(), before)

    def test_owner_session_crud_with_valid_csrf(self):
        client, token = self.session_client(self.owner)
        headers = {"HTTP_X_CSRFTOKEN": token}
        response = client.post(self.list_url, self.payload, format="json", **headers)
        self.assertEqual(response.status_code, 201)
        created_id = response.data["id"]
        self.assertTrue(Education.objects.filter(pk=created_id).exists())
        url = reverse("api:education-detail", args=[created_id])
        for method in ("put", "patch"):
            payload = {**self.payload, "title": method}
            response = getattr(client, method)(url, payload, format="json", **headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Education.objects.get(pk=created_id).title, method)
        response = client.delete(url, **headers)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Education.objects.filter(pk=created_id).exists())
        self.assertTrue(Education.objects.filter(pk=self.education.pk).exists())

    def test_editor_session_update_with_valid_csrf(self):
        client, token = self.session_client(self.editor)
        for method in ("put", "patch"):
            with self.subTest(method=method):
                response = getattr(client, method)(
                    self.detail_url, {**self.payload, "title": method},
                    format="json", HTTP_X_CSRFTOKEN=token,
                )
                self.assertEqual(response.status_code, 200)
                self.education.refresh_from_db()
                self.assertEqual(self.education.title, method)
        before = self.education_state()
        for method, url in (("post", self.list_url), ("delete", self.detail_url)):
            response = getattr(client, method)(
                url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(self.education_state(), before)

    def test_session_star_ignores_forged_account_and_preserves_other_stars(self):
        self.education.starred_by.add(self.staff)
        forged = {"user": self.staff.pk, "user_id": self.staff.pk,
                  "starred_by": [self.staff.pk], "star_count": 99, "is_starred": False}
        for user in (self.visitor, self.editor, self.owner):
            client, token = self.session_client(user)
            for expected_starred, expected_count in ((True, 2), (False, 1)):
                with self.subTest(user=user.username, starred=expected_starred):
                    response = client.post(
                        self.star_url, forged, format="json", HTTP_X_CSRFTOKEN=token,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data["is_starred"], expected_starred)
                    self.assertEqual(response.data["star_count"], expected_count)
                    self.assertEqual(self.education.starred_by.filter(pk=user.pk).exists(), expected_starred)
                    self.assertTrue(self.education.starred_by.filter(pk=self.staff.pk).exists())
                    self.assertEqual(self.education.starred_by.count(), expected_count)

    def test_guest_cannot_forge_star_account(self):
        self.education.starred_by.add(self.staff)
        before = self.education_state()
        response = self.client.post(self.star_url, {"user": self.owner.pk}, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.education_state(), before)

    def test_create_ignores_client_supplied_star_fields(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.list_url, {
            **self.payload, "star_count": 99, "is_starred": True,
            "starred_by": [self.visitor.pk],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(Education.objects.get(pk=response.data["id"]).starred_by.count(), 0)

    def test_updates_cannot_overwrite_star_fields(self):
        self.education.starred_by.add(self.owner, self.visitor)
        for user in (self.owner, self.editor):
            self.client.force_authenticate(user=user)
            expected_starred = user == self.owner
            for method in ("put", "patch"):
                with self.subTest(user=user.username, method=method):
                    response = getattr(self.client, method)(self.detail_url, {
                        **self.payload, "star_count": 99,
                        "is_starred": not expected_starred, "starred_by": [self.staff.pk],
                    }, format="json")
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.data["star_count"], 2)
                    self.assertEqual(response.data["is_starred"], expected_starred)
                    self.assertSetEqual(set(self.education.starred_by.values_list("pk", flat=True)),
                                        {self.owner.pk, self.visitor.pk})

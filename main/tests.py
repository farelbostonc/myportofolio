from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from main.models import Education, Experience, Project


@override_settings(PORTFOLIO_EDIT_KEYS=["ZmFyZWw=", "Ym9zdG9u"])
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

    def test_create_experience_rejects_invalid_edit_key(self):
        response = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "Security Intern",
                "description": "Belajar keamanan aplikasi.",
                "category": "internship",
                "thumbnail": "",
                "ended_at": "",
                "access_key": "wrong-key",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kode rahasia admin tidak valid.")
        self.assertFalse(Experience.objects.filter(title="Security Intern").exists())

    def test_create_experience_accepts_first_edit_key(self):
        response = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "Security Intern",
                "description": "Belajar keamanan aplikasi.",
                "category": "internship",
                "thumbnail": "",
                "ended_at": "",
                "access_key": "ZmFyZWw=",
            },
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertTrue(Experience.objects.filter(title="Security Intern").exists())

    def test_create_education_accepts_second_edit_key(self):
        response = self.client.post(
            reverse("main:create_education"),
            {
                "title": "Security Course",
                "description": "Kursus keamanan siber.",
                "start_year": "2026",
                "end_year": "2026",
                "access_key": "Ym9zdG9u",
            },
        )

        self.assertRedirects(response, reverse("main:show_education"))
        self.assertTrue(Education.objects.filter(title="Security Course").exists())

    def test_project_create_rejects_invalid_edit_key(self):
        response = self.client.post(
            reverse("main:create_project"),
            {
                "title": "Unauthorized Project",
                "description": "Tidak boleh tersimpan.",
                "tech_stack": "Django",
                "project_url": "",
                "project_image_url": "",
                "access_key": "wrong-key",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Project.objects.filter(title="Unauthorized Project").exists())

    def test_project_delete_requires_valid_edit_key(self):
        delete_url = reverse("main:delete_project", args=[self.project.id])

        response = self.client.post(delete_url, {"access_key": "wrong-key"})
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(Project.objects.filter(pk=self.project.id).exists())

        response = self.client.post(delete_url, {"access_key": "ZmFyZWw="})
        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertFalse(Project.objects.filter(pk=self.project.id).exists())

    def test_experience_delete_requires_valid_admin_code(self):
        delete_url = reverse("main:delete_experience", args=[self.experience.id])

        response = self.client.post(delete_url, {"access_key": "wrong-key"})
        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertTrue(Experience.objects.filter(pk=self.experience.id).exists())

        response = self.client.post(delete_url, {"access_key": "Ym9zdG9u"})
        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertFalse(Experience.objects.filter(pk=self.experience.id).exists())

    def test_education_delete_requires_valid_admin_code(self):
        delete_url = reverse("main:delete_education", args=[self.education.id])

        response = self.client.post(delete_url, {"access_key": "wrong-key"})
        self.assertRedirects(response, reverse("main:show_education"))
        self.assertTrue(Education.objects.filter(pk=self.education.id).exists())

        response = self.client.post(delete_url, {"access_key": "ZmFyZWw="})
        self.assertRedirects(response, reverse("main:show_education"))
        self.assertFalse(Education.objects.filter(pk=self.education.id).exists())

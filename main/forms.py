from django.core.exceptions import ValidationError
from django.forms import DateTimeInput, ModelForm, TextInput, Textarea, URLInput
from django.utils.html import strip_tags

from main.models import Education, Experience, Project


class ProjectForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "tech_stack",
            "project_url",
            "project_image_url",
        ]

        labels = {
            "title": "Nama Proyek",
            "description": "Deskripsi Proyek",
            "tech_stack": "Teknologi yang Digunakan",
            "project_url": "URL Proyek",
            "project_image_url": "URL Gambar Proyek",
        }

        widgets = {
            "title": TextInput(
                attrs={
                    "placeholder": "Portfolio Website",
                    "maxlength": 255,
                }
            ),
            "description": Textarea(
                attrs={
                    "placeholder": "Ceritakan Proyekmu",
                    "rows": 3,
                }
            ),
            "tech_stack": TextInput(
                attrs={
                    "placeholder": "Django, Python, HTML, CSS",
                }
            ),
            "project_url": URLInput(
                attrs={
                    "placeholder": "https://github.com/kakBurhan/burhanquestv4",
                }
            ),
            "project_image_url": URLInput(
                attrs={
                    "placeholder": "https://drive.google.com/thumbnail?id=...&sz=w1000",
                }
            ),
        }

    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Nama proyek tidak boleh hanya berisi tag HTML.")
        return title

    def clean_tech_stack(self):
        return strip_tags(self.cleaned_data["tech_stack"]).strip()

    def clean_description(self):
        return strip_tags(self.cleaned_data["description"]).strip()


class ExperienceForm(ModelForm):
    class Meta:
        model = Experience
        fields = [
            "title",
            "description",
            "category",
            "thumbnail",
            "ended_at",
        ]
        labels = {
            "title": "Posisi atau Kegiatan",
            "description": "Deskripsi",
            "category": "Kategori",
            "thumbnail": "URL Gambar",
            "ended_at": "Waktu Selesai",
        }
        widgets = {
            "title": TextInput(attrs={"placeholder": "Contoh: Asisten Laboratorium"}),
            "description": Textarea(
                attrs={"placeholder": "Ceritakan pengalamanmu", "rows": 4}
            ),
            "thumbnail": URLInput(attrs={"placeholder": "https://..."}),
            "ended_at": DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
        }


class EducationForm(ModelForm):
    class Meta:
        model = Education
        fields = ["title", "description", "start_year", "end_year"]
        labels = {
            "title": "Program Pendidikan",
            "description": "Institusi atau Deskripsi",
            "start_year": "Tahun Mulai",
            "end_year": "Tahun Selesai",
        }
        widgets = {
            "title": TextInput(attrs={"placeholder": "Contoh: S1 Sistem Informasi"}),
            "description": Textarea(
                attrs={
                    "placeholder": "Contoh: Fakultas Ilmu Komputer, Universitas Indonesia",
                    "rows": 4,
                }
            ),
            "start_year": TextInput(attrs={"placeholder": "2025"}),
            "end_year": TextInput(attrs={"placeholder": "Present"}),
        }

    def _clean_text(self, field_name):
        value = strip_tags(self.cleaned_data[field_name]).strip()
        if not value:
            raise ValidationError(
                "Kolom ini tidak boleh kosong atau hanya berisi tag HTML.",
                code="required",
            )
        return value

    def clean_title(self):
        return self._clean_text("title")

    def clean_description(self):
        return self._clean_text("description")

    def clean_start_year(self):
        return self._clean_text("start_year")

    def clean_end_year(self):
        return self._clean_text("end_year")

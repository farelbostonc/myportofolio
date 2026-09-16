import hmac

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.forms import DateTimeInput, ModelForm, PasswordInput, TextInput, Textarea, URLInput

from main.models import Education, Experience, Project


def edit_key_is_valid(submitted_key):
    configured_keys = settings.PORTFOLIO_EDIT_KEYS
    if not configured_keys or not submitted_key:
        return False
    return any(
        hmac.compare_digest(str(submitted_key), str(configured_key))
        for configured_key in configured_keys
    )


class ProtectedModelForm(ModelForm):
    access_key = forms.CharField(
        label="Kode Rahasia Admin",
        strip=False,
        widget=PasswordInput(
            attrs={
                "placeholder": "Masukkan kode rahasia admin",
                "autocomplete": "current-password",
            }
        ),
        help_text="Kode rahasia admin diperlukan untuk menyimpan perubahan.",
    )

    def clean_access_key(self):
        access_key = self.cleaned_data["access_key"]
        if not settings.PORTFOLIO_EDIT_KEYS:
            raise ValidationError("Kode rahasia admin belum dikonfigurasi di server.")
        if not edit_key_is_valid(access_key):
            raise ValidationError("Kode rahasia admin tidak valid.")
        return access_key


class ProjectForm(ProtectedModelForm):
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


class ExperienceForm(ProtectedModelForm):
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


class EducationForm(ProtectedModelForm):
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

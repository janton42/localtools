from django.db import models


class WorkType(models.TextChoices):
    BOOK_CHAPTER = 'book_chapter', 'Book Chapter'
    ARTICLE = 'article', 'Article'
    THESIS = 'thesis', 'Thesis'
    DISSERTATION = 'dissertation', 'Dissertation'
    CONFERENCE_PAPER = 'conference_paper', 'Conference Paper'
    ESSAY = 'essay', 'Essay'
    OTHER = 'other', 'Other'


class Work(models.Model):
    title = models.CharField(max_length=300)
    work_type = models.CharField(max_length=50, choices=WorkType.choices, default=WorkType.OTHER)
    link = models.URLField(blank=True)
    author_first_name = models.CharField(max_length=100)
    author_last_name = models.CharField(max_length=100)
    institution = models.CharField(max_length=200, blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['author_last_name', 'author_first_name']

    def __str__(self):
        return f"{self.title} — {self.author_last_name}, {self.author_first_name}"


class Applicant(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    institution = models.CharField(max_length=200, blank=True)
    work = models.OneToOneField(Work, on_delete=models.CASCADE, related_name='applicant')
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.email})"

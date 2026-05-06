from django.db import models
from django.urls import reverse, NoReverseMatch


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='portfolio/images/', blank=True, null=True)
    link = models.CharField(max_length=2000, blank=True)
    internal_url_name = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField('Tag', blank=True)
    project_date = models.DateField(null=True, blank=True)
    github_url = models.URLField(blank=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('portfolio:detail', kwargs={'slug': self.slug})

    def get_project_url(self):
        if self.internal_url_name:
            try:
                return reverse(self.internal_url_name)
            except NoReverseMatch:
                return None
        return self.link or None
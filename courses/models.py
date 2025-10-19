from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
import os

User = get_user_model()


def get_lesson_upload_path(instance, filename):
    return f"lessons/{instance.course.id}/{filename}"


def get_certificate_upload_path(instance, filename):
    return f"certificates/{instance.enrollment.id}_{instance.enrollment.student.username}.pdf"


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.name.lower().replace(" ", "-")
        super().save(*args, **kwargs)


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    instructor = models.ForeignKey(
        User, on_delete=models.CASCADE, limit_choices_to={"user_type": "instructor"}
    )
    thumbnail = models.ImageField(upload_to="course_thumbnails/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration = models.CharField(
        max_length=50, blank=True, help_text="e.g., 12 weeks, 2 months"
    )
    level = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Beginner"),
            ("intermediate", "Intermediate"),
            ("advanced", "Advanced"),
        ],
        default="beginner",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.title.lower().replace(" ", "-").replace("/", "-")
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("course_detail", kwargs={"slug": self.slug})

    @property
    def total_lessons(self):
        return self.lessons.count()

    @property
    def enrollments_count(self):
        return self.enrollments.count()


class Lesson(models.Model):
    LESSON_TYPE_CHOICES = [
        ("video", "Video"),
        ("pdf", "PDF Document"),
        ("text", "Text Content"),
        ("quiz", "Quiz"),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    slug = models.SlugField(blank=True)
    lesson_type = models.CharField(max_length=20, choices=LESSON_TYPE_CHOICES)
    content_file = models.FileField(
        upload_to=get_lesson_upload_path, blank=True, null=True
    )
    content_text = models.TextField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    duration = models.IntegerField(default=0, help_text="Duration in minutes")
    is_preview = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.title.lower().replace(" ", "-")
        super().save(*args, **kwargs)


class Enrollment(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"user_type": "student"},
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    progress = models.IntegerField(default=0, help_text="Percentage completed")
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ["student", "course"]
        ordering = ["-enrolled_at"]

    def __str__(self):
        return f"{self.student.username} - {self.course.title}"

    def update_progress(self):
        total_lessons = self.course.lessons.count()
        if total_lessons == 0:
            return

        completed_lessons = self.course.lessons.filter(is_completed=True).count()
        self.progress = int((completed_lessons / total_lessons) * 100)
        self.is_completed = self.progress >= 100
        if self.is_completed and not self.completed_at:
            self.completed_at = timezone.now()
        self.save()


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="quizzes", blank=True, null=True
    )
    title = models.CharField(max_length=200)
    instructions = models.TextField(blank=True)
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes")
    total_marks = models.FloatField(default=0)
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def update_total_marks(self):
        """Manually update total marks - call this after creating questions"""
        if self.pk:  # Only if object has been saved
            self.total_marks = sum(q.marks for q in self.questions.all())
            self.save(update_fields=["total_marks"])

    def save(self, *args, **kwargs):
        # Skip automatic total_marks calculation during initial save
        # Only calculate if object already exists in DB
        if self.pk is None:
            # First save - don't calculate total_marks
            super().save(*args, **kwargs)
            # After saving, calculate total_marks if questions exist
            if self.questions.exists():
                self.update_total_marks()
        else:
            # Subsequent saves - calculate total_marks
            try:
                self.total_marks = sum(q.marks for q in self.questions.all())
            except:
                # If can't calculate (no PK or no questions), keep existing value
                pass
            super().save(*args, **kwargs)


class Question(models.Model):
    QUESTION_TYPE_CHOICES = [
        ("mcq", "Multiple Choice"),
        ("true_false", "True/False"),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    marks = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.text[:50]


class Answer(models.Model):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="answers"
    )
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.text


class QuizAttempt(models.Model):
    enrollment = models.ForeignKey(
        Enrollment, on_delete=models.CASCADE, related_name="quiz_attempts"
    )
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    total_marks = models.FloatField(null=True, blank=True)
    is_passed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.enrollment.student.username} - {self.quiz.title}"


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True)
    is_correct = models.BooleanField(null=True, blank=True)


class Certificate(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE)
    certificate_file = models.FileField(upload_to=get_certificate_upload_path)
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate for {self.enrollment.student.username} - {self.enrollment.course.title}"

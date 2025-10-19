from django.contrib import admin
from .models import (
    Category, Course, Lesson, Enrollment,
    Quiz, Question, Answer, QuizAttempt, QuizAnswer, Certificate
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)
    list_per_page = 20


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'category', 'instructor', 'price',
        'level', 'is_published', 'created_at'
    )
    list_filter = ('category', 'level', 'is_published', 'created_at')
    search_fields = ('title', 'description', 'instructor__username')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_published',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 20


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'course', 'lesson_type', 'order',
        'duration', 'is_preview', 'is_completed'
    )
    list_filter = ('lesson_type', 'is_preview', 'is_completed', 'course')
    search_fields = ('title', 'course__title')
    ordering = ('course', 'order')
    list_editable = ('is_preview', 'is_completed')
    list_per_page = 20


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        'student', 'course', 'progress',
        'is_completed', 'enrolled_at', 'completed_at'
    )
    list_filter = ('is_completed', 'enrolled_at')
    search_fields = ('student__username', 'course__title')
    list_editable = ('is_completed',)
    ordering = ('-enrolled_at',)
    list_per_page = 20


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'course', 'time_limit',
        'total_marks', 'is_published', 'created_at'
    )
    list_filter = ('is_published', 'course')
    search_fields = ('title', 'course__title')
    list_editable = ('is_published',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 20


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'question_type', 'marks', 'order')
    list_filter = ('question_type', 'quiz')
    search_fields = ('text', 'quiz__title')
    ordering = ('quiz', 'order')
    list_per_page = 20


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct', 'order')
    list_filter = ('is_correct', 'question')
    search_fields = ('text', 'question__text')
    list_editable = ('is_correct',)
    ordering = ('question', 'order')
    list_per_page = 20


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'enrollment', 'quiz', 'score', 'total_marks',
        'is_passed', 'started_at', 'completed_at'
    )
    list_filter = ('is_passed', 'quiz')
    search_fields = ('enrollment__student__username', 'quiz__title')
    list_editable = ('is_passed',)
    ordering = ('-started_at',)
    list_per_page = 20


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_answer', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('attempt__quiz__title', 'question__text')
    ordering = ('attempt',)
    list_per_page = 20


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'certificate_file', 'issued_at')
    search_fields = (
        'enrollment__student__username',
        'enrollment__course__title'
    )
    date_hierarchy = 'issued_at'
    ordering = ('-issued_at',)
    list_per_page = 20

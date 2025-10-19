from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Course, Enrollment, Lesson, Category
from .forms import CourseForm, LessonForm


def home(request):
    """Home page with featured courses"""
    featured_courses = Course.objects.filter(is_published=True)[:6]
    categories = Category.objects.all()[:8]

    context = {
        "featured_courses": featured_courses,
        "categories": categories,
    }
    return render(request, "courses/home.html", context)


def course_list(request):
    """List all published courses with filtering and pagination"""
    courses = Course.objects.filter(is_published=True)

    # Filtering
    category_id = request.GET.get("category")
    if category_id:
        courses = courses.filter(category_id=category_id)

    level = request.GET.get("level")
    if level:
        courses = courses.filter(level=level)

    search = request.GET.get("search")
    if search:
        courses = courses.filter(
            Q(title__icontains=search) | Q(description__icontains=search)
        )

    # Pagination
    paginator = Paginator(courses, 9)
    page_number = request.GET.get("page")
    courses_page = paginator.get_page(page_number)

    context = {
        "courses": courses_page,
        "categories": Category.objects.all(),
    }
    return render(request, "courses/course_list.html", context)


def course_detail(request, slug):
    """Course detail page"""
    course = get_object_or_404(Course, slug=slug, is_published=True)

    # Check enrollment for students
    enrollment = None
    if request.user.is_authenticated and request.user.user_type == "student":
        enrollment = Enrollment.objects.filter(
            student=request.user, course=course
        ).first()

    context = {
        "course": course,
        "enrollment": enrollment,
        "lessons": course.lessons.all(),
    }
    return render(request, "courses/course_detail.html", context)


@login_required
@require_http_methods(["POST"])
def enroll_course(request, course_id):
    """Enroll student in a course"""
    if request.user.user_type != "student":
        messages.error(request, "Only students can enroll in courses.")
        return redirect("course_list")

    course = get_object_or_404(Course, id=course_id, is_published=True)

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user, course=course
    )

    if created:
        messages.success(request, f'Successfully enrolled in "{course.title}"!')
    else:
        messages.info(request, f'You are already enrolled in "{course.title}".')

    return redirect("course_detail", slug=course.slug)


@login_required
def my_courses(request):
    """Student's enrolled courses"""
    if request.user.user_type != "student":
        messages.error(request, "Only students can view their courses.")
        return redirect("home")

    enrollments = Enrollment.objects.filter(student=request.user).select_related(
        "course"
    )
    context = {"enrollments": enrollments}
    return render(request, "courses/my_courses.html", context)


@login_required
def course_lessons(request, course_id):
    """View course lessons for enrolled students or instructors"""
    course = get_object_or_404(Course, id=course_id, is_published=True)

    if request.user.user_type == "student":
        enrollment = Enrollment.objects.filter(
            student=request.user, course=course
        ).first()
        if not enrollment:
            messages.error(request, "You need to enroll in this course first.")
            return redirect("course_detail", slug=course.slug)
    elif request.user != course.instructor and request.user.user_type != "admin":
        messages.error(request, "Access denied.")
        return redirect("home")

    lessons = course.lessons.all()
    context = {
        "course": course,
        "lessons": lessons,
        "enrollment": getattr(request.user, "enrollment", None),
    }
    return render(request, "courses/course_lessions.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def create_course(request):
    """Create new course (instructors only)"""
    if request.user.user_type != "instructor":
        messages.error(request, "Only instructors can create courses.")
        return redirect("home")

    if request.method == "POST":
        form = CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            course.instructor = request.user
            course.save()
            messages.success(request, "Course created successfully!")
            return redirect("course_detail", slug=course.slug)
    else:
        form = CourseForm()

    return render(
        request, "courses/course_form.html", {"form": form, "action": "Create"}
    )


@login_required
@require_http_methods(["POST"])
def update_lesson_progress(request, lesson_id):
    """Update lesson completion status"""
    if request.user.user_type != "student":
        return JsonResponse({"error": "Unauthorized"}, status=403)

    lesson = get_object_or_404(Lesson, id=lesson_id)
    enrollment = Enrollment.objects.filter(
        student=request.user, course=lesson.course
    ).first()

    if not enrollment:
        return JsonResponse({"error": "Not enrolled"}, status=403)

    # Mark lesson as completed
    lesson.is_completed = True
    lesson.save()

    # Update enrollment progress
    enrollment.update_progress()

    return JsonResponse(
        {
            "success": True,
            "progress": enrollment.progress,
            "completed": enrollment.is_completed,
        }
    )

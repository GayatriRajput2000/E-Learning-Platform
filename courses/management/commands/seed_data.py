import os
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from courses.models import Category, Course, Lesson, Enrollment, Quiz, Question, Answer
from accounts.models import User
import logging

User = get_user_model()

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Create demo data for courses, categories, users, lessons, and enrollments"

    def add_arguments(self, parser):
        parser.add_argument(
            "--categories",
            type=int,
            default=10,
            help="Number of categories to create (default: 10)",
        )
        parser.add_argument(
            "--courses",
            type=int,
            default=50,
            help="Number of courses to create (default: 50)",
        )
        parser.add_argument(
            "--students",
            type=int,
            default=20,
            help="Number of student users to create (default: 20)",
        )
        parser.add_argument(
            "--instructors",
            type=int,
            default=10,
            help="Number of instructor users to create (default: 10)",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Delete existing demo data before creating new data",
        )

    def handle(self, *args, **options):
        categories_count = options["categories"]
        courses_count = options["courses"]
        students_count = options["students"]
        instructors_count = options["instructors"]
        clean = options["clean"]

        self.stdout.write(self.style.SUCCESS(f"Starting demo data creation..."))

        if clean:
            self._clean_demo_data()

        try:
            with transaction.atomic():
                # Create categories
                categories = self._create_categories(categories_count)
                self.stdout.write(
                    self.style.SUCCESS(f"Created {len(categories)} categories")
                )

                # Create users
                instructors = self._create_instructors(instructors_count)
                students = self._create_students(students_count)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created {len(instructors)} instructors and {len(students)} students"
                    )
                )

                # Create courses
                courses = self._create_courses(courses_count, categories, instructors)
                self.stdout.write(self.style.SUCCESS(f"Created {len(courses)} courses"))

                # Create lessons
                lessons_count = self._create_lessons(courses)
                self.stdout.write(
                    self.style.SUCCESS(f"Created {lessons_count} lessons")
                )

                # Create quizzes (FIXED VERSION)
                quizzes_count = self._create_quizzes_fixed(courses)
                self.stdout.write(
                    self.style.SUCCESS(f"Created {quizzes_count} quizzes")
                )

                # Create enrollments
                enrollments_count = self._create_enrollments(students, courses)
                self.stdout.write(
                    self.style.SUCCESS(f"Created {enrollments_count} enrollments")
                )

                # Update progress for some enrollments
                self._update_enrollment_progress(enrollments_count)

            self.stdout.write(
                self.style.SUCCESS("Demo data creation completed successfully!")
            )
            self.stdout.write(
                self.style.WARNING(
                    "Run `python manage.py collectstatic` to serve thumbnails"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating demo data: {str(e)}"))
            logger.error(f"Demo data creation failed: {str(e)}", exc_info=True)
            raise

    def _clean_demo_data(self):
        """Clean existing demo data"""
        self.stdout.write("Cleaning existing demo data...")

        try:
            # Delete in reverse order due to foreign key constraints
            Lesson.objects.all().delete()
            Enrollment.objects.all().delete()
            Quiz.objects.all().delete()
            Question.objects.all().delete()
            Answer.objects.all().delete()
            Course.objects.filter(is_published=False).delete()
            Category.objects.filter(name__startswith="Demo ").delete()
            User.objects.filter(username__startswith="demo_").delete()

            self.stdout.write(self.style.SUCCESS("Cleaned existing demo data"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error cleaning data: {str(e)}"))

    def _create_categories(self, count):
        """Create demo categories"""
        categories_data = [
            ("Demo Python Programming", "Python courses for all levels"),
            ("Demo Web Development", "Frontend and backend web development"),
            ("Demo Data Science", "Machine learning and data analysis"),
            ("Demo Digital Marketing", "SEO, social media, and marketing"),
            ("Demo Graphic Design", "Adobe tools and design principles"),
            ("Demo Mobile Development", "iOS and Android app development"),
            ("Demo Business & Finance", "Management and financial skills"),
            ("Demo AI & Machine Learning", "Artificial intelligence courses"),
            ("Demo Cybersecurity", "Network security and ethical hacking"),
            ("Demo Cloud Computing", "AWS, Azure, and cloud technologies"),
            ("Demo DevOps", "CI/CD pipelines and infrastructure as code"),
            ("Demo Blockchain", "Cryptocurrency and smart contracts"),
        ]

        created_categories = []
        for i in range(min(count, len(categories_data))):
            name, description = categories_data[i]
            category, created = Category.objects.get_or_create(
                name=name, defaults={"description": description}
            )
            if created:
                created_categories.append(category)

        # Create additional generic categories if needed
        for i in range(len(created_categories), count):
            category, created = Category.objects.get_or_create(
                name=f"Demo Category {i+1}",
                defaults={"description": f"Description for category {i+1}"},
            )
            if created:
                created_categories.append(category)

        return created_categories

    def _create_instructors(self, count):
        """Create demo instructors"""
        instructors = []
        for i in range(count):
            instructor = User.objects.create_user(
                username=f"demo_instructor_{i+1}",
                email=f"demo_instructor_{i+1}@edusmart.com",
                first_name=f"Instructor",
                last_name=f"User {i+1}",
                password="demo123",
                user_type="instructor",
            )
            instructor.bio = f"Experienced instructor with {random.randint(5, 15)} years in teaching {random.choice(['Python', 'Web Development', 'Data Science', 'Design'])}"
            instructor.save()
            instructors.append(instructor)

        # Create admin user if doesn't exist
        try:
            admin = User.objects.get(username="admin")
        except User.DoesNotExist:
            admin = User.objects.create_superuser(
                username="admin",
                email="admin@edusmart.com",
                password="admin123",
                user_type="admin",
            )
            admin.first_name = "Admin"
            admin.last_name = "User"
            admin.save()

        return instructors

    def _create_students(self, count):
        """Create demo students"""
        students = []
        for i in range(count):
            student = User.objects.create_user(
                username=f"demo_student_{i+1}",
                email=f"demo_student_{i+1}@edusmart.com",
                first_name=f"Student",
                last_name=f"User {i+1}",
                password="demo123",
                user_type="student",
            )
            students.append(student)
        return students

    def _create_courses(self, count, categories, instructors):
        """Create demo courses"""
        course_data = [
            (
                "Complete Python Bootcamp",
                "Learn Python from scratch to advanced",
                "beginner",
                "12 weeks",
                89.99,
            ),
            (
                "Advanced Web Development",
                "Build modern web applications",
                "intermediate",
                "10 weeks",
                129.99,
            ),
            (
                "Data Science Masterclass",
                "Machine learning and data analysis",
                "intermediate",
                "16 weeks",
                149.99,
            ),
            (
                "Digital Marketing Pro",
                "SEO, PPC, and social media marketing",
                "beginner",
                "8 weeks",
                79.99,
            ),
            (
                "React Native Mobile Apps",
                "Build cross-platform mobile apps",
                "intermediate",
                "6 weeks",
                99.99,
            ),
            (
                "AWS Cloud Practitioner",
                "Amazon Web Services fundamentals",
                "beginner",
                "4 weeks",
                59.99,
            ),
            (
                "UI/UX Design Essentials",
                "Figma and design principles",
                "beginner",
                "8 weeks",
                69.99,
            ),
            (
                "Cybersecurity Fundamentals",
                "Network security basics",
                "beginner",
                "6 weeks",
                89.99,
            ),
            (
                "DevOps Engineering",
                "CI/CD pipelines and automation",
                "intermediate",
                "12 weeks",
                119.99,
            ),
            (
                "Machine Learning Deep Dive",
                "Neural networks and deep learning",
                "advanced",
                "20 weeks",
                199.99,
            ),
        ]

        created_courses = []

        # Create courses from predefined data
        for i, (title, desc, level, duration, price) in enumerate(course_data):
            if i >= len(instructors):
                break

            course = Course.objects.create(
                title=title,
                description=f"{desc}. This comprehensive course covers all essential topics with hands-on projects.",
                short_description=desc,
                category=categories[i % len(categories)],
                instructor=instructors[i % len(instructors)],
                price=price,
                duration=duration,
                level=level,
                is_published=True,
            )
            created_courses.append(course)

        # Create additional random courses
        for i in range(len(created_courses), count):
            course = Course.objects.create(
                title=f"Demo Course {i+1}",
                description=f'Comprehensive course covering various topics in {Course._meta.get_field("level").choices[random.randint(0, 2)][1].lower()} level.',
                short_description=f'Learn essential skills for {Course._meta.get_field("level").choices[random.randint(0, 2)][1].lower()} development',
                category=random.choice(categories),
                instructor=random.choice(instructors),
                price=random.choice([0, 29.99, 49.99, 79.99, 99.99, 129.99]),
                duration=f"{random.randint(4, 16)} weeks",
                level=random.choice(["beginner", "intermediate", "advanced"]),
                is_published=True,
            )
            created_courses.append(course)

        return created_courses

    def _create_lessons(self, courses):
        """Create demo lessons for courses"""
        lesson_types = ["video", "pdf", "text"]
        total_lessons = 0

        for course in courses:
            num_lessons = random.randint(5, 15)
            for i in range(num_lessons):
                lesson_type = random.choice(lesson_types)

                Lesson.objects.create(
                    course=course,
                    title=f"Lesson {i+1}: {lesson_type.title()} Content",
                    lesson_type=lesson_type,
                    order=i + 1,
                    duration=random.randint(5, 60),
                    is_preview=(i == 0),  # First lesson is preview
                    content_text=f"Demo content for {lesson_type} lesson {i+1} of {course.title}. This lesson covers important concepts and practical examples.",
                    is_completed=random.choice([True, False]),
                )
                total_lessons += 1

        return total_lessons

    def _create_quizzes_fixed(self, courses):
        """Create demo quizzes with fixed Quiz model"""
        total_quizzes = 0

        for course in courses:
            num_quizzes = random.randint(1, 3)
            for i in range(num_quizzes):
                # Step 1: Create quiz (total_marks will be 0 initially)
                quiz = Quiz.objects.create(
                    course=course,
                    title=f"Quiz {i+1}: {course.title[:30]} Assessment",
                    instructions="Answer all questions to test your understanding",
                    time_limit=random.randint(15, 45),
                    is_published=True,
                )

                # Step 2: Create questions and answers
                num_questions = random.randint(2, 4)
                total_quiz_marks = 0

                for j in range(num_questions):
                    question_type = random.choice(["mcq", "true_false"])
                    question = Question.objects.create(
                        quiz=quiz,
                        text=f"What is the main concept covered in lesson {j+1}?",
                        question_type=question_type,
                        marks=random.randint(1, 3),
                        order=j + 1,
                    )
                    total_quiz_marks += question.marks

                    # Create answers
                    if question_type == "mcq":
                        num_answers = random.randint(3, 4)
                        correct_answer_idx = random.randint(0, num_answers - 1)
                        for k in range(num_answers):
                            Answer.objects.create(
                                question=question,
                                text=f"Option {chr(65 + k)}: Demo answer {k+1}",
                                is_correct=(k == correct_answer_idx),
                                order=k + 1,
                            )
                    else:  # true_false
                        is_true_correct = random.choice([True, False])
                        Answer.objects.create(
                            question=question,
                            text="True",
                            is_correct=is_true_correct,
                            order=1,
                        )
                        Answer.objects.create(
                            question=question,
                            text="False",
                            is_correct=not is_true_correct,
                            order=2,
                        )

                # Step 3: Update total marks using the new method
                quiz.total_marks = total_quiz_marks
                quiz.save(
                    update_fields=["total_marks"]
                )  # Direct update without triggering save() logic

                total_quizzes += 1

        return total_quizzes

    def _create_enrollments(self, students, courses):
        """Create demo enrollments"""
        total_enrollments = 0

        for student in students:
            # Each student enrolls in 2-8 courses
            num_enrollments = random.randint(2, min(8, len(courses)))
            enrolled_courses = random.sample(list(courses), num_enrollments)

            for course in enrolled_courses:
                enrollment, created = Enrollment.objects.get_or_create(
                    student=student,
                    course=course,
                    defaults={
                        "enrolled_at": timezone.now()
                        - timedelta(days=random.randint(1, 90)),
                        "progress": random.randint(0, 100),
                        "is_completed": random.choice([False, False, True]),
                    },
                )
                if created:
                    total_enrollments += 1

        return total_enrollments

    def _update_enrollment_progress(self, enrollments_count):
        """Update enrollment progress based on lesson completion"""
        self.stdout.write("Updating enrollment progress...")

        enrollments = Enrollment.objects.all()

        for enrollment in enrollments:
            course = enrollment.course
            lessons = course.lessons.all()

            if lessons.exists():
                # Calculate progress based on completed lessons
                completed_lessons = lessons.filter(is_completed=True).count()
                total_lessons = lessons.count()
                progress = int((completed_lessons / total_lessons) * 100)

                enrollment.progress = progress
                enrollment.is_completed = progress >= 90
                if enrollment.is_completed and not enrollment.completed_at:
                    enrollment.completed_at = timezone.now()
                enrollment.save()

        self.stdout.write(self.style.SUCCESS("Enrollment progress updated"))

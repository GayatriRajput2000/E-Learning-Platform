from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.course_list, name='course_list'),
    path('course/<slug:slug>/', views.course_detail, name='course_detail'),
    path('enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path('course/<int:course_id>/lessons/', views.course_lessons, name='course_lessons'),
    path('course/create/', views.create_course, name='create_course'),
    path('update-progress/<int:lesson_id>/', views.update_lesson_progress, name='update_lesson_progress'),
]
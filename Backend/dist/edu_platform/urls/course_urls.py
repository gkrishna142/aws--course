from django.urls import path
from edu_platform.views.course_views import (
    CourseListView, AdminCourseCreateView, AdminCourseUpdateView, MyCoursesView,CourseStudentCountView, AllPaymentRecordsAPIView,CoursePricingCreateAPIView
)
from edu_platform.views.enrollment_views import UpdateEnrollmentView


urlpatterns = [
    # Public course endpoints. Lists active courses with search and category filtering.
    path('', CourseListView.as_view(), name='course_list'),
    
    # Admin-only endpoint to create and update a new course
    path('admin/create/course/', AdminCourseCreateView.as_view(), name='admin_course_create'),
    path('admin/update/<int:id>/', AdminCourseUpdateView.as_view(), name='admin_course_update'),
    path('payments/all/', AllPaymentRecordsAPIView.as_view(), name='all-payment-records'),

    # Lists purchased courses for the authenticated student
    path('my_courses/', MyCoursesView.as_view(), name='my_courses'),
    path('courses/student-count/', CourseStudentCountView.as_view(), name='course-student-count'),

    # Update batch for a subscribed course
    path('enrollment/<int:subscription_id>/', UpdateEnrollmentView.as_view(), name='update_enrollment'),
    path('courses/pricing/create/', CoursePricingCreateAPIView.as_view(), name='create-course-pricing'),
]


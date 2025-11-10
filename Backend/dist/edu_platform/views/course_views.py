from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.db.models import Q, Count
from rest_framework import serializers
from edu_platform.models import Course, CourseSubscription, ClassSchedule, CoursePricing
from edu_platform.serializers.course_serializers import CourseSerializer, PurchasedCoursesSerializer, CourseStudentCountSerializer, MyCoursesSerializer, PaymentRecordSerializer, CoursePricingSerializer
from edu_platform.permissions.auth_permissions import IsTeacher, IsStudent, IsTeacherOrAdmin, IsAdmin
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from datetime import date
import logging

logger = logging.getLogger(__name__)

def get_error_message(errors):
    """Extracts a specific error message from serializer errors."""
    if isinstance(errors, dict):
        for field, error in errors.items():
            if field == 'non_field_errors':
                if isinstance(error, list) and error:
                    if isinstance(error[0], dict):
                        return error[0].get('error', error[0].get('message', str(error[0])))
                    return str(error[0])
            else:
                if isinstance(error, list) and error:
                    if isinstance(error[0], dict):
                        return error[0].get('error', error[0].get('message', str(error[0])))
                    error_msg = str(error[0])
                    field_name = field.replace('_', ' ').title()
                    if error_msg == 'This field may not be blank.':
                        return f"{field_name} cannot be empty."
                    if error_msg == 'This field is required.':
                        return f"{field_name} is required."
                    if error_msg == 'Ensure this field has at least 8 characters.':
                        return f"{field_name} must be at least 8 characters long."
                    return f"{field_name}: {error_msg}"
                elif isinstance(error, dict):
                    return error.get('error', error.get('message', str(error)))
                return f"{field.replace('_', ' ').title()}: {str(error)}"
    elif isinstance(errors, list) and errors:
        if isinstance(errors[0], dict):
            return errors[0].get('error', errors[0].get('message', str(errors[0])))
        return str(errors[0])
    return 'Invalid input provided.'

class BaseAPIView(APIView):
    def validate_serializer(self, serializer_class, data, context=None):
        serializer = serializer_class(data=data, context=context or {'request': self.request})
        if not serializer.is_valid():
            raise serializers.ValidationError({
                'message': get_error_message(serializer.errors),
                'message_type': 'error',
                'status': status.HTTP_400_BAD_REQUEST
            })
        return serializer

class CourseListView(generics.ListAPIView):
    """Lists active courses with filtering for students."""
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsTeacher | IsStudent | IsAdmin]

    def get_queryset(self):
        """Filters courses based on user role, purchase status, and query parameters."""
        today = date.today()
        queryset = Course.objects.filter(is_active=True)
        user = self.request.user
        if user.is_authenticated and user.role == 'student':
            queryset = queryset.filter(class_schedules__batch_start_date__gte=today).distinct()
            if user.has_purchased_courses:
                purchased_course_ids = CourseSubscription.objects.filter(
                    student=user, payment_status='completed'
                ).values_list('course__id', flat=True)
                queryset = queryset.exclude(id__in=purchased_course_ids)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__iexact=category)
        return queryset

    @swagger_auto_schema(
        operation_description="List active courses with optional search and category filters, including batch details",
        responses={
            200: openapi.Response(
                description="Courses retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'slug': openapi.Schema(type=openapi.TYPE_STRING),
                                    'description': openapi.Schema(type=openapi.TYPE_STRING),
                                    'category': openapi.Schema(type=openapi.TYPE_STRING),
                                    'level': openapi.Schema(type=openapi.TYPE_STRING),
                                    'thumbnail': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'duration_hours': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'base_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                                    'advantages': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                                    'batches': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                                    'schedule': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT)),
                                    'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                    'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                    'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                                }
                            )
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            return Response({
                'message': 'Courses retrieved successfully.',
                'message_type': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Course list error: {str(e)}")
            return Response({
                'message': 'Failed to retrieve courses. Please try again.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminCourseCreateView(BaseAPIView, generics.CreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @swagger_auto_schema(
        operation_description="Create a new course (Admin only)",
        responses={
            201: openapi.Response(
                description="Course created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def post(self, request, *args, **kwargs):
        try:
            serializer = self.validate_serializer(CourseSerializer, request.data)
            course = serializer.save()
            return Response({
                'message': 'Course created successfully.',
                'message_type': 'success',
                'data': CourseSerializer(course, context={'request': request}).data
            }, status=status.HTTP_201_CREATED)
        except serializers.ValidationError as e:
            return Response({
                'message': e.detail.get('message', 'Invalid input data.'),
                'message_type': 'error',
                'status': e.detail.get('status', status.HTTP_400_BAD_REQUEST)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Course creation error: {str(e)}")
            return Response({
                'message': 'Failed to create course. Please try again.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminCourseUpdateView(BaseAPIView, generics.UpdateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    lookup_field = 'id'

    @swagger_auto_schema(
        operation_description="Update a course (Admin only)",
        responses={
            200: openapi.Response(
                description="Course updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            404: openapi.Response(
                description="Course not found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def put(self, request, *args, **kwargs):
        try:
            course = self.get_object()
            serializer = self.validate_serializer(CourseSerializer, request.data, context={'request': request})
            serializer.instance = course
            serializer.save()
            return Response({
                'message': 'Course updated successfully.',
                'message_type': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response({
                'message': 'Course not found.',
                'message_type': 'error',
                'status': status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)
        except serializers.ValidationError as e:
            return Response({
                'message': e.detail.get('message', 'Invalid input data.'),
                'message_type': 'error',
                'status': e.detail.get('status', status.HTTP_400_BAD_REQUEST)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Course update error: {str(e)}")
            return Response({
                'message': 'Failed to update course. Please try again.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MyCoursesView(generics.ListAPIView):
    """Lists purchased courses for students or assigned courses for teachers with their specific batch and schedule details."""
    serializer_class = MyCoursesSerializer
    permission_classes = [IsAuthenticated, IsStudent | IsTeacher]

    def get_queryset(self):
        """Returns purchased courses for students or assigned courses for teachers."""
        user = self.request.user
        if user.role == 'student':
            return CourseSubscription.objects.filter(
                student=user,
                payment_status='completed'
            ).select_related('course').prefetch_related('enrollments').order_by('-purchased_at')
        elif user.role == 'teacher':
            return Course.objects.filter(
                class_schedules__teacher=user,
                is_active=True
            ).distinct().order_by('-created_at')
        return CourseSubscription.objects.none()

    @swagger_auto_schema(
        operation_description="List purchased courses for students (with enrolled batch and schedule details) or assigned courses for teachers (with all assigned batches and their schedule details)",
        responses={
            200: openapi.Response(
                description="Courses retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'course': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'name': openapi.Schema(type=openapi.TYPE_STRING),
                                            'slug': openapi.Schema(type=openapi.TYPE_STRING),
                                            'description': openapi.Schema(type=openapi.TYPE_STRING),
                                            'category': openapi.Schema(type=openapi.TYPE_STRING),
                                            'level': openapi.Schema(type=openapi.TYPE_STRING),
                                            'thumbnail': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                            'duration_hours': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'base_price': openapi.Schema(type=openapi.TYPE_NUMBER),
                                            'advantages': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                                            'batches': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                                            'schedule': openapi.Schema(
                                                type=openapi.TYPE_ARRAY,
                                                items=openapi.Items(
                                                    type=openapi.TYPE_OBJECT,
                                                    properties={
                                                        'days': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                                                        'time': openapi.Schema(type=openapi.TYPE_STRING),
                                                        'type': openapi.Schema(type=openapi.TYPE_STRING),
                                                        'batchStartDate': openapi.Schema(type=openapi.TYPE_STRING),
                                                        'batchEndDate': openapi.Schema(type=openapi.TYPE_STRING)
                                                    }
                                                )
                                            ),
                                            'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                            'created_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time'),
                                            'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                                        }
                                    ),
                                    'purchased_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time', nullable=True),
                                    'payment_status': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                                }
                            )
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.get_serializer(queryset, many=True)
            message = 'Assigned courses retrieved successfully.' if request.user.role == 'teacher' else 'Purchased courses retrieved successfully.'
            return Response({
                'message': message,
                'message_type': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Courses retrieval error for {request.user.role}: {str(e)}")
            return Response({
                'message': 'Failed to retrieve courses. Please try again.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CourseStudentCountView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    @swagger_auto_schema(
        operation_description="List courses with their enrolled student counts (Admin only)",
        responses={
            200: openapi.Response(
                description="Course student counts retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="No courses found",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def get(self, request):
        try:
            courses = Course.objects.filter(
                subscriptions__payment_status='completed',
                subscriptions__is_active=True
            ).annotate(
                student_count=Count('subscriptions__student')
            ).order_by('name')

            if not courses.exists():
                return Response({
                    'message': 'No courses found with enrolled students.',
                    'message_type': 'error',
                    'status': status.HTTP_404_NOT_FOUND
                }, status=status.HTTP_404_NOT_FOUND)

            serializer = CourseStudentCountSerializer(courses, many=True)
            return Response({
                'message': 'Course student counts retrieved successfully.',
                'message_type': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Course student count error: {str(e)}")
            return Response({
                'message': 'Failed to retrieve course student counts.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name='payment_completed_at', lookup_expr='gte')
    end_date = filters.DateTimeFilter(field_name='payment_completed_at', lookup_expr='lte')
    course = filters.CharFilter(field_name='course__name', lookup_expr='icontains')
    status = filters.CharFilter(field_name='payment_status', lookup_expr='iexact')

    class Meta:
        model = CourseSubscription
        fields = ['start_date', 'end_date', 'course', 'status']

class AllPaymentRecordsAPIView(generics.ListAPIView):
    queryset = CourseSubscription.objects.all().order_by('-payment_completed_at')
    serializer_class = PaymentRecordSerializer
    permission_classes = [IsAuthenticated, IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PaymentFilter

    @swagger_auto_schema(
        operation_description="List all payment records with filtering (Admin only)",
        responses={
            200: openapi.Response(
                description="Payment records retrieved successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                'results': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_OBJECT))
                            }
                        )
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def list(self, request, *args, **kwargs):
        try:
            response = super().list(request, *args, **kwargs)
            return Response({
                'message': 'Payment records retrieved successfully.',
                'message_type': 'success',
                'data': {
                    'count': response.data['count'],
                    'next': response.data['next'],
                    'previous': response.data['previous'],
                    'results': response.data['results']
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Payment records retrieval error: {str(e)}")
            return Response({
                'message': 'Failed to retrieve payment records.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CoursePricingCreateAPIView(generics.CreateAPIView):
    serializer_class = CoursePricingSerializer
    permission_classes = [IsAuthenticated, IsAdmin]

    @swagger_auto_schema(
        operation_description="Create course pricing (Admin only)",
        responses={
            201: openapi.Response(
                description="Course pricing created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(type=openapi.TYPE_OBJECT)
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid input",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            401: openapi.Response(
                description="Unauthorized",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            403: openapi.Response(
                description="Forbidden",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            500: openapi.Response(
                description="Server error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'status': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            )
        }
    )
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'message': get_error_message(serializer.errors),
                    'message_type': 'error',
                    'status': status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            self.perform_create(serializer)
            return Response({
                'message': 'Course pricing created successfully.',
                'message_type': 'success',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Course pricing creation error: {str(e)}")
            return Response({
                'message': 'Failed to create course pricing. Please try again.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
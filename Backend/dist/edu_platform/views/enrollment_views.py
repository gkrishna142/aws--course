from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from edu_platform.models import CourseEnrollment
from edu_platform.serializers.enrollment_serializers import CourseEnrollmentSerializer
from edu_platform.permissions.auth_permissions import IsStudent
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

class UpdateEnrollmentView(views.APIView):
    """Allows students to update their batch selection for a course."""
    permission_classes = [IsAuthenticated, IsStudent]

    @swagger_auto_schema(
        request_body=CourseEnrollmentSerializer,
        responses={
            200: openapi.Response(
                description="Enrollment updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'course': openapi.Schema(type=openapi.TYPE_STRING),
                                'batch': openapi.Schema(type=openapi.TYPE_STRING),
                                'enrolled_at': openapi.Schema(type=openapi.TYPE_STRING, format='date-time')
                            }
                        )
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
                description="Enrollment not found",
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
    def patch(self, request, subscription_id=None):
        """Updates the batch for a specific enrollment."""
        try:
            enrollment = CourseEnrollment.objects.get(
                subscription_id=subscription_id,
                student=request.user,
                subscription__is_active=True
            )
            serializer = CourseEnrollmentSerializer(enrollment, data=request.data, partial=True, context={'request': request})
            if not serializer.is_valid():
                error_message = get_error_message(serializer.errors)
                logger.error(f"Enrollment update validation error: {error_message}")
                return Response({
                    'message': error_message,
                    'message_type': 'error',
                    'status': status.HTTP_400_BAD_REQUEST
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer.save()
            return Response({
                'message': 'Enrollment updated successfully.',
                'message_type': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except CourseEnrollment.DoesNotExist:
            return Response({
                'message': 'Enrollment not found or subscription is inactive.',
                'message_type': 'error',
                'status': status.HTTP_404_NOT_FOUND
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error updating enrollment: {str(e)}")
            return Response({
                'message': f'Failed to update enrollment: {str(e)}',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
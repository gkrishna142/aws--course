from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from rest_framework import serializers
from edu_platform.models import Course, CourseSubscription, CourseEnrollment
from edu_platform.permissions.auth_permissions import IsStudent
from edu_platform.serializers.payment_serializers import CreateOrderSerializer, VerifyPaymentSerializer, TransactionReportSerializer
from io import BytesIO
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import razorpay
import logging
import pandas as pd

# Initialize Razorpay client
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Set up logging
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

class BaseAPIView(views.APIView):
    def validate_serializer(self, serializer_class, data, context=None):
        serializer = serializer_class(data=data, context=context or {'request': self.request})
        if not serializer.is_valid():
            raise serializers.ValidationError({
                'message': get_error_message(serializer.errors),
                'message_type': 'error',
                'status': status.HTTP_400_BAD_REQUEST
            })
        return serializer

class CreateOrderView(BaseAPIView):
    """Creates a Razorpay order for course purchase."""
    permission_classes = [IsAuthenticated, IsStudent]

    @swagger_auto_schema(
        request_body=CreateOrderSerializer,
        responses={
            200: openapi.Response(
                description="Order created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'order_id': openapi.Schema(type=openapi.TYPE_STRING),
                                'amount': openapi.Schema(type=openapi.TYPE_NUMBER),
                                'currency': openapi.Schema(type=openapi.TYPE_STRING),
                                'key': openapi.Schema(type=openapi.TYPE_STRING),
                                'subscription_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'batch': openapi.Schema(type=openapi.TYPE_STRING)
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
    def post(self, request):
        """Generates Razorpay order and creates/updates subscription and enrollment."""
        try:
            serializer = self.validate_serializer(CreateOrderSerializer, request.data)
            course_id = serializer.validated_data['course_id']
            batch = serializer.validated_data['batch']
            course = Course.objects.get(id=course_id, is_active=True)

            # Check for existing pending subscription
            try:
                subscription = CourseSubscription.objects.get(
                    student=request.user,
                    course=course,
                    payment_status='pending'
                )
                logger.info(f"Reusing existing pending subscription {subscription.id} for user {request.user.id}, course {course.id}")
            except CourseSubscription.DoesNotExist:
                subscription = None

            # Create Razorpay order
            amount = int(course.base_price * 100)
            order_data = {
                'amount': amount,
                'currency': 'INR',
                'payment_capture': '1',
                'notes': {
                    'course_id': str(course.id),
                    'student_id': str(request.user.id),
                    'student_email': request.user.email,
                    'batch': batch
                }
            }
            order = client.order.create(data=order_data)

            # Update or create subscription
            if subscription:
                subscription.order_id = order['id']
                subscription.purchased_at = timezone.now()
                subscription.save(update_fields=['order_id', 'purchased_at'])
                logger.info(f"Updated subscription {subscription.id} with new order_id {order['id']}")
            else:
                subscription = CourseSubscription.objects.create(
                    student=request.user,
                    course=course,
                    amount_paid=course.base_price,
                    order_id=order['id'],
                    payment_method='razorpay',
                    payment_status='pending',
                    currency='INR'
                )
                logger.info(f"Created new subscription {subscription.id} for user {request.user.id}, course {course.id}")

            try:
                enrollment = CourseEnrollment.objects.get(
                    student=request.user,
                    course=course,
                    subscription=subscription
                )
                enrollment.batch = batch
                enrollment.save(update_fields=['batch'])
                logger.info(f"Updated enrollment for subscription {subscription.id} with batch {batch}")
            except CourseEnrollment.DoesNotExist:
                enrollment = CourseEnrollment.objects.create(
                    student=request.user,
                    course=course,
                    batch=batch,
                    subscription=subscription
                )
                logger.info(f"Created new enrollment for subscription {subscription.id} with batch {batch}")

            return Response({
                'message': 'Order created successfully.',
                'message_type': 'success',
                'data': {
                    'order_id': order['id'],
                    'amount': order['amount'],
                    'currency': order['currency'],
                    'key': settings.RAZORPAY_KEY_ID,
                    'subscription_id': subscription.id,
                    'batch': batch
                }
            }, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            return Response({
                'message': e.detail.get('message', 'Invalid input data.'),
                'message_type': 'error',
                'status': e.detail.get('status', status.HTTP_400_BAD_REQUEST)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({
                'message': 'Course not found or inactive.',
                'message_type': 'error',
                'status': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        except razorpay.errors.BadRequestError as e:
            logger.error(f"Razorpay error creating order: {str(e)}")
            return Response({
                'message': f'Payment gateway error: {str(e)}',
                'message_type': 'error',
                'status': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error creating order: {str(e)}")
            return Response({
                'message': 'Failed to create order. Please try again.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPaymentView(BaseAPIView):
    """Verifies Razorpay payment and updates subscription and enrollment."""
    permission_classes = [IsAuthenticated, IsStudent]

    @swagger_auto_schema(
        request_body=VerifyPaymentSerializer,
        responses={
            200: openapi.Response(
                description="Payment verified successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'message_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['success', 'error']),
                        'data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'subscription_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'course_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'batch': openapi.Schema(type=openapi.TYPE_STRING)
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
    def post(self, request):
        """Verifies payment signature and updates subscription and enrollment status."""
        try:
            serializer = self.validate_serializer(VerifyPaymentSerializer, request.data)
            payment_id = serializer.validated_data['razorpay_payment_id']
            order_id = serializer.validated_data['razorpay_order_id']
            signature = serializer.validated_data['razorpay_signature']
            subscription = serializer.validated_data['subscription']

            # Handle idempotency for completed payments
            if subscription.payment_status == 'completed':
                enrollment = CourseEnrollment.objects.get(subscription=subscription)
                logger.info(f"Payment already verified for subscription {subscription.id}, user {request.user.id}")
                return Response({
                    'message': 'Payment already verified.',
                    'message_type': 'success',
                    'data': {
                        'subscription_id': subscription.id,
                        'course_name': subscription.course.name,
                        'batch': enrollment.batch
                    }
                }, status=status.HTTP_200_OK)

            # Verify payment signature
            params_dict = {
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            if settings.DEBUG and settings.RAZORPAY_KEY_SECRET == 'fake_secret_for_testing':
                logger.info(f"Skipping signature verification for subscription {subscription.id} in test mode")
            else:
                try:
                    client.utility.verify_payment_signature(params_dict)
                except razorpay.errors.SignatureVerificationError as e:
                    logger.error(f"Signature verification failed for subscription {subscription.id}, user {request.user.id}: {str(e)}")
                    subscription.payment_status = 'failed'
                    subscription.save()
                    return Response({
                        'message': 'Invalid payment signature.',
                        'message_type': 'error',
                        'status': status.HTTP_400_BAD_REQUEST
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Update subscription details
            subscription.payment_id = payment_id
            subscription.payment_status = 'completed'
            subscription.payment_response = params_dict
            subscription.payment_completed_at = timezone.now()
            subscription.save()
            
            enrollment = CourseEnrollment.objects.get(subscription=subscription)
            
            logger.info(f"Payment verified for subscription {subscription.id}, user {request.user.id}, course {subscription.course.name}, batch {enrollment.batch}")
            return Response({
                'message': 'Payment verified successfully.',
                'message_type': 'success',
                'data': {
                    'subscription_id': subscription.id,
                    'course_name': subscription.course.name,
                    'batch': enrollment.batch
                }
            }, status=status.HTTP_200_OK)

        except serializers.ValidationError as e:
            return Response({
                'message': e.detail.get('message', 'Invalid input data.'),
                'message_type': 'error',
                'status': e.detail.get('status', status.HTTP_400_BAD_REQUEST)
            }, status=status.HTTP_400_BAD_REQUEST)
        except CourseEnrollment.DoesNotExist:
            logger.error(f"No enrollment found for subscription {subscription.id if 'subscription' in locals() else 'unknown'}")
            return Response({
                'message': 'No enrollment found for this subscription.',
                'message_type': 'error',
                'status': status.HTTP_400_BAD_REQUEST
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error updating subscription {subscription.id if 'subscription' in locals() else 'unknown'} for user {request.user.id}: {str(e)}")
            return Response({
                'message': 'Failed to verify payment. Please try again.',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TransactionReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @swagger_auto_schema(
        operation_description="Retrieve the last 5 transactions (Admin only)",
        responses={
            200: openapi.Response(
                description="Transactions retrieved successfully",
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
    def get(self, request):
        try:
            transactions = CourseSubscription.objects.all().order_by('-purchased_at')[:5]
            serializer = TransactionReportSerializer(transactions, many=True)
            return Response({
                'message': 'Transactions retrieved successfully.',
                'message_type': 'success',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Transaction report error: {str(e)}")
            return Response({
                'message': f'Failed to retrieve transactions: {str(e)}',
                'message_type': 'error',
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
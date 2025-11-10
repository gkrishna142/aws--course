from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from edu_platform.models import User, TeacherProfile, OTP, StudentProfile, Course, ClassSchedule,CourseEnrollment, ClassSession
from edu_platform.serializers.course_serializers import CourseSerializer
from edu_platform.utility.email_services import send_teacher_credentials
import re
from django.utils import timezone
from datetime import datetime, timedelta
import logging
from django.core.mail import send_mail
from django.conf import settings
import uuid

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()


def validate_identifier_utility(value, identifier_type=None):
    """Validates and detects identifier type (email or phone)."""
    if not identifier_type:
        if '@' in value and re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            identifier_type = 'email'
        elif re.match(r'^\+?\d{10,15}$', value):
            identifier_type = 'phone'
        else:
            raise serializers.ValidationError(
                'Invalid identifier. Must be a valid email or phone number (10-15 digits).'
            )
    else:
        if identifier_type == 'email' and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', value):
            raise serializers.ValidationError(
                'Invalid email format.'
            )
        elif identifier_type == 'phone' and not re.match(r'^\+?\d{10,15}$', value):
            raise serializers.ValidationError(
                'Invalid phone number. Must be 10-15 digits, optionally starting with +.'
            )
    return value, identifier_type


def check_user_existence_utility(email=None, phone_number=None):
    if email and User.objects.filter(email=email).exists():
        raise serializers.ValidationError({
            'This email is already registered.'
        })
    if phone_number and User.objects.filter(phone_number=phone_number).exists():
        raise serializers.ValidationError({
            'This phone number is already registered.'
        })

class TeacherProfileSerializer(serializers.ModelSerializer):
    """Serializes teacher profile data."""
    
    class Meta:
        model = TeacherProfile
        fields = ['qualification', 'experience_years', 'specialization', 'bio', 
                  'profile_picture', 'linkedin_url', 'resume', 'is_verified', 
                  'teaching_languages']
        read_only_fields = ['is_verified']

    def validate_experience_years(self, value):
        """Ensures experience years are within valid range."""
        if value < 0 or value > 50:
            raise serializers.ValidationError({
                'error': 'Experience years must be between 0 and 50.'
            })
        return value

    def validate_specialization(self, value):
        """Ensures specialization is a non-empty list."""
        if not isinstance(value, list) or not value:
            raise serializers.ValidationError({
                'error': 'Specialization must be a non-empty list of subjects.'
            })
        return value

    def validate_teaching_languages(self, value):
        """Ensures teaching languages is a list."""
        if not isinstance(value, list):
            raise serializers.ValidationError({
                'error': 'Teaching languages must be a list.'
            })
        return value

    def validate_linkedin_url(self, value):
        """Ensures LinkedIn URL is valid if provided."""
        if value and not re.match(r'^https?://(www\.)?linkedin\.com/.*$', value):
            raise serializers.ValidationError({
                'error': 'Invalid LinkedIn URL.'
            })
        return value


class UserSerializer(serializers.ModelSerializer):
    """Serializes basic user data for retrieval and updates."""
    profile = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'first_name', 
                  'last_name', 'role', 'email_verified', 'phone_verified', 
                  'date_joined', 'profile']
        read_only_fields = ['id', 'date_joined', 'email_verified', 'phone_verified']

    def validate_email(self, value):
        check_user_existence_utility(email=value)
        return value
    
    def validate_phone_number(self, value):
        check_user_existence_utility(phone_number=value)
        return value

    def get_profile(self, obj):
        logger.debug(f"Serializing profile for user {obj.id}, role: {obj.role}")
        try:
            if obj.is_teacher:
                profile = TeacherProfile.objects.get(user=obj)
                return TeacherProfileSerializer(profile, context=self.context).data
            elif obj.is_student:
                profile = StudentProfile.objects.get(user=obj)
                return StudentProfileSerializer(profile, context=self.context).data
            return None
        except Exception as e:
            logger.error(f"Error serializing profile for user {obj.id}: {str(e)}")
            raise serializers.ValidationError({
                'error': f'Failed to serialize profile: {str(e)}'
            })

class RegisterSerializer(serializers.Serializer):
    """Handles student user registration with email and phone verification."""
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)

    def validate_email(self, value):
        """Ensures email is not already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError({
                'error': 'This email is already registered.'
            })
        return value
    
    def validate_phone_number(self, value):
        """Ensures phone number is valid and not already registered."""
        if not re.match(r'^\+?\d{10,15}$', value):
            raise serializers.ValidationError({
                'error': 'Invalid phone number. Must be 10-15 digits, optionally starting with +.'
            })
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError(
                'This phone number is already registered.'
            )
        return value
    
    def validate(self, attrs):
        """Verifies email and phone OTPs and password match."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'error': 'Passwords do not match.'
            })
        
        email = attrs['email']
        phone_number = attrs['phone_number']

        # Check for verified OTPs for email and phone
        if not OTP.objects.filter(
            identifier=email,
            otp_type='email',
            purpose='registration',
            is_verified=True,
            expires_at__gt=timezone.now()
        ).exists():
            raise serializers.ValidationError({
                'error': 'Email OTP not verified or expired.'
            })

        if not OTP.objects.filter(
            identifier=phone_number,
            otp_type='phone',
            purpose='registration',
            is_verified=True,
            expires_at__gt=timezone.now()
        ).exists():
            raise serializers.ValidationError({
                'error': 'Phone OTP not verified or expired.'
            })

        return attrs
    
    def create(self, validated_data):
        """Creates a student user and deletes used OTPs."""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        #validated_data['username'] = 'name' 
        
        user = User.objects.create_user(
            **validated_data,
            role='student',
            email_verified=True,
            phone_verified=True
        )
        user.set_password(password)
        user.save()
        StudentProfile.objects.create(user=user)
        
        # Delete used OTPs to prevent reuse
        OTP.objects.filter(
            identifier=validated_data['email'],
            otp_type='email',
            purpose='registration'
        ).delete()
        
        OTP.objects.filter(
            identifier=validated_data['phone_number'],
            otp_type='phone',
            purpose='registration'
        ).delete()
        
        return user

class TeacherCourseAssignmentSerializer(serializers.Serializer):
    """Validates course assignment data for teacher registration."""
    course_id = serializers.IntegerField()
    batches = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    weekdays_start_date = serializers.DateField(required=False)
    weekdays_end_date = serializers.DateField(required=False)
    weekdays_days = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    weekdays_start = serializers.CharField(max_length=8, required=False)
    weekdays_end = serializers.CharField(max_length=8, required=False)
    weekend_start_date = serializers.DateField(required=False)
    weekend_end_date = serializers.DateField(required=False)
    saturday_start = serializers.CharField(max_length=8, required=False)
    saturday_end = serializers.CharField(max_length=8, required=False)
    sunday_start = serializers.CharField(max_length=8, required=False)
    sunday_end = serializers.CharField(max_length=8, required=False)

    def validate_session_conflicts(self, teacher, course_id, schedules):
        """
        Validate if new schedules overlap with teacher’s existing sessions.
        """
        from datetime import datetime

        for schedule in schedules:
            start_time = datetime.strptime(schedule['start_time'], "%I:%M %p").time()
            end_time = datetime.strptime(schedule['end_time'], "%I:%M %p").time()

            existing_sessions = ClassSession.objects.filter(
                schedule__teacher=teacher,
                schedule__course_id=course_id,
                session_date__range=[schedule['start_date'], schedule['end_date']]
            )

            for session in existing_sessions:
                if not (end_time <= session.start_time.time() or start_time >= session.end_time.time()):
                    raise serializers.ValidationError(
                        f"Schedule conflict on {session.session_date} "
                        f"({start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')})"
                    )

        return schedules

    def _error(self, errors):
        """Helper: format errors into one-line response."""
        messages = []
        if isinstance(errors, dict):
            for field, errs in errors.items():
                if isinstance(errs, (list, tuple)):
                    for e in errs:
                        messages.append(f"{field}: {e}")
                else:
                    messages.append(f"{field}: {errs}")
        elif isinstance(errors, list):
            messages.extend(str(e) for e in errors)
        else:
            messages.append(str(errors))

        raise serializers.ValidationError(
        " | ".join(messages)
    )

    def to_internal_value(self, data):
        """Override to catch field-level validation errors and reformat."""
        try:
            return super().to_internal_value(data)
        except serializers.ValidationError as exc:
            self._error(exc.detail)

    def validate_course_id(self, value):
        try:
            Course.objects.get(id=value, is_active=True)
            return value
        except Course.DoesNotExist:
            self._error({"course_id": f"Course with ID {value} not found or inactive."})

    def validate_batches(self, value):
        valid_batches = ['weekdays', 'weekends']
        errors = []
        if not all(batch in valid_batches for batch in value):
            errors.append(f"batches: Must be one or more of: {', '.join(valid_batches)}.")
        if len(value) != len(set(value)):
            errors.append("batches: Duplicate batches are not allowed in the same assignment.")
        if len(value) > 2:
            errors.append("batches: At most two batches (weekdays, weekends) can be assigned per course.")

        if errors:
            self._error(errors)
        return value

    def validate(self, attrs):
        batches = attrs.get('batches', [])
        errors = {}

        if 'weekdays' in batches:
            required_fields = ['weekdays_start_date', 'weekdays_end_date', 'weekdays_start', 'weekdays_end']
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = "This field is required for 'weekdays' batch."

            if attrs.get('weekdays_start_date') and attrs.get('weekdays_end_date'):
                if attrs['weekdays_start_date'] > attrs['weekdays_end_date']:
                    errors['weekdays_end_date'] = "End date must be after start date."

            if 'weekdays_days' in attrs and attrs.get('weekdays_days') is not None:
                valid_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                invalid_days = [d for d in attrs['weekdays_days'] if d not in valid_days]
                if invalid_days:
                    errors['weekdays_days'] = f"Invalid days {invalid_days}. Must be from: {', '.join(valid_days)}."

        if 'weekends' in batches:
            required_fields = ['weekend_start_date', 'weekend_end_date']
            for field in required_fields:
                if not attrs.get(field):
                    errors[field] = "This field is required for 'weekends' batch."

            if attrs.get('weekend_start_date') and attrs.get('weekend_end_date'):
                if attrs['weekend_start_date'] > attrs['weekend_end_date']:
                    errors['weekend_end_date'] = "End date must be after start date."

            has_sat = attrs.get('saturday_start') and attrs.get('saturday_end')
            has_sun = attrs.get('sunday_start') and attrs.get('sunday_end')
            if not (has_sat or has_sun):
                errors['weekend_times'] = "At least Saturday or Sunday timings must be provided."

        if errors:
            self._error(errors)
        return attrs


class TeacherCreateSerializer(serializers.ModelSerializer):
    """Serializes teacher registration data with course assignments."""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(max_length=150, required=True, allow_blank=False,trim_whitespace=False)
    course_assignments = TeacherCourseAssignmentSerializer(many=True, required=True)
    phone = serializers.CharField(source='phone_number', max_length=15, required=True, allow_blank=False)
    
    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'password', 'confirm_password', 'course_assignments']
        extra_kwargs = {
            'password': {'write_only': True},
            'confirm_password': {'write_only': True}
        }

    def validate_email(self, value):
        """Ensures email is not blank and not already registered."""
        logger.debug(f"Validating email: {value}")
        if not value.strip():
            raise serializers.ValidationError({
                'error': 'Email is required and cannot be blank.'
            })
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError({"error": "Email is already in use."})
        return value

    def validate_phone(self, value):
        """Ensures phone number is valid and not already registered."""
        logger.debug(f"Validating phone: {value}")
        value, _ = validate_identifier_utility(value, 'phone')
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("Phone number is already in use.")
        return value

    def validate(self, attrs):
        """Ensures passwords match."""
        logger.debug(f"Validating attrs: {attrs}")
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"error": "Passwords do not match."})

        course_ids = [assignment['course_id'] for assignment in attrs.get('course_assignments', [])]
        if len(course_ids) != len(set(course_ids)):
            raise serializers.ValidationError({"error": "Duplicate course assignments are not allowed."})

        return attrs

    def create(self, validated_data):
        """Creates a teacher with course assignments and schedules."""
        course_assignments = validated_data.pop('course_assignments')
        
        try:
            # Handle name only once
            full_name = validated_data.pop('name')
            if " " in full_name:
                first_name, last_name = full_name.split(" ", 1)
            else:
                first_name, last_name = full_name, ""

            validated_data['first_name'] = first_name
            validated_data['last_name'] = last_name

            # ✅ Generate a unique username automatically
            validated_data['username'] = f"{first_name.lower()}_{uuid.uuid4().hex[:6]}"

            phone = validated_data.pop('phone_number')
            validated_data['phone_number'] = phone
            #validated_data['username'] = name
            #validated_data['first_name'] = name
            validated_data.pop('confirm_password')
            password = validated_data.pop('password')
            
            # Create the user
            logger.info(f"Creating user with email: {validated_data['email']}")
            user = User.objects.create_user(
                **validated_data,
                role='teacher',
                email_verified=True,
                phone_verified=True
            )
            user.set_password(password)
            user.save()
            
            # Create the teacher profile
            logger.info(f"Creating teacher profile for user: {user.id}")
            TeacherProfile.objects.create(
                user=user,
                qualification='',
                specialization=[],
                teaching_languages=[],
            )

            # Create ClassSchedule + ClassSession for each assignment
            for assignment in course_assignments:
                course = Course.objects.get(id=assignment['course_id'])
                batches = assignment['batches']
                schedules = []

                # Weekdays
                if 'weekdays' in batches:
                    start_date = assignment['weekdays_start_date']
                    end_date = assignment['weekdays_end_date']
                    days = assignment['weekdays_days'] or ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                    start_time = assignment['weekdays_start']
                    end_time = assignment['weekdays_end']
                    schedules.append({
                        'type': 'weekdays',
                        'batch': 'weekdays',
                        'start_date': start_date,
                        'end_date': end_date,
                        'days': days,
                        'start_time': start_time,
                        'end_time': end_time
                    })

                # Weekends
                if 'weekends' in batches:
                    start_date = assignment['weekend_start_date']
                    end_date = assignment['weekend_end_date']
                    weekend_days = []
                    weekend_times = {}

                    if assignment.get('saturday_start') and assignment.get('saturday_end'):
                        weekend_days.append('Saturday')
                        weekend_times['Saturday'] = (assignment['saturday_start'], assignment['saturday_end'])
                    if assignment.get('sunday_start') and assignment.get('sunday_end'):
                        weekend_days.append('Sunday')
                        weekend_times['Sunday'] = (assignment['sunday_start'], assignment['sunday_end'])

                    if weekend_days:
                        for day in weekend_days:
                            start_time_str, end_time_str = weekend_times[day]
                            schedules.append({
                                'type': 'weekends',
                                'batch': 'weekends',
                                'start_date': start_date,
                                'end_date': end_date,
                                'days': [day],
                                'start_time': start_time_str,
                                'end_time': end_time_str
                            })

                # Validate session conflicts
                assignment_serializer = TeacherCourseAssignmentSerializer(data=assignment)
                if not assignment_serializer.is_valid():
                    raise serializers.ValidationError(assignment_serializer.errors)
                assignment_serializer.validate_session_conflicts(user, assignment['course_id'], schedules)

                # Create schedules + sessions
                if 'weekdays' in batches:
                    class_schedule = ClassSchedule.objects.create(
                        course=course,
                        teacher=user,
                        batch='weekdays',
                        batch_start_date=assignment['weekdays_start_date'],
                        batch_end_date=assignment['weekdays_end_date']
                    )
                    start_date = assignment['weekdays_start_date']
                    end_date = assignment['weekdays_end_date']
                    days = assignment['weekdays_days'] or ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                    start_time = datetime.strptime(assignment['weekdays_start'], '%I:%M %p').time()
                    end_time = datetime.strptime(assignment['weekdays_end'], '%I:%M %p').time()

                    current_date = start_date
                    while current_date <= end_date:
                        day_name = current_date.strftime('%A')
                        if day_name in days:
                            session_start = timezone.make_aware(datetime.combine(current_date, start_time))
                            session_end = timezone.make_aware(datetime.combine(current_date, end_time))
                            ClassSession.objects.create(
                                class_id=uuid.uuid4(),
                                schedule=class_schedule,
                                session_date=current_date,
                                start_time=session_start,
                                end_time=session_end
                            )
                        current_date += timedelta(days=1)

                if 'weekends' in batches:
                    class_schedule = ClassSchedule.objects.create(
                        course=course,
                        teacher=user,
                        batch='weekends',
                        batch_start_date=assignment['weekend_start_date'],
                        batch_end_date=assignment['weekend_end_date']
                    )
                    start_date = assignment['weekend_start_date']
                    end_date = assignment['weekend_end_date']

                    # Saturday sessions
                    if assignment.get('saturday_start') and assignment.get('saturday_end'):
                        sat_start_time = datetime.strptime(assignment['saturday_start'], '%I:%M %p').time()
                        sat_end_time = datetime.strptime(assignment['saturday_end'], '%I:%M %p').time()
                        current_date = start_date
                        while current_date <= end_date:
                            if current_date.strftime('%A') == 'Saturday':
                                session_start = timezone.make_aware(datetime.combine(current_date, sat_start_time))
                                session_end = timezone.make_aware(datetime.combine(current_date, sat_end_time))
                                ClassSession.objects.create(
                                    class_id=uuid.uuid4(),
                                    schedule=class_schedule,
                                    session_date=current_date,
                                    start_time=session_start,
                                    end_time=session_end
                                )
                            current_date += timedelta(days=1)

                    # Sunday sessions
                    if assignment.get('sunday_start') and assignment.get('sunday_end'):
                        sun_start_time = datetime.strptime(assignment['sunday_start'], '%I:%M %p').time()
                        sun_end_time = datetime.strptime(assignment['sunday_end'], '%I:%M %p').time()
                        current_date = start_date
                        while current_date <= end_date:
                            if current_date.strftime('%A') == 'Sunday':
                                session_start = timezone.make_aware(datetime.combine(current_date, sun_start_time))
                                session_end = timezone.make_aware(datetime.combine(current_date, sun_end_time))
                                ClassSession.objects.create(
                                    class_id=uuid.uuid4(),
                                    schedule=class_schedule,
                                    session_date=current_date,
                                    start_time=session_start,
                                    end_time=session_end
                                )
                            current_date += timedelta(days=1)

            # Send teacher credentials
            try:
                send_teacher_credentials(
                    email=user.email,
                    username=user.username,
                    password=password
                )
            except Exception as e:
                logger.error(f"Failed to send teacher credentials email: {str(e)}")

            return user

        except Exception as e:
            logger.error(f"Error creating teacher: {str(e)}")
            if 'user' in locals():
                user.delete()
            raise serializers.ValidationError({"error": f"Failed to create teacher: {str(e)}"})


class ListTeachersSerializer(serializers.ModelSerializer):
    """Serializes teacher data for listing."""
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone_number', read_only=True)
    course_assigned = serializers.SerializerMethodField(read_only=True)
    batches = serializers.SerializerMethodField(read_only=True)
    status = serializers.BooleanField(source='user.is_active', read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ['name', 'email', 'phone', 'course_assigned', 'batches', 'status']

    def get_course_assigned(self, obj):
        """Fetch assigned courses from ClassSchedule."""
        teacher_user = getattr(obj, 'user', obj)  # if obj has user, use it; else obj itself
        schedules = ClassSchedule.objects.filter(teacher=teacher_user)
        return [schedule.course.name for schedule in schedules]

    def get_batches(self, obj):
        """Fetch unique batch values from ClassSchedule."""
        teacher_user = getattr(obj, 'user', obj)
        schedules = ClassSchedule.objects.filter(teacher=teacher_user)
        # Collect unique batch values (e.g., "weekdays", "weekends")
        batches = {schedule.batch for schedule in schedules}
        return list(batches)

class ListStudentsSerializer(serializers.ModelSerializer):
    """Serializes student data for admin listing."""
    name = serializers.CharField(source='get_full_name', read_only=True)
    email = serializers.EmailField(read_only=True)
    phone = serializers.CharField(source='phone_number', read_only=True)
    enrolled_courses = serializers.SerializerMethodField()
    batches = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    registration_date = serializers.DateTimeField(source='date_joined', format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = User
        fields = ['name', 'email', 'phone', 'enrolled_courses', 'batches', 'registration_date', 'status']

    def get_enrolled_courses(self, obj):
        """Fetch courses assigned to this student."""
        enrollments = CourseEnrollment.objects.filter(student=obj)
        return [enrollment.course.name for enrollment in enrollments]

    def get_batches(self, obj):
        enrollments = CourseEnrollment.objects.filter(student=obj)
        batch_set = set()
        for enrollment in enrollments:
            if enrollment.batch:  # make sure it exists
                batch_set.add(enrollment.batch)  # add whole string, not characters
        return list(batch_set)


    def get_status(self, obj):
        """Return Active/Inactive status."""
        return "Active" if obj.is_active else "Inactive"


class AdminCreateSerializer(serializers.ModelSerializer):
    """Handles admin user creation by any user."""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True, allow_null=True)
    username = serializers.CharField(max_length=150, required=True, allow_blank=False)
    email = serializers.EmailField(required=True, allow_blank=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'password', 
                  'confirm_password', 'first_name', 'last_name']
    
    def validate_username(self, value):
        """Ensures username is not blank."""
        if not value.strip():
            raise serializers.ValidationError({
                'error': 'Username is required and cannot be blank.'
            })
        return value
    
    def validate_email(self, value):
        """Ensures email is not blank and not already registered."""
        if not value.strip():
            raise serializers.ValidationError({
                'error': 'Email is required and cannot be blank.'
            })
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError({
                'error': 'This email is already registered.'
            })
        return value
    
    def validate_phone_number(self, value):
        """Ensures phone number is valid and not already registered if provided."""
        if value:
            value, _ = validate_identifier_utility(value, 'phone')
            if User.objects.filter(phone_number=value).exists():
                raise serializers.ValidationError({
                    'error': 'This phone number is already registered.'
                })
        return value
    
    def validate_password(self, value):
        """Validates password strength."""
        return value
    
    def validate(self, attrs):
        """Ensures passwords match."""
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'error': 'Passwords do not match.'
            })
        return attrs
    
    def create(self, validated_data):
        """Creates a pre-verified admin user."""
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User.objects.create_superuser(
            **validated_data,
        )
        user.set_password(password)
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Manages password changes with validation."""
    old_password = serializers.CharField(required=True, allow_blank=False)
    new_password = serializers.CharField(required=True, min_length=8, allow_blank=False)
    confirm_password = serializers.CharField(required=True, min_length=8, allow_blank=False)
    
    def validate_old_password(self, value):
        """Verifies the old password is correct."""
        if not value:
            raise serializers.ValidationError({
                'message': 'Old password cannot be empty.',
                'message_type': 'error'
            })
        user = self.context.get('request').user
        if not user.check_password(value):
            raise serializers.ValidationError({
                'message': 'Old password is incorrect.',
                'message_type': 'error'
            })
        return value
    
    def validate_new_password(self, value):
        """Validates new password complexity."""
        if not value:
            raise serializers.ValidationError({
                'message': 'New password cannot be empty.',
                'message_type': 'error'
            })
        try:
            return value
        except Exception as e:
            raise serializers.ValidationError({
                'message': str(e) if str(e) else 'New password does not meet complexity requirements.',
                'message_type': 'error'
            })
    
    def validate_confirm_password(self, value):
        """Ensures confirm password is not empty."""
        if not value:
            raise serializers.ValidationError({
                'message': 'Confirm password cannot be empty.',
                'message_type': 'error'
            })
        return value
    
    def validate(self, attrs):
        """Ensures new password and confirm password match."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'error': 'New passwords do not match.'
            })
        return attrs
    
    def save(self):
        """Updates the user's password."""
        user = self.context.get('request').user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Handles user login with email, phone, or username."""
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate_identifier(self, value):
        identifier_type = self.initial_data.get('identifier_type')
        value, identifier_type = validate_identifier_utility(value, identifier_type)
        self.initial_data['identifier_type'] = identifier_type
        return value
    
    def validate(self, attrs):
        """Authenticates user credentials."""
        identifier = attrs.get('identifier')
        password = attrs.get('password')
        
        if not identifier or not password:
            raise serializers.ValidationError({
                'error': 'Must include "identifier" and "password".'
            })

        user = None
        try:
            user_obj = User.objects.get(Q(email=identifier) | Q(phone_number=identifier) | Q(username=identifier))
            user = authenticate(username=user_obj.email, password=password)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'error': 'Invalid identifier. Please provide a valid email, phone number, or username.'
            })

        if not user:
            raise serializers.ValidationError({
                'error': 'Invalid credentials.'
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                'error': 'User account is disabled.'
            })
        
        attrs['user'] = user
        return attrs


class SendOTPSerializer(serializers.Serializer):
    """Sends OTP to email or phone with auto-detection."""
    identifier = serializers.CharField(help_text="Email address or phone number")
    identifier_type = serializers.ChoiceField(choices=['email', 'phone'], required=False, 
                                             help_text="Optional - will be auto-detected if not provided")
    purpose = serializers.ChoiceField(choices=['registration', 'password_reset'])

    def validate_identifier(self, value):
        identifier_type = self.initial_data.get('identifier_type')
        value, identifier_type = validate_identifier_utility(value, identifier_type)
        self.initial_data['identifier_type'] = identifier_type
        return value

    def validate(self, attrs):
        """Ensures user exists for password reset and not for registration."""
        identifier = attrs['identifier']
        purpose = attrs['purpose']
        identifier_type = self.initial_data['identifier_type']
        
        if purpose == 'password_reset':
            if identifier_type == 'email' and not User.objects.filter(email=identifier).exists():
                raise serializers.ValidationError({
                    'error': 'No user found with this email address.'
                })
            elif identifier_type == 'phone' and not User.objects.filter(phone_number=identifier).exists():
                raise serializers.ValidationError({
                    'error': 'No user found with this phone number.'
                })
        elif purpose == 'registration':
            if identifier_type == 'email' and User.objects.filter(email=identifier).exists():
                raise serializers.ValidationError({
                    'error': 'This email is already registered.'
                })
            elif identifier_type == 'phone' and User.objects.filter(phone_number=identifier).exists():
                raise serializers.ValidationError({
                    'error': 'This phone number is already registered.'
                })
        
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    """Verifies OTP with auto-detection of identifier type."""
    identifier = serializers.CharField(help_text="Email address or phone number")
    identifier_type = serializers.ChoiceField(choices=['email', 'phone'], required=False,
                                             help_text="Optional - will be auto-detected if not provided")
    otp_code = serializers.CharField(max_length=4)
    purpose = serializers.ChoiceField(choices=['registration', 'password_reset'])

    def validate_identifier(self, value):
        identifier_type = self.initial_data.get('identifier_type')
        value, identifier_type = validate_identifier_utility(value, identifier_type)
        self.initial_data['identifier_type'] = identifier_type
        return value

    def validate(self, attrs):
        """Verifies OTP exists and is not expired."""
        identifier = attrs['identifier']
        otp_code = attrs['otp_code']
        purpose = attrs['purpose']
        identifier_type = self.initial_data['identifier_type']
        
        otp = OTP.objects.filter(
            identifier=identifier,
            otp_type=identifier_type,
            purpose=purpose,
            otp_code=otp_code
        ).order_by('-created_at').first()
        
        if not otp:
            raise serializers.ValidationError({
                'error': 'Invalid OTP.'
            })
        if otp.is_expired:
            raise serializers.ValidationError({
                'error': 'OTP has expired.'
            })
        
        attrs['otp'] = otp
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    """Resets password using OTP verification."""
    identifier = serializers.CharField()
    otp_code = serializers.CharField(max_length=4)
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)

    def validate_identifier(self, value):
        identifier_type = self.initial_data.get('identifier_type')
        value, identifier_type = validate_identifier_utility(value, identifier_type)
        self.initial_data['identifier_type'] = identifier_type
        return value
    
    def validate_new_password(self, value):
        return value
    
    def validate(self, attrs):
        """Verifies passwords match and OTP is valid."""
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'error': 'Passwords do not match.'
            })
        
        identifier = attrs['identifier']
        otp_code = attrs['otp_code']
        
        # Determine identifier type
        identifier_type = 'email' if '@' in identifier else 'phone'
        
        # Verify user exists
        user = None
        try:
            if identifier_type == 'email':
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(phone_number=identifier)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'error': 'No user found with this identifier.'
            })
        
        # Verify OTP
        otp = OTP.objects.filter(
            identifier=identifier,
            otp_type=identifier_type,
            purpose='password_reset',
            otp_code=otp_code
        ).order_by('-created_at').first()
        
        if not otp:
            raise serializers.ValidationError({
                'error': 'Invalid OTP.'
            })
        if otp.is_expired:
            raise serializers.ValidationError({
                'error': 'OTP has expired.'
            })
        
        attrs['user'] = user
        attrs['otp'] = otp
        return attrs

    def save(self):
        """Updates the user's password and deletes OTP."""
        user = self.validated_data['user']
        otp = self.validated_data['otp']
        user.set_password(self.validated_data['new_password'])
        user.save()
        otp.is_verified = True
        otp.save()
        OTP.objects.filter(
            identifier=self.validated_data['identifier'],
            otp_type=self.initial_data['identifier_type'],
            purpose='password_reset'
        ).delete()
        return user


class StudentProfileSerializer(serializers.ModelSerializer):
    """Serializes student profile data."""
    class Meta:
        model = StudentProfile
        fields = ['profile_picture']

class UserStatusCountSerializer(serializers.Serializer):
    active_users = serializers.IntegerField()
    registered_users = serializers.IntegerField()
    deactivated_users = serializers.IntegerField()

class StudentNotEnrolledSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    registration_dateTime = serializers.DateTimeField(source="created_at", read_only=True)
    remaining_days = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name", "email", "phone_number", "registration_dateTime", "remaining_days", "status"]

    def get_name(self, obj):
        return obj.get_full_name() or obj.username or obj.email

    def get_remaining_days(self, obj):
        if obj.trial_remaining_seconds:
            return obj.trial_remaining_seconds // 86400  # convert seconds → days
        return 0

    def get_status(self, obj):
        if obj.has_purchased_courses:
            return "purchased"
        elif obj.is_trial_expired:
            return "trial_expired"
        else:
            return "trial_active"
  
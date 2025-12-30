"""
Email service for sending OTPs using Django's SMTP backend.
"""
 
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from edu_platform.models import User, TeacherProfile, ClassSchedule, Course
import logging
 
logger = logging.getLogger(__name__)
 
 
def send_otp_email(email, otp_code, purpose='registration'):
    """Sends OTP email with HTML and plain text versions."""
    # Set email subject based on purpose
    subject = f'Your OTP for {purpose.replace("_", " ").title()}'
   
    # Create HTML content for styled email
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
            <h1>Edupravahaa</h1>
        </div>
        <div style="padding: 20px; background-color: #f9f9f9;">
            <h2>Verification Code</h2>
            <p>Hello,</p>
            <p>Your OTP verification code is:</p>
            <div style="background-color: #fff; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 5px; margin: 20px 0; border: 2px dashed #4CAF50;">
                {otp_code}
            </div>
            <p style="color: #666;">This code will expire in 10 minutes.</p>
            <p style="color: #666;">Please do not share this code with anyone.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">If you didn't request this code, please ignore this email.</p>
        </div>
        <div style="background-color: #333; color: white; padding: 10px; text-align: center; font-size: 12px;">
            © 2024 Edupravahaa. All rights reserved.
        </div>
    </div>
    """
    
    # Create plain text version for fallback
    plain_message = f"""
        Hello,
 
        Your OTP verification code is: {otp_code}
 
        This code will expire in 10 minutes. Please do not share this code with anyone.
 
        If you didn't request this code, please ignore this email.
 
        Best regards,
        Edupravahaa Team
    """
   
    try:
        # Send email using Django's SMTP backend
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"OTP email sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        # Fallback to console output in debug mode
        if settings.DEBUG:
            # In debug mode, print to console as fallback
            print(f"\n{'='*50}")
            print(f"Email to: {email}")
            print(f"Subject: {subject}")
            print(f"OTP Code: {otp_code}")
            print(f"{'='*50}\n")
            return True  # Return True in debug mode
        return False
 
 
def send_teacher_credentials(email, username, password):
    """Sends teacher credentials email with all teacher details, assigned courses, and schedules."""
    subject = 'Your Edupravahaa Instructor Profile and Course Assignments'
 
    # Fetch teacher details
    try:
        user = User.objects.get(email=email)
        teacher_profile = TeacherProfile.objects.get(user=user)
        teacher_details = {
            'name': user.first_name,
            'email': user.email,
            'password': password,
            'phone': user.phone_number,
            'qualification': teacher_profile.qualification or 'Not specified',
            'specialization': ', '.join(teacher_profile.specialization) if teacher_profile.specialization else 'Not specified',
            'teaching_languages': ', '.join(teacher_profile.teaching_languages) if teacher_profile.teaching_languages else 'Not specified',
        }
    except (User.DoesNotExist, TeacherProfile.DoesNotExist) as e:
        logger.error(f"Failed to fetch teacher details for {email}: {str(e)}")
        teacher_details = {
            'name': username,
            'email': email,
            'password': password,
            'phone': 'Not available',
            'qualification': 'Not available',
            'specialization': 'Not available',
            'teaching_languages': 'Not available',
        }
 
    # Fetch teacher's course assignments
    try:
        schedules = ClassSchedule.objects.filter(teacher__email=email)
        course_details = []
        for schedule in schedules:
            course = schedule.course
            for entry in schedule.schedule:
                course_info = {
                    'course_name': course.name,
                    'batch_type': entry['type'],
                    'start_date': entry['startDate'],
                    'end_date': entry['endDate'],
                    'days': ', '.join(entry['days']),
                    'time': entry['time']
                }
                course_details.append(course_info)
    except Exception as e:
        logger.error(f"Failed to fetch course schedules for {email}: {str(e)}")
        course_details = []
 
    # Create HTML content for styled email
    html_message = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background-color: #4CAF50; color: white; padding: 20px; text-align: center;">
            <h1>Edupravahaa</h1>
        </div>
        <div style="padding: 20px; background-color: #f9f9f9;">
            <h2>Welcome to Edupravahaa!</h2>
            <p>Hello {teacher_details['name']},</p>
            <p>Your instructor account has been created successfully. Below are your profile details and assigned courses:</p>
            <div style="background-color: #fff; padding: 20px; margin: 20px 0; border: 2px dashed #4CAF50;">
                <h3>Profile Details</h3>
                <p><strong>Name:</strong> {teacher_details['name']}</p>
                <p><strong>Email:</strong> {teacher_details['email']}</p>
                <p><strong>Password:</strong> {teacher_details['password']}</p>
                <p><strong>Phone:</strong> {teacher_details['phone']}</p>
                <p><strong>Qualification:</strong> {teacher_details['qualification']}</p>
                <p><strong>Specialization:</strong> {teacher_details['specialization']}</p>
                <p><strong>Teaching Languages:</strong> {teacher_details['teaching_languages']}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <h3>Assigned Courses</h3>
    """
    if course_details:
        for course in course_details:
            html_message += f"""
                <p><strong>Course:</strong> {course['course_name']}</p>
                <p><strong>Batch Type:</strong> {course['batch_type'].capitalize()}</p>
                <p><strong>Duration:</strong> {course['start_date']} to {course['end_date']}</p>
                <p><strong>Days:</strong> {course['days']}</p>
                <p><strong>Time:</strong> {course['time']}</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 10px 0;">
            """
    else:
        html_message += "<p>No course assignments available at this time.</p>"
 
    html_message += """
            </div>
            <p style="color: #666;">Please log in to your account to view full details and prepare for your classes.</p>
            <p style="color: #666;">Contact our support team for any questions regarding your profile or schedule.</p>
            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <p style="color: #999; font-size: 12px;">If you did not expect this email, please contact our support team.</p>
        </div>
        <div style="background-color: #333; color: white; padding: 10px; text-align: center; font-size: 12px;">
            © 2025 Edupravahaa. All rights reserved.
        </div>
    </div>
    """
 
    # Create plain text version for fallback
    plain_message = f"""
        Hello {teacher_details['name']},
 
        Your instructor account has been created successfully. Below are your profile details and assigned courses:
 
        Profile Details:
        Name: {teacher_details['name']}
        Email: {teacher_details['email']}
        Phone: {teacher_details['phone']}
        Qualification: {teacher_details['qualification']}
        Specialization: {teacher_details['specialization']}
        Teaching Languages: {teacher_details['teaching_languages']}
 
        Assigned Courses:
    """
    if course_details:
        for course in course_details:
            plain_message += f"""
        Course: {course['course_name']}
        Batch Type: {course['batch_type'].capitalize()}
        Duration: {course['start_date']} to {course['end_date']}
        Days: {course['days']}
        Time: {course['time']}
        ---
        """
    else:
        plain_message += "No course assignments available at this time.\n"
 
    plain_message += """
        Please log in to your account to view full details and prepare for your classes. Contact our support team for any questions regarding your profile or schedule.
 
        If you did not expect this email, please contact our support team.
 
        Best regards,
        Edupravahaa Team
    """
 
    try:
        # Send email using Django's SMTP backend
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Teacher profile and course assignments email sent successfully to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send teacher profile and course assignments email to {email}: {str(e)}")
        # Fallback to console output in debug mode
        if settings.DEBUG:
            print(f"\n{'='*50}")
            print(f"Email to: {email}")
            print(f"Subject: {subject}")
            print(f"Profile Details:")
            print(f"Name: {teacher_details['name']}")
            print(f"Email: {teacher_details['email']}")
            print(f"Phone: {teacher_details['phone']}")
            print(f"Qualification: {teacher_details['qualification']}")
            print(f"Specialization: {teacher_details['specialization']}")
            print(f"Teaching Languages: {teacher_details['teaching_languages']}")
            print(f"Course Assignments:")
            for course in course_details:
                print(f"Course: {course['course_name']}")
                print(f"Batch Type: {course['batch_type'].capitalize()}")
                print(f"Duration: {course['start_date']} to {course['end_date']}")
                print(f"Days: {course['days']}")
                print(f"Time: {course['time']}")
                print(f"{'-'*30}")
            print(f"{'='*50}\n")
            return True  # Return True in debug mode
        return False
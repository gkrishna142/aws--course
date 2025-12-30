import { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import Flatpickr from 'react-flatpickr'
import { User, Mail, Calendar, Lock, Phone, X } from 'react-feather'
import {
  Button,
  Modal,
  ModalHeader,
  ModalBody,
  FormGroup,
  InputGroup,
  InputGroupText,
  Input,
  Label
} from 'reactstrap'
import { registerTeacher } from '../../redux/teacherSlice'
import { fetchCourses } from "../../redux/courseSlice"
import { fetchTeachers } from '../../redux/teacherSlice'
import '@styles/react/libs/flatpickr/flatpickr.scss'
import { useNavigate } from "react-router-dom"
import Swal from "sweetalert2"

const AddNewModal = ({ open, handleModal }) => {
  const dispatch = useDispatch()
  const [formData, setFormData] = useState({
    name: '',
    course: '',
    batch: [],
    weekdaysStartDate: '',
    weekendStartDate: '',
    weekdaysStart: '',
    weekdaysEnd: '',
    saturdayStart: '',
    saturdayEnd: '',
    sundayStart: '',
    sundayEnd: '',
    email: '',
    phone: '',
    password: '',
    confirmPassword: ''
  })


  const [formErrors, setFormErrors] = useState({});

  const [selectedCourse, setSelectedCourse] = useState("");
  const { list: courses, loading: courseLoading } = useSelector((state) => state.courses);
  // Fetch course on mount
  useEffect(() => {
    dispatch(fetchCourses())
  }, [dispatch]);

  const handleChange = e => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: value })
  }

  const formatTime = date =>
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true })

  const formatDate = date => date.toLocaleDateString('en-CA')

  const generateSchedule = () => {
    let schedule = []

    if (formData.batch.includes('weekdays')) {
      schedule.push({
        type: 'weekdays',
        startDate: formData.weekdaysStartDate,
        enddate: formData.weekdaysEndDate,
        days: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
        time: `${formData.weekdaysStart} to ${formData.weekdaysEnd}`
      })
    }

    if (formData.batch.includes('weekends')) {
      if (formData.saturdayStart && formData.saturdayEnd) {
        schedule.push({
          type: 'weekends',
          startDate: formData.weekendStartDate,
          day: 'Saturday',
          time: `${formData.saturdayStart} to ${formData.saturdayEnd}`
        })
      }
      if (formData.sundayStart && formData.sundayEnd) {
        schedule.push({
          type: 'weekends',
          startDate: formData.weekendStartDate,
          day: 'Sunday',
          time: `${formData.sundayStart} to ${formData.sundayEnd}`
        })
      }
    }

    return schedule
  }

  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (loading) return;
    setLoading(true);

    try {
      const courseAssignments = {
        course_id: formData.course,
        batches: formData.batch || []
      };

      if (formData.batch.includes("weekdays")) {
        courseAssignments.weekdays_start_date = formData.weekdaysStartDate;
        courseAssignments.weekdays_end_date = formData.weekdaysEndDate;
        courseAssignments.weekdays_days = [
          "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"
        ];
        courseAssignments.weekdays_start = formData.weekdaysStart;
        courseAssignments.weekdays_end = formData.weekdaysEnd;
      }

      if (formData.batch.includes("weekends")) {
        courseAssignments.weekend_start_date = formData.weekendStartDate;
        courseAssignments.weekend_end_date = formData.weekendEndDate;
        courseAssignments.saturday_start = formData.saturdayStart;
        courseAssignments.saturday_end = formData.saturdayEnd;
        courseAssignments.sunday_start = formData.sundayStart;
        courseAssignments.sunday_end = formData.sundayEnd;
      }

      const payload = {
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        password: formData.password,
        confirm_password: formData.confirmPassword,
        course_assignments: [courseAssignments],
      };

      const resultAction = await dispatch(registerTeacher(payload));

      if (registerTeacher.fulfilled.match(resultAction)) {
        Swal.fire({
          icon: "success",
          title: "Success!",
          text: "Teacher registered successfully!",
        }).then(() => {
          handleModal(); // close modal
          navigate("/teacherdetails"); // navigate to teacher list
        });

        setFormData({
          name: '',
          course: '',
          batch: [],
          weekdaysStartDate: '',
          weekendStartDate: '',
          weekdaysStart: '',
          weekdaysEnd: '',
          saturdayStart: '',
          saturdayEnd: '',
          sundayStart: '',
          sundayEnd: '',
          email: '',
          phone: '',
          password: '',
          confirmPassword: ''
        });
        // handleModal();
        dispatch(fetchTeachers());
      } else {
        const data = resultAction.payload;

        let errorMessage = "Something went wrong!";

        if (typeof data?.message === "string") {
          // message is just a string
          errorMessage = data.message;
        } else if (data?.message?.error) {
          // message.error case
          errorMessage = data.message.error;
        } else if (typeof data?.message === "object") {

          setFormErrors(data.message);
          // message is an object with field errors
          errorMessage = Object.values(data.message)
            .flat()
            .join("\n");
        }

        Swal.fire({
          icon: "error",
          title: "Registration Failed",
          text: errorMessage,
        }).then(async() => {
          handleModal(); 

          await dispatch(fetchTeachers());  
          
          navigate("/teacherdetails"); // navigate to teacher list even on error
        });
      }
    } catch (err) {
      Swal.fire({
        icon: "error",
        title: "Error",
        text: err.message || "Something went wrong!",
      }).then(() => {
        dispatch(fetchTeachers()); 
        handleModal(); // close modal
        navigate("/teacherdetails"); // navigate to teacher list
      });
    } finally {
      setLoading(false);
    }
  };

  const CloseBtn = <X className='cursor-pointer' size={15} onClick={handleModal} />

  return (
    <Modal
      isOpen={open}
      toggle={handleModal}
      className='sidebar-sm'
      modalClassName='modal-slide-in'
      contentClassName='pt-0'
    >
      <ModalHeader className='mb-3' toggle={handleModal} close={CloseBtn} tag='div'>
        <h5 className='modal-title'>New Teacher Registration</h5>
      </ModalHeader>
      <ModalBody className='flex-grow-1'>
        <form onSubmit={handleSubmit}>
          {/* Name */}
          <FormGroup>
            <Label for='name'>Full Name</Label>
            <InputGroup>
              <InputGroupText>
                <User size={15} />
              </InputGroupText>
              <Input
                id='name'
                name='name'
                placeholder='Enter full name'
                value={formData.name}
                onChange={handleChange}
                required
              />
            </InputGroup>
          </FormGroup>

          {/* Course */}
          <FormGroup>
            <Label for='course'>Course</Label>
            <Input type="select" value={formData.course}
              onChange={(e) =>
                setFormData({ ...formData, course: parseInt(e.target.value, 10) })
              }
              required>
              <option value="" disabled>Select course</option>
              {courseLoading ? (
                <option>Loading...</option>
              ) : (
                courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))
              )}
            </Input>
          </FormGroup>

          {/* Batch */}
          <FormGroup>
            <Label>Batch Type</Label>
            <Input
              type='select'
              name='batch'
              multiple
              value={formData.batch}
              onChange={e => {
                const selected = Array.from(e.target.selectedOptions, option => option.value)
                setFormData({ ...formData, batch: selected })
              }}
              required
            >
              <option value='weekdays'>Weekdays</option>
              <option value='weekends'>Weekends</option>
            </Input>
            <small className="text-muted">
              Hold Ctrl (Windows) or Command (Mac) to select multiple batch types
            </small>
          </FormGroup>
          {/* Weekdays & Weekend Date/Time pickers */}

          {formData.batch.includes('weekdays') && (
            <>
              <FormGroup>
                <Label>Weekdays Course Start Date</Label>
                <Flatpickr
                  className='form-control'
                  options={{ dateFormat: 'Y-m-d' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, weekdaysStartDate: formatDate(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
              <FormGroup>
                <Label>Weekdays Course End Date</Label>
                <Flatpickr
                  className='form-control'
                  options={{ dateFormat: 'Y-m-d' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, weekdaysEndDate: formatDate(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
              <FormGroup>
                <Label>Weekdays Start Time</Label>
                <Flatpickr
                  className='form-control'
                  options={{ enableTime: true, noCalendar: true, dateFormat: 'h:i K' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, weekdaysStart: formatTime(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
              <FormGroup>
                <Label>Weekdays End Time</Label>
                <Flatpickr
                  className='form-control'
                  options={{ enableTime: true, noCalendar: true, dateFormat: 'h:i K' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, weekdaysEnd: formatTime(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
            </>
          )}

          {/* Weekend Date & Time */}
          {formData.batch.includes('weekends') && (
            <>
              <FormGroup>
                <Label>Weekends Course Start Date</Label>
                <Flatpickr
                  className='form-control'
                  options={{ dateFormat: 'Y-m-d' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, weekendStartDate: formatDate(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>

              <FormGroup>
                <Label>Weekends Course End Date</Label>
                <Flatpickr
                  className="form-control"
                  options={{ dateFormat: "Y-m-d" }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, weekendEndDate: formatDate(date[0]) });
                    }
                  }}
                  required
                />
              </FormGroup>
              <FormGroup>
                <Label>Saturday Start Time</Label>
                <Flatpickr
                  className='form-control'
                  options={{ enableTime: true, noCalendar: true, dateFormat: 'h:i K' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, saturdayStart: formatTime(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
              <FormGroup>
                <Label>Saturday End Time</Label>
                <Flatpickr
                  className='form-control'
                  options={{ enableTime: true, noCalendar: true, dateFormat: 'h:i K' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, saturdayEnd: formatTime(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
              <FormGroup>
                <Label>Sunday Start Time</Label>
                <Flatpickr
                  className='form-control'
                  options={{ enableTime: true, noCalendar: true, dateFormat: 'h:i K' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, sundayStart: formatTime(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
              <FormGroup>
                <Label>Sunday End Time</Label>
                <Flatpickr
                  className='form-control'
                  options={{ enableTime: true, noCalendar: true, dateFormat: 'h:i K' }}
                  onChange={date => {
                    if (date.length > 0) {
                      setFormData({ ...formData, sundayEnd: formatTime(date[0]) })
                    }
                  }}
                  required
                />
              </FormGroup>
            </>
          )}

          {/* ... keep all Flatpickr inputs as before ... */}

          {/* Email */}
          <FormGroup>
            <Label for='email'>Email</Label>
            <InputGroup>
              <InputGroupText>
                <Mail size={15} />
              </InputGroupText>
              <Input
                type='email'
                id='email'
                name='email'
                placeholder='example@email.com'
                value={formData.email}
                onChange={handleChange}
                required
              />
            </InputGroup>
          </FormGroup>

          {/* Phone */}
          <FormGroup>
            <Label for='phone'>Phone Number</Label>
            <InputGroup>
              <InputGroupText>
                <Phone size={15} />
              </InputGroupText>
              <Input
                type='text'
                id='phone'
                name='phone'
                placeholder='Enter phone number'
                value={formData.phone}
                onChange={handleChange}
                required
              />
            </InputGroup>
          </FormGroup>

          {/* Password */}
          <FormGroup>
            <Label for='password'>Password</Label>
            <InputGroup>
              <InputGroupText>
                <Lock size={15} />
              </InputGroupText>
              <Input
                type='password'
                id='password'
                name='password'
                placeholder='Enter password'
                value={formData.password}
                onChange={handleChange}
                required
              />
            </InputGroup>
          </FormGroup>

          {/* Confirm Password */}
          <FormGroup>
            <Label for='confirmPassword'>Confirm Password</Label>
            <InputGroup>
              <InputGroupText>
                <Lock size={15} />
              </InputGroupText>
              <Input
                type='password'
                id='confirmPassword'
                name='confirmPassword'
                placeholder='Re-enter password'
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />
            </InputGroup>
          </FormGroup>

          {/* <Button color='primary' type='submit'> */}
          <Button color='primary' disabled={loading}>
            {loading ? "Adding..." : "Submit"}
          </Button>
        </form>
      </ModalBody>
    </Modal>
  )
}

export default AddNewModal

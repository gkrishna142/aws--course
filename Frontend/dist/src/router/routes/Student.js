import { lazy } from 'react'

const StudentDetails = lazy(() => import('../../views/student'))

const StudentRoutes = [
  {
    path: '/studentdetails',
    element: <StudentDetails />
  }
]

export default StudentRoutes
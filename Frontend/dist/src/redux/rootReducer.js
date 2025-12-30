// ** Reducers Imports
import navbar from './navbar'
import layout from './layout'
import auth from './authentication'
import dashboard from './analyticsSlice'
import teachers from './teacherSlice'
import students from './studentSlice'
import payments from './paymentSlice'
import courses from './courseSlice'
import pricing from './priceSlice'



const rootReducer = {
  auth,
  navbar,
  layout,
  dashboard,
  teachers,
  students,
  payments,
  courses,
  pricing


} 

export default rootReducer

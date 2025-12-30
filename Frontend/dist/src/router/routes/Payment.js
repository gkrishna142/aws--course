import { lazy } from 'react'

const PaymentDetails = lazy(() => import('../../views/payment'))

const PaymentRoutes = [
  {
    path: '/paymentdetails',
    element: <PaymentDetails />
  }
]

export default PaymentRoutes
// ** Icons Import
import { Home, Circle } from 'react-feather'

export default [
  {
    id: 'dashboards',
    title: 'Dashboard',
    icon: <Home size={20} />,
    badge: 'light-warning',
    children: [
      {
        id: 'analyticsDash',
        title: 'Analytics',
        icon: <Circle size={12} />,
        navLink: '/dashboard/analytics'
      },
      // {
      //   id: 'eCommerceDash',
      //   title: 'eCommerce',
      //   icon: <Circle size={12} />,
      //   navLink: '/dashboard/ecommerce'
      // }
    ]
  }
]

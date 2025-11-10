import { lazy } from 'react'
import { Navigate } from 'react-router-dom'
const Profile = lazy(() => import('../../views/pages/profile'))
const Error = lazy(() => import('../../views/pages/misc/Error'))
const ComingSoon = lazy(() => import('../../views/pages/misc/ComingSoon'))
const ModalExamples = lazy(() => import('../../views/pages/modal-examples'))
const Maintenance = lazy(() => import('../../views/pages/misc/Maintenance'))
const NotAuthorized = lazy(() => import('../../views/pages/misc/NotAuthorized'))

const PagesRoutes = [
  {
    path: '/pages/profile',
    element: <Profile />
  },
  {
    path: '/pages/modal-examples',
    element: <ModalExamples />
  },
  {
    path: '/pages/blog/detail',
    element: <Navigate to='/pages/blog/detail/1' />
  },
  {
    path: '/pages/blog/edit',
    element: <Navigate to='/pages/blog/edit/1' />
  },
  {
    path: '/misc/coming-soon',
    element: <ComingSoon />,
    meta: {
      publicRoute: true,
      layout: 'blank'
    }
  },
  {
    path: '/misc/not-authorized',
    element: <NotAuthorized />,
    meta: {
      publicRoute: true,
      layout: 'blank'
    }
  },
  {
    path: '/misc/maintenance',
    element: <Maintenance />,
    meta: {
      publicRoute: true,
      layout: 'blank'
    }
  },
  {
    path: '/misc/error',
    element: <Error />,
    meta: {
      publicRoute: true,
      layout: 'blank'
    }
  }
]

export default PagesRoutes

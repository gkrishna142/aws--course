import React, { Suspense } from 'react'
import './App.css';
// ** Router Import
import Router from './router/Router'

const App = () => {
  return (
    <Suspense fallback={null}>
      <Router />
      {/* // gof */}
    </Suspense>
  )
}

export default App

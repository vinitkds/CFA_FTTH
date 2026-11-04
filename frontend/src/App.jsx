import React from 'react'
import { useState } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import About from './pages/About'
import Login from './pages/Login'
import Register from './pages/Register'
import NotFound from './pages/NotFound'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/navbar'
import Sidebar from './components/Sidebar'
import FTTHRetention from './pages/FTTHRetention'
import OLTInfraCharges from './pages/OLTInfraCharges'
import Leads from './pages/Leads'



function Logout(){
  localStorage.clear()
  return <Navigate to ="/login" />
}

function RegisterAndLogout(){
  localStorage.clear()
  return <Register />
}

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      {/* <Navbar/> */}
      <Routes>
        <Route path="*" element={<NotFound />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<RegisterAndLogout />} />
        <Route path="/logout" element={<Logout />} />
        
        <Route element={<Navbar/>}>
              <Route element={<Sidebar/>}>
                    <Route path="/" element={<Home />} />

                    {/* <Route path="/ftthretention" element={<FTTHRetention />} />
                    <Route path="/OLTinfracharges" element={<OLTInfraCharges/>} />
                    <Route path="/leads" element={<Leads/>} />

                    <Route path='/about' element = {
                        <ProtectedRoute>
                          <About/>
                        </ProtectedRoute>
                      }
                    /> */}
                    <Route element={<ProtectedRoute />}>
                        <Route path="/ftthretention" element={<FTTHRetention />} />
                        <Route path="/OLTinfracharges" element={<OLTInfraCharges />} />
                        <Route path="/leads" element={<Leads />} />
                        <Route path="/about" element={<About />} />
                    </Route>
              </Route>

        </Route>

      </Routes>
    </>
  )
}

export default App

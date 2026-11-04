import React from 'react'
import Sidebar from '../components/Sidebar'

const Home = () => {
  return (
    <>
      <div className='bg-red-100'>Home</div>
      {/* <Sidebar/> */}      {/* As sidebar is now children of Navbar it is rendered as outlet from Navbar */}
    </>
  )
}

export default Home
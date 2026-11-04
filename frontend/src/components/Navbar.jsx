import React from 'react'
import { Link, Outlet } from 'react-router-dom'
import FTTHLogo from '../assets/CFA-FTTH_logo.png'

const Navbar = () => {
  return (
    <>
        <nav className='flex items-center justify-between px-6 py-2 shadow'>
            <Link to="/">
                <img src={FTTHLogo} alt="CFA-FTTH" className='h-12 w-auto' />
            </Link>
            <ul className='flex gap-6 list-none m-0 p-0'>
                <li><Link to="/">Home</Link></li>
                <li><Link to="/about">About</Link></li>
                <li><Link to="/login">Login</Link></li>
                <li><Link to="/register">Register</Link></li>
            </ul>
        </nav>
        <main className='bg-pink-50'>
            {/* <p className="p-6 text-red-500">NAVBAR V2</p> */}
            <Outlet/>      {/* sidebar renders from here as a outlet of Navbar not from Home */}
        </main>
    </>
  )
}

export default Navbar
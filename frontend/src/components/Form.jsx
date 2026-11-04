import React from 'react'
import { useState } from "react";
import api from "../api"
import { useNavigate } from 'react-router-dom'
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";
import { Link } from 'react-router-dom';

// we will give 2 props to this function to use the same form dynamically for both login  & register
// 1. route it will pass corresponding api path for login (../api/token/) and register (../ap/user/register)
// 2. methode will be 'login' or 'register' 

const Form = ({ route, method }) => {   
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const methodName = method === 'login' ? "Login" : "Register"

    const handleSubmit = async(e) => {
        setLoading(true);
        e.preventDefault();

        try{
            const res = await api.post(route, {username, password})
            if(method === "login"){
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
                navigate("/")
            }else{
                navigate("/login")
            }
        }catch(error){
            alert(error)
        }finally{
            setLoading(false)
        }
    };

  return (
    <>
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
            <div className="w-full max-w-sm">
                {/* Logo Container */}
                <div className="flex justify-center mb-8">
                <img
                    src="/path/to/your/logo.svg" // Replace with your actual logo path
                    alt="Your Company Logo"
                    className="h-12 w-auto"
                />
                </div>

                {/* Form Container */}
                <form 
                onSubmit={handleSubmit} 
                className="bg-white p-6 rounded-xl shadow-lg border border-gray-100 space-y-5"
                >
                <div className="text-center">
                    <h1 className="text-xl font-bold tracking-tight text-gray-900">
                    {methodName}
                    </h1>
                    <p className="mt-1 text-xs text-gray-500">
                    {method === 'login' ? 'Welcome back! Please enter your details.' : 'Create an account to get started.'}
                    </p>
                </div>

                <div className="space-y-3.5">
                    <div>
                    <label htmlFor="username" className="block text-xs font-semibold text-gray-700 mb-1">
                        Username
                    </label>
                    <input 
                        id="username"
                        type="text"
                        className="w-full px-3.5 py-2 text-gray-900 bg-gray-50 border border-gray-300 rounded-lg text-sm transition duration-150 ease-in-out focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent placeholder-gray-400"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        placeholder="Enter username"
                        required
                    />
                    </div>

                    <div>
                    <label htmlFor="password" className="block text-xs font-semibold text-gray-700 mb-1">
                        Password
                    </label>
                    <input 
                        id="password"
                        type="password"
                        className="w-full px-3.5 py-2 text-gray-900 bg-gray-50 border border-gray-300 rounded-lg text-sm transition duration-150 ease-in-out focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent placeholder-gray-400"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="••••••••"
                        required
                    />
                    </div>
                </div>

                <button 
                    type="submit" 
                    disabled={loading}
                    className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 active:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition duration-150 ease-in-out shadow-sm"
                >
                    {loading ? (
                    <span className="flex items-center gap-2">
                        <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                    </span>
                    ) : (
                    methodName
                    )}
                </button>
                {method === 'login' ? (
                        <div>
                            <h3 className='inline-block'>In case of new user!</h3>
                            <span> </span>
                            <Link className="text-blue-500 no-underline text-bold hover:text-blue-700" to="/register">
                                Register here..
                            </Link>                        
                        </div>
                    ) : 
                    (
                        <div>
                            <h3 className='inline-block'>already registered!</h3>
                            <span> </span>
                            <Link className="text-blue-500 no-underline text-bold hover:text-blue-700" to="/login">
                                Login..
                            </Link>                        
                        </div>
                    )
                }
                </form>
            </div>
            
        </div>
            
        
    </>
  )
}

export default Form


/*
import React from 'react'
import { useState } from "react";
import api from "../api"
import { useNavigate } from 'react-router-dom'
import { ACCESS_TOKEN, REFRESH_TOKEN } from "../constants";

// we will give 2 props to this function to use the same form dynamically for both login  & register
// 1. route it will pass corresponding api path for login (../api/token/) and register (../ap/user/register)
// 2. methode will be 'login' or 'register' 

const Form = ({ route, method }) => {   
    const [username, setUsername] = useState("")
    const [password, setPassword] = useState("")
    const [loading, setLoading] = useState(false)
    const navigate = useNavigate()

    const methodName = method === 'login' ? "Login" : "Register"

    const handleSubmit = async(e) => {
        setLoading(true);
        e.preventDefault();

        try{
            const res = await api.post(route, {username, password})
            if(method === "login"){
                localStorage.setItem(ACCESS_TOKEN, res.data.access);
                localStorage.setItem(REFRESH_TOKEN, res.data.refresh);
                navigate("/")
            }else{
                navigate("/login")
            }
        }catch(error){
            alert(error)
        }finally{
            setLoading(false)
        }
    };

  return (
    <>
        <Form onSubmit={handleSubmit}>
            <h1>{ methodName }</h1>

            <div className="mb-4">
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                Username
            </label>
            <input 
                id="username"
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter Username"
            />
            </div>

            <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
            </label>
            <input 
                id="password"
                type="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter Password"
            />
            </div>

            <button className='form-button' type='submit' >
                {methodName}
            </button>


        </Form>
    </>
  )
}

export default Form

*/
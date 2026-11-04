import React, { useState } from 'react';
import { Link, Outlet } from 'react-router-dom';
import { 
  CurrencyRupeeIcon, 
  UserGroupIcon, 
  ShieldCheckIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Sidebar = () => {
  // Simple state to track whether sidebar is expanded or collapsed
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className='flex min-h-screen bg-gray-50'>
      {/* Sidebar Container */}
      <div 
        className={`${
          isOpen ? 'w-64' : 'w-16'
        } bg-blue-600 transition-all duration-300 ease-in-out flex flex-col shadow-lg z-10`}
      >
        {/* Top Header / Toggle Button Section */}
        <div className='flex items-center justify-between p-4 border-b border-blue-500'>
                {isOpen && (
                    <span className='text-white font-bold text-lg tracking-wide truncate'>
                    User Portal
                    </span>
                )}

                <button 
                    onClick={() => setIsOpen(!isOpen)}
                    className='p-2 rounded-lg text-white hover:bg-blue-700 transition-colors focus:outline-none mx-auto'
                    title={isOpen ? "Collapse Sidebar" : "Expand Sidebar"}
                >
                    {isOpen ? (
                    <XMarkIcon className='w-6 h-6' />
                    ) : (
                    <Bars3Icon className='w-6 h-6' />
                    )}
                </button>
        </div>

        {/* Navigation Links */}
        <div className='flex-1 py-4 px-2'>
          <ul className='space-y-2'>
            <li>
              <Link 
                to="/OLTinfracharges" 
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-white hover:bg-blue-700 transition-colors font-medium group"
                title="OLT Infra Charges"
              >
                <CurrencyRupeeIcon className="w-6 h-6 shrink-0 text-blue-200 group-hover:text-white" /> 
                {isOpen && <span className='truncate'>OLT Infra Charges</span>}
              </Link>
            </li>

            <li>
              <Link 
                to="/leads" 
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-white hover:bg-blue-700 transition-colors font-medium group"
                title="Leads"
              >
                <UserGroupIcon className="w-6 h-6 shrink-0 text-blue-200 group-hover:text-white" /> 
                {isOpen && <span className='truncate'>Leads</span>}
              </Link>
            </li>

            <li>
              <Link 
                to="/ftthretention" 
                className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-white hover:bg-blue-700 transition-colors font-medium group"
                title="FTTH Retention"
              >
                <ShieldCheckIcon className="w-6 h-6 shrink-0 text-blue-200 group-hover:text-white" /> 
                {isOpen && <span className='truncate'>FTTH Retention</span>}
              </Link>
            </li>
          </ul>
        </div>
      </div>

      {/* Main Content / Outlet Area */}
      <div className='flex-1 flex justify-center items-start p-6 bg-gray-100 overflow-y-auto'>
        <div className='w-full max-w-7xl bg-white rounded-xl shadow-sm p-6 border border-gray-200'>
          <Outlet /> {/*sidebar childrens viz Home, Leads, FTTH infra Charges render from here*/}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;



// import React from 'react'
// import { Link, Outlet } from 'react-router-dom'
// import { 
//   CurrencyRupeeIcon, 
//   UserGroupIcon, 
//   ShieldCheckIcon 
// } from '@heroicons/react/24/outline';

// const Sidebar = () => {
//   return (
//     <>
//         <div className='flex justify-between items-center border border-red-400'> 
//             <div className='w-12 hover:w-62 min-h-screen bg-blue-400'>
//                 <div className='text-white font-bold px-1 py-2'>
//                     <ul>
//                         <li className='my-1'>
//                             <Link 
//                                 to="/OLTinfracharges" 
//                                 className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors font-medium"
//                             >
//                                 <CurrencyRupeeIcon className="w-5 h-5 text-gray-500" /> 
//                                 OLT Infra Charges
//                             </Link>
//                         </li>

//                         <li className='my-1'>
//                             <Link 
//                                 to="/leads" 
//                                 className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors font-medium"
//                             >
//                                 <UserGroupIcon className="w-5 h-5 text-gray-500" /> 
//                                 Leads
//                             </Link>
//                         </li>

//                         <li className='my-1'>
//                             <Link 
//                                 to="/ftthretention" 
//                                 className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-700 hover:bg-gray-100 hover:text-blue-600 transition-colors font-medium"
//                             >
//                                 <ShieldCheckIcon className="w-5 h-5 text-gray-500" /> 
//                                 FTTH Retention
//                             </Link>
//                         </li>
//                     </ul>
//                 </div>
//             </div>
//             <div className='flex justify-center items-center w-full border border-white'> 
//                 <Outlet/>      
//             </div>
//         </div>
//     </>
//   )
// }

// export default Sidebar
import React from 'react';

interface InputGroupProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label: string;
}

export function InputGroup({ label, className, ...props }: InputGroupProps) {
    return (
        <div className="space-y-1.5">
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
                {label}
            </label>
            <input
                className="w-full px-4 py-2.5 bg-gray-50 border border-gray-100 rounded-xl text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#FF8BA7]/50 focus:border-[#FF8BA7] transition-all"
                {...props}
            />
        </div>
    );
}

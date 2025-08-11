'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const UTILITIES = [
  'Centerpoint',
  'AEP Texas Central',
  'AEP Texas North',
  'Oncor',
  'Texas-New Mexico Power'
];

const LOAD_FACTORS = [
  'Low',    // 30-50%
  'Medium', // 50-70%
  'High'    // 70-90%
];

function generateStartMonths() {
  const months = [];
  const currentDate = new Date();
  for (let i = 0; i < 12; i++) {
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth() + i, 1);
    const monthYear = date.toLocaleString('default', { month: 'long', year: 'numeric' });
    months.push(monthYear);
  }
  return months;
}

export function PricingSearchForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    startMonth: '',
    utility: '',
    zipCode: '',
    loadFactor: '',
    annualVolume: ''
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // Convert the form data to query parameters
    const params = new URLSearchParams(formData);
    
    // Navigate to the results page with the form data as query parameters
    router.push(`/pricing/results?${params.toString()}`);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 mb-6">
        <div>
          <label htmlFor="startMonth" className="block text-sm font-medium text-gray-700 mb-2">
            Start Month
          </label>
          <select
            id="startMonth"
            name="startMonth"
            value={formData.startMonth}
            onChange={handleChange}
            required
            className="w-full rounded-md border border-gray-300 py-2 px-3 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          >
            <option value="">Select a month</option>
            {generateStartMonths().map(month => (
              <option key={month} value={month}>{month}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="utility" className="block text-sm font-medium text-gray-700 mb-2">
            Utility
          </label>
          <select
            id="utility"
            name="utility"
            value={formData.utility}
            onChange={handleChange}
            required
            className="w-full rounded-md border border-gray-300 py-2 px-3 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          >
            <option value="">Select a utility</option>
            {UTILITIES.map(utility => (
              <option key={utility} value={utility}>{utility}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="zipCode" className="block text-sm font-medium text-gray-700 mb-2">
            ZIP Code
          </label>
          <input
            type="text"
            id="zipCode"
            name="zipCode"
            value={formData.zipCode}
            onChange={handleChange}
            pattern="[0-9]{5}"
            required
            className="w-full rounded-md border border-gray-300 py-2 px-3 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            placeholder="Enter 5-digit ZIP code"
          />
        </div>

        <div>
          <label htmlFor="loadFactor" className="block text-sm font-medium text-gray-700 mb-2">
            Load Factor
          </label>
          <select
            id="loadFactor"
            name="loadFactor"
            value={formData.loadFactor}
            onChange={handleChange}
            required
            className="w-full rounded-md border border-gray-300 py-2 px-3 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
          >
            <option value="">Select load factor</option>
            {LOAD_FACTORS.map(factor => (
              <option key={factor} value={factor}>{factor}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="annualVolume" className="block text-sm font-medium text-gray-700 mb-2">
            Annual Volume (kWh)
          </label>
          <input
            type="number"
            id="annualVolume"
            name="annualVolume"
            value={formData.annualVolume}
            onChange={handleChange}
            required
            min="0"
            className="w-full rounded-md border border-gray-300 py-2 px-3 shadow-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            placeholder="Enter annual volume"
          />
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Loading...' : 'Get Pricing'}
          </button>
        </div>
      </div>
    </form>
  );
}

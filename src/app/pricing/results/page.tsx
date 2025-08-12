'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { SectionHeader } from '@/components/ui/SectionHeader';
import Image from 'next/image';

interface PricingResult {
  term: string;
  rate: number;
  provider: string;
}

interface BackendPricingResult {
  rep: string;
  term: number;
  price_cents_per_kwh: number;
}

export default function PricingResultsPage() {
  const searchParams = useSearchParams();
  const [results, setResults] = useState<PricingResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const logoMap: Record<string, string> = {
    Atlantic: '/Atlantic_logo.png',
    ENGIE: '/ENGIE_logotype_2018.png',
  };

  useEffect(() => {
    const fetchPricingData = async () => {
      try {
        const params: Record<string, string> = {
          start_month: searchParams.get('startMonth') ?? '',
          utility: searchParams.get('utility') ?? '',
          zip_code: searchParams.get('zipCode') ?? '',
          load_factor: searchParams.get('loadFactor') ?? '',
          annual_volume: searchParams.get('annualVolume') ?? '',
        };

        const response = await fetch('/api/prices?' + new URLSearchParams(params));
        const data: BackendPricingResult[] | { error: string } = await response.json();
        if (!response.ok || !Array.isArray(data)) {
          const message = Array.isArray(data) ? 'Failed to fetch pricing data' : data.error;
          throw new Error(message || 'Failed to fetch pricing data');
        }

        const transformed = data.map((item) => ({
          provider: item.rep,
          term: String(item.term),
          rate: item.price_cents_per_kwh,
        }));
        setResults(transformed);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchPricingData();
  }, [searchParams]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading pricing data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="bg-red-50 text-red-600 p-4 rounded-lg inline-block">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <SectionHeader
        title="Pricing Results"
        description={`Found ${results.length} pricing options matching your criteria`}
      />

      {/* Summary table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Provider
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Term
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rate (¢/kWh)
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((result, index) => (
                <tr key={`summary-${index}`} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center gap-2">
                      {logoMap[result.provider] && (
                        <Image
                          src={logoMap[result.provider]}
                          alt={result.provider}
                          width={32}
                          height={16}
                        />
                      )}
                      {result.provider}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {result.term}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-blue-600">
                    <a href={`#result-${index}`} className="hover:underline">
                      {result.rate.toFixed(4)}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Provider
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Term
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rate (¢/kWh)
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {results.map((result, index) => (
                <tr key={index} id={`result-${index}`} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center gap-2">
                      {logoMap[result.provider] && (
                        <Image
                          src={logoMap[result.provider]}
                          alt={result.provider}
                          width={32}
                          height={16}
                        />
                      )}
                      {result.provider}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {result.term}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {result.rate.toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <button className="text-blue-600 hover:text-blue-800 font-medium">
                      Select Plan
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}


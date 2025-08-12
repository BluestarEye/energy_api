import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.PRICING_API_URL ?? 'http://localhost:8000';

function mapLoadFactor(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized === 'high' || normalized === 'hi') return 'HI';
  if (normalized === 'medium' || normalized === 'md') return 'HI';
  return 'LO';
}

export async function GET(request: NextRequest) {
  const { searchParams } = request.nextUrl;
  const start_month = searchParams.get('start_month') ?? '';
  const utility = searchParams.get('utility') ?? '';
  const zipcode = searchParams.get('zip_code') ?? '';
  const load_factor_param = searchParams.get('load_factor') ?? '';
  const annual_volume = parseFloat(searchParams.get('annual_volume') ?? '0');

  const load_factor = mapLoadFactor(load_factor_param);

  try {
    const res = await fetch(`${API_BASE}/get-prices`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        start_month,
        utility,
        zipcode,
        load_factor,
        annual_volume,
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      return NextResponse.json({ error: text || 'Pricing API error' }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch {
    return NextResponse.json({ error: 'Failed to connect to pricing service' }, { status: 500 });
  }
}

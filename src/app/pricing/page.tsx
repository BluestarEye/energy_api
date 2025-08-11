import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";

export default function PricingPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Energy Pricing Analysis"
        description="Access comprehensive energy pricing data and analysis tools to make informed decisions for your business."
      />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card
          title="Real-Time Pricing"
          description="Monitor current energy prices across different regions and utilities."
        />
        
        <Card
          title="Historical Trends"
          description="Analyze historical price patterns and identify market trends."
        />

        <Card
          title="Price Forecasting"
          description="Access predictive analytics for future energy pricing trends."
        />

        <Card
          title="Utility Comparison"
          description="Compare rates and terms across multiple utility providers."
        />

        <Card
          title="Custom Reports"
          description="Generate detailed pricing reports tailored to your needs."
        />

        <Card
          title="Market Insights"
          description="Get expert analysis and insights on energy market conditions."
        />
      </div>

      <div className="mt-12 bg-gray-50 rounded-lg p-8">
        <h2 className="text-2xl font-semibold mb-4">Why Choose Our Platform?</h2>
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <h3 className="text-lg font-medium mb-2">Comprehensive Data</h3>
            <p className="text-gray-600">Access pricing data from multiple sources, utilities, and regions in one place.</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Advanced Analytics</h3>
            <p className="text-gray-600">Use our powerful analytics tools to understand trends and make better decisions.</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Real-Time Updates</h3>
            <p className="text-gray-600">Stay informed with the latest pricing changes and market movements.</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Expert Support</h3>
            <p className="text-gray-600">Get assistance from our team of energy market specialists.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

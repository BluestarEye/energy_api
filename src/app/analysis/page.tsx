import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";

export default function AnalysisPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Energy Market Analysis"
        description="Leverage advanced analytics tools and insights to understand energy market trends and make data-driven decisions."
      />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card
          title="Market Trends"
          description="Analyze long-term market trends and patterns across different regions."
        />
        
        <Card
          title="Price Analytics"
          description="Deep dive into pricing data with advanced analytical tools."
        />

        <Card
          title="Consumption Analysis"
          description="Track and analyze energy consumption patterns and costs."
        />

        <Card
          title="Forecasting Models"
          description="Access sophisticated forecasting models for future pricing trends."
        />

        <Card
          title="Comparative Analysis"
          description="Compare pricing and trends across different utilities and regions."
        />

        <Card
          title="Custom Analytics"
          description="Create custom analytics dashboards tailored to your needs."
        />
      </div>

      <div className="mt-12">
        <h2 className="text-2xl font-semibold mb-6">Advanced Analytics Features</h2>
        <div className="grid gap-8 md:grid-cols-2">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-lg font-medium mb-4">Data Visualization</h3>
            <ul className="space-y-3 text-gray-600">
              <li>• Interactive charts and graphs</li>
              <li>• Real-time data updates</li>
              <li>• Customizable dashboards</li>
              <li>• Export capabilities</li>
            </ul>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-lg font-medium mb-4">Predictive Analytics</h3>
            <ul className="space-y-3 text-gray-600">
              <li>• Machine learning models</li>
              <li>• Trend predictions</li>
              <li>• Risk analysis</li>
              <li>• Market forecasting</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

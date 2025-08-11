import { SectionHeader } from "@/components/ui/SectionHeader";

export default function AboutPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="About Texas Energy Partner"
        description="We help Texas businesses secure affordable, reliable energy through expert market guidance."
      />

      <div className="grid gap-8 md:grid-cols-2">
        <div className="space-y-6">
          <div>
            <h2 className="text-2xl font-semibold mb-4">Our Mission</h2>
            <p className="text-gray-600">
              We are dedicated to providing businesses with accurate, timely, and actionable energy pricing data and analytics.
              Our team negotiates on your behalf so you can make informed decisions about energy consumption and costs.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-semibold mb-4">Our Approach</h2>
            <p className="text-gray-600">
              We combine cutting-edge technology with deep industry expertise to deliver comprehensive energy market insights. 
              Our platform aggregates data from multiple sources and presents it in an intuitive, accessible format.
            </p>
          </div>
        </div>

        <div className="bg-gray-50 p-8 rounded-lg">
          <h2 className="text-2xl font-semibold mb-6">Why Choose Us</h2>
          <div className="space-y-4">
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="font-medium mb-2">Comprehensive Coverage</h3>
              <p className="text-gray-600">Access data from multiple utilities and regions across the market.</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="font-medium mb-2">Advanced Analytics</h3>
              <p className="text-gray-600">Leverage powerful tools for deeper market insights and analysis.</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="font-medium mb-2">Expert Support</h3>
              <p className="text-gray-600">Get assistance from our team of energy market specialists.</p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm">
              <h3 className="font-medium mb-2">Real-Time Updates</h3>
              <p className="text-gray-600">Stay informed with the latest market changes and trends.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-12 border-t pt-12">
        <h2 className="text-2xl font-semibold mb-6">Our Commitment</h2>
        <div className="grid gap-6 md:grid-cols-3">
          <div>
            <h3 className="text-lg font-medium mb-2">Accuracy</h3>
            <p className="text-gray-600">We maintain the highest standards of data accuracy and validation.</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Innovation</h3>
            <p className="text-gray-600">Continuously improving our platform with the latest technology.</p>
          </div>
          <div>
            <h3 className="text-lg font-medium mb-2">Support</h3>
            <p className="text-gray-600">Dedicated to helping our clients succeed with responsive support.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

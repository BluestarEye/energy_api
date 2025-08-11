import { PricingSearchForm } from "@/components/forms/PricingSearchForm";
import { Card } from "@/components/ui/Card";

export default function Home() {
  return (
    <>
      <section className="text-center py-20">
        <h1 className="text-5xl font-bold mb-4">Texas Energy Partner</h1>
        <p className="text-xl text-gray-600 mb-8">
          Reliable energy brokerage services for Texas businesses.
        </p>
        <a
          href="#quote"
          className="bg-blue-600 text-white px-6 py-3 rounded-md hover:bg-blue-700"
        >
          Get a Quote
        </a>
      </section>

      <section id="quote" className="max-w-5xl mx-auto mt-12">
        <PricingSearchForm />
      </section>

      <section className="grid gap-6 mt-12 md:grid-cols-3">
        <Card
          title="Competitive Rates"
          description="We negotiate the best rates so you can focus on your business."
        />
        <Card
          title="Expert Market Analysis"
          description="Stay informed with detailed market insights and forecasts."
        />
        <Card
          title="Simple Process"
          description="Easy, transparent contracting from start to finish."
        />
      </section>

      <footer className="mt-20 text-center text-sm text-gray-500">
        © {new Date().getFullYear()} Texas Energy Partner. All rights reserved.
      </footer>
    </>
  );
}

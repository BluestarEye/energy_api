import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";

export default function ServicesPage() {
  return (
    <div className="space-y-8">
      <SectionHeader
        title="Our Services"
        description="Comprehensive energy brokerage solutions for Texas businesses."
      />

      <div className="grid gap-6 md:grid-cols-3">
        <Card
          title="Commercial Energy Procurement"
          description="We negotiate with leading providers to secure competitive rates tailored to your usage."
        />
        <Card
          title="Risk Management"
          description="Protect your business from market volatility with expert hedging strategies."
        />
        <Card
          title="Energy Efficiency Consulting"
          description="Optimize consumption and uncover savings through efficiency audits and guidance."
        />
      </div>
    </div>
  );
}

// Product data - Edit this file to add, remove, or update products.
// Each product needs: id, name, price, category, image, description.
// Optional: featured (boolean), features (array of strings).

const PRODUCTS = [
  {
    id: 1,
    name: "Aria Pro Access",
    price: 29.00,
    category: "subscriptions",
    image: "images/placeholder.svg",
    description: "Monthly access package for teams that want provider-backed chat, richer character workflows, dashboards, and production-grade runtime features without a custom engagement.",
    featured: true,
    features: [
      "Managed provider access for Azure OpenAI and OpenAI routes",
      "Full character actions, world generation, and dashboard surfaces",
      "Priority access to training and evaluation workflows",
      "Fits teams moving from local demos to cloud-backed usage"
    ]
  },
  {
    id: 2,
    name: "Autonomous Training Sprint",
    price: 399.00,
    category: "training",
    image: "images/placeholder.svg",
    description: "A focused enablement package for teams adopting LoRA fine-tuning, evaluation loops, and autonomous training cycles across the Aria stack.",
    featured: true,
    features: [
      "Training pipeline review and dataset readiness guidance",
      "Evaluation setup for batch runs, analytics, and promotion gates",
      "Operator walkthrough for dashboards and performance tracking",
      "Best fit before turning on continuous or scheduled retraining"
    ]
  },
  {
    id: 3,
    name: "Quantum Pilot Package",
    price: 1299.00,
    category: "quantum",
    image: "images/placeholder.svg",
    description: "Hybrid quantum-classical pilot planning for teams exploring simulators, Azure Quantum workflows, and proof-of-value experiments before committing to larger workloads.",
    featured: true,
    features: [
      "Circuit design and simulation workflow review",
      "Azure Quantum integration planning and guardrail setup",
      "Pilot architecture guidance for hybrid quantum ML experiments",
      "Intended for research or enterprise readiness conversations"
    ]
  },
  {
    id: 4,
    name: "Enterprise Deployment Workshop",
    price: 799.00,
    category: "services",
    image: "images/placeholder.svg",
    description: "Hands-on deployment scoping for organizations packaging Aria for internal rollout, managed infrastructure, and operator onboarding.",
    featured: false,
    features: [
      "Deployment path review across docs, APIs, and automation surfaces",
      "Recommendations for monitoring, subscriptions, and service ownership",
      "Rollout plan for customer-facing or internal operator teams",
      "Ideal precursor to a broader enterprise implementation"
    ]
  }
];

// Categories used for filtering
const CATEGORIES = [
  { id: "subscriptions", name: "Subscriptions", icon: "fa-layer-group" },
  { id: "training", name: "Training", icon: "fa-brain" },
  { id: "quantum", name: "Quantum Programs", icon: "fa-atom" },
  { id: "services", name: "Deployment Services", icon: "fa-server" }
];

function getCategoryById(id) {
  return CATEGORIES.find(function (category) { return category.id === id; }) || null;
}

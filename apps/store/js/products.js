// Product data - Edit this file to add, remove, or update products.
// Each product needs: id, name, price, category, image, description.
// Optional: featured (boolean), features (array of strings).

const PRODUCTS = [
  {
    id: 1,
    name: "Wireless Bluetooth Earbuds",
    price: 49.99,
    category: "audio",
    image: "images/placeholder.svg",
    description: "High-quality wireless earbuds with noise cancellation, 24-hour battery life, and premium sound. Perfect for music, calls, and workouts.",
    featured: true,
    features: [
      "Active noise cancellation",
      "24-hour battery with charging case",
      "IPX5 water resistant",
      "Bluetooth 5.3"
    ]
  },
  {
    id: 2,
    name: "Smart Watch Pro",
    price: 129.99,
    category: "wearables",
    image: "images/placeholder.svg",
    description: "Feature-packed smartwatch with health tracking, GPS, and a stunning AMOLED display. Stay connected and monitor your fitness goals.",
    featured: true,
    features: [
      "1.4\" AMOLED display",
      "Heart rate & SpO2 monitoring",
      "Built-in GPS",
      "7-day battery life"
    ]
  },
  {
    id: 3,
    name: "USB-C Hub Adapter 7-in-1",
    price: 34.99,
    category: "accessories",
    image: "images/placeholder.svg",
    description: "Expand your laptop connectivity with this compact 7-in-1 USB-C hub featuring HDMI, USB 3.0, SD card reader, and power delivery.",
    featured: false,
    features: [
      "4K HDMI output",
      "100W power delivery passthrough",
      "USB 3.0 ports x3",
      "SD & microSD card reader"
    ]
  },
  {
    id: 4,
    name: "Portable Bluetooth Speaker",
    price: 59.99,
    category: "audio",
    image: "images/placeholder.svg",
    description: "Compact, waterproof Bluetooth speaker with 360-degree sound and 12-hour playtime. Take your music anywhere.",
    featured: true,
    features: [
      "360-degree immersive sound",
      "IPX7 waterproof",
      "12-hour battery life",
      "Built-in microphone"
    ]
  }
];

// Categories used for filtering
const CATEGORIES = [
  { id: "smartphones", name: "Smartphones", icon: "fa-mobile-screen-button" },
  { id: "audio", name: "Audio", icon: "fa-headphones" },
  { id: "wearables", name: "Wearables", icon: "fa-clock" },
  { id: "accessories", name: "Accessories", icon: "fa-plug" }
];

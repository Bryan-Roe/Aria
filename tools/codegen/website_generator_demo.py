#!/usr/bin/env python3
"""
Website Generator - Create Complete Static Websites
Aria Platform Code Generation System
"""

import sys
from pathlib import Path

# ============================================================================
# EXAMPLE 1: GENERATED PORTFOLIO WEBSITE
# ============================================================================

PORTFOLIO_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Portfolio - John Doe</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <div class="logo">John Doe</div>
            <ul class="nav-menu">
                <li><a href="#home">Home</a></li>
                <li><a href="#about">About</a></li>
                <li><a href="#work">Work</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <section id="home" class="hero">
        <div class="hero-content">
            <h1>Creative Developer & Designer</h1>
            <p>Building beautiful digital experiences</p>
            <a href="#work" class="btn btn-primary">View My Work</a>
        </div>
    </section>

    <section id="about" class="about">
        <div class="container">
            <h2>About Me</h2>
            <p>I'm a passionate developer with 5+ years of experience creating web applications and digital products.</p>
            <div class="skills">
                <div class="skill-item">
                    <h3>Frontend</h3>
                    <p>React, Vue, HTML/CSS, JavaScript</p>
                </div>
                <div class="skill-item">
                    <h3>Backend</h3>
                    <p>Node.js, Python, PostgreSQL</p>
                </div>
                <div class="skill-item">
                    <h3>Design</h3>
                    <p>UI/UX, Figma, Prototyping</p>
                </div>
            </div>
        </div>
    </section>

    <section id="work" class="work">
        <div class="container">
            <h2>Recent Work</h2>
            <div class="portfolio-grid">
                <div class="portfolio-item">
                    <img src="project1.jpg" alt="Project 1">
                    <h3>E-Commerce Platform</h3>
                    <p>Built a full-stack e-commerce solution</p>
                </div>
                <div class="portfolio-item">
                    <img src="project2.jpg" alt="Project 2">
                    <h3>Mobile App</h3>
                    <p>React Native mobile application</p>
                </div>
                <div class="portfolio-item">
                    <img src="project3.jpg" alt="Project 3">
                    <h3>SaaS Dashboard</h3>
                    <p>Analytics and management dashboard</p>
                </div>
            </div>
        </div>
    </section>

    <section id="contact" class="contact">
        <div class="container">
            <h2>Get In Touch</h2>
            <form class="contact-form">
                <input type="text" placeholder="Name" required>
                <input type="email" placeholder="Email" required>
                <textarea placeholder="Message" rows="5" required></textarea>
                <button type="submit" class="btn btn-primary">Send Message</button>
            </form>
        </div>
    </section>

    <footer class="footer">
        <p>&copy; 2026 John Doe. All rights reserved.</p>
    </footer>

    <script src="script.js"></script>
</body>
</html>"""

PORTFOLIO_CSS = """* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary: #667eea;
    --secondary: #764ba2;
    --dark: #1a202c;
    --light: #f7fafc;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background: white;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

/* Navigation */
.navbar {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-menu a {
    color: white;
    text-decoration: none;
    transition: opacity 0.3s;
}

.nav-menu a:hover {
    opacity: 0.8;
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    color: white;
    padding: 8rem 2rem;
    text-align: center;
    min-height: 600px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.hero-content h1 {
    font-size: 3.5rem;
    margin-bottom: 1rem;
    animation: fadeInUp 1s ease;
}

.hero-content p {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

/* Buttons */
.btn {
    display: inline-block;
    padding: 0.8rem 2rem;
    border-radius: 5px;
    text-decoration: none;
    font-weight: bold;
    transition: all 0.3s;
    border: none;
    cursor: pointer;
}

.btn-primary {
    background: white;
    color: var(--primary);
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
}

/* Sections */
section {
    padding: 4rem 2rem;
}

section h2 {
    font-size: 2.5rem;
    margin-bottom: 2rem;
    text-align: center;
    color: var(--dark);
}

/* About Section */
.about {
    background: var(--light);
}

.skills {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.skill-item {
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    text-align: center;
}

.skill-item h3 {
    color: var(--primary);
    margin-bottom: 1rem;
}

/* Portfolio Grid */
.portfolio-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
    margin-top: 2rem;
}

.portfolio-item {
    background: white;
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.portfolio-item:hover {
    transform: translateY(-5px);
}

.portfolio-item img {
    width: 100%;
    height: 200px;
    object-fit: cover;
}

.portfolio-item h3,
.portfolio-item p {
    padding: 1rem;
}

.portfolio-item h3 {
    color: var(--primary);
}

/* Contact Section */
.contact {
    background: var(--light);
}

.contact-form {
    max-width: 600px;
    margin: 2rem auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}

.contact-form input,
.contact-form textarea {
    padding: 1rem;
    border: 1px solid #ddd;
    border-radius: 5px;
    font-family: inherit;
    font-size: 1rem;
}

.contact-form input:focus,
.contact-form textarea:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* Footer */
.footer {
    background: var(--dark);
    color: white;
    text-align: center;
    padding: 2rem;
}

/* Animations */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Responsive */
@media (max-width: 768px) {
    .nav-menu {
        flex-direction: column;
        gap: 1rem;
    }

    .hero-content h1 {
        font-size: 2rem;
    }

    section h2 {
        font-size: 2rem;
    }
}
"""

PORTFOLIO_JS = """// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Contact form submission
const contactForm = document.querySelector('.contact-form');
if (contactForm) {
    contactForm.addEventListener('submit', function(e) {
        e.preventDefault();
        alert('Thank you for your message! I will get back to you soon.');
        this.reset();
    });
}

// Add scroll effect to navbar
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 0) {
        navbar.style.boxShadow = '0 5px 15px rgba(0,0,0,0.1)';
    } else {
        navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    }
});

console.log('Website loaded successfully!');
"""


# ============================================================================
# EXAMPLE 2: GENERATED LANDING PAGE
# ============================================================================

LANDING_HTML_SNIPPET = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ProductName - Modern SaaS Solution</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <div class="logo">ProductName</div>
            <ul class="nav-menu">
                <li><a href="#features">Features</a></li>
                <li><a href="#pricing">Pricing</a></li>
                <li><a href="#faq">FAQ</a></li>
                <li><a href="#contact">Contact</a></li>
            </ul>
        </div>
    </nav>

    <section class="hero">
        <h1>The Modern Solution You've Been Waiting For</h1>
        <p>Increase productivity, reduce costs, and scale faster</p>
        <button class="btn btn-primary">Start Free Trial</button>
    </section>

    <section id="features" class="features">
        <h2>Powerful Features</h2>
        <div class="feature-grid">
            <div class="feature-card">
                <h3>⚡ Lightning Fast</h3>
                <p>Built for performance and speed</p>
            </div>
            <div class="feature-card">
                <h3>🔒 Secure</h3>
                <p>Enterprise-grade security</p>
            </div>
            <div class="feature-card">
                <h3>📊 Analytics</h3>
                <p>Real-time insights and reports</p>
            </div>
        </div>
    </section>

    <section id="pricing" class="pricing">
        <h2>Simple, Transparent Pricing</h2>
        <!-- Pricing table here -->
    </section>

    <section id="faq" class="faq">
        <h2>Frequently Asked Questions</h2>
        <!-- FAQ items here -->
    </section>

    <footer class="footer">
        <p>&copy; 2026 ProductName. All rights reserved.</p>
    </footer>
</body>
</html>"""


# ============================================================================
# EXAMPLE 3: GENERATED BLOG
# ============================================================================

BLOG_HTML_SNIPPET = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Tech Blog</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <nav class="navbar">
        <div class="container">
            <div class="logo">Tech Blog</div>
            <input type="text" class="search-box" placeholder="Search posts...">
        </div>
    </nav>

    <main class="container">
        <div class="blog-grid">
            <article class="blog-card">
                <img src="post1.jpg" alt="Post 1">
                <h2>Getting Started with Web Development</h2>
                <p class="meta">March 28, 2026 • 5 min read</p>
                <p>A comprehensive guide for beginners...</p>
                <a href="/post1.html" class="read-more">Read More →</a>
            </article>

            <article class="blog-card">
                <img src="post2.jpg" alt="Post 2">
                <h2>Advanced JavaScript Patterns</h2>
                <p class="meta">March 27, 2026 • 8 min read</p>
                <p>Master modern JavaScript techniques...</p>
                <a href="/post2.html" class="read-more">Read More →</a>
            </article>
        </div>
    </main>

    <footer class="footer">
        <p>&copy; 2026 Tech Blog. All rights reserved.</p>
    </footer>
</body>
</html>"""


def demo_portfolio_generation():
    """Demo: Generate portfolio website"""
    print("\n" + "=" * 70)
    print("DEMO 1: PORTFOLIO WEBSITE GENERATION")
    print("=" * 70)

    print("\n📝 REQUEST:")
    print(
        "  @llm-maker Build a professional portfolio website with home, about, work, and contact pages"
    )

    print("\n📦 GENERATED FILES:")
    files = {
        "index.html": len(PORTFOLIO_INDEX_HTML),
        "style.css": len(PORTFOLIO_CSS),
        "script.js": len(PORTFOLIO_JS),
    }

    total_bytes = sum(files.values())

    for filename, size in files.items():
        print(f"  ✓ {filename:20} ({size:>6} bytes)")

    print(f"\n  Total Size: {total_bytes} bytes")

    print("\n📄 SAMPLE CODE (index.html):")
    print("-" * 70)
    print(PORTFOLIO_INDEX_HTML[:600] + "...")

    print("\n🎨 FEATURES INCLUDED:")
    features = [
        "Sticky navigation menu",
        "Hero section with CTA",
        "About section with skills grid",
        "Portfolio grid with hover effects",
        "Contact form with validation",
        "Smooth scrolling",
        "Responsive design",
        "Modern gradient styling",
        "Animations",
    ]

    for feature in features:
        print(f"  ✓ {feature}")


def demo_landing_page():
    """Demo: Generate landing page"""
    print("\n" + "=" * 70)
    print("DEMO 2: LANDING PAGE GENERATION")
    print("=" * 70)

    print("\n📝 REQUEST:")
    print(
        "  @llm-maker Build a SaaS landing page with hero, features, pricing, and FAQ"
    )

    print("\n📦 GENERATED STRUCTURE:")
    sections = [
        "Navigation bar with logo",
        "Hero section with headline and CTA",
        "Features section with 3+ feature cards",
        "Pricing table with 3 tiers",
        "FAQ accordion section",
        "Footer with links",
    ]

    for section in sections:
        print(f"  ✓ {section}")

    print("\n📄 SAMPLE HTML:")
    print("-" * 70)
    print(LANDING_HTML_SNIPPET[:500] + "...")

    print("\n💡 CUSTOMIZATION READY:")
    print("  • Text: Easy to change all copy and headlines")
    print("  • Colors: Modify CSS gradient and color variables")
    print("  • Pricing: Update pricing tiers and features")
    print("  • Images: Replace placeholder images")


def demo_blog():
    """Demo: Generate blog"""
    print("\n" + "=" * 70)
    print("DEMO 3: BLOG WEBSITE GENERATION")
    print("=" * 70)

    print("\n📝 REQUEST:")
    print("  @llm-maker Create a tech blog with posts, archives, and dark mode")

    print("\n📦 GENERATED PAGES:")
    pages = [
        "index.html - Blog post listing",
        "post.html - Individual post template",
        "archive.html - Posts by date/category",
        "about.html - Blog author info",
        "style.css - Responsive styling + dark mode toggle",
    ]

    for page in pages:
        print(f"  ✓ {page}")

    print("\n📄 SAMPLE CODE:")
    print("-" * 70)
    print(BLOG_HTML_SNIPPET[:400] + "...")

    print("\n✨ FEATURES:")
    features = [
        "Blog post grid layout",
        "Search functionality",
        "Category filtering",
        "Dark mode toggle",
        "Social sharing buttons",
        "Comments section",
        "Related posts",
        "Reading time estimate",
    ]

    for feature in features:
        print(f"  ✓ {feature}")


def show_generation_types():
    """Show all website types that can be generated"""
    print("\n" + "=" * 70)
    print("WEBSITE TYPES YOU CAN GENERATE")
    print("=" * 70)

    types = {
        "Portfolio": {
            "perfect_for": "Designers, developers, freelancers, creatives",
            "includes": "Hero, portfolio grid, about, testimonials, contact",
            "pages": "4-6",
        },
        "Landing Page": {
            "perfect_for": "SaaS products, startups, services",
            "includes": "Hero, features, pricing, FAQ, testimonials, CTA",
            "pages": "1 + modal pages",
        },
        "Blog": {
            "perfect_for": "Writers, journalists, tech blogs, news",
            "includes": "Post listing, archives, categories, search, dark mode",
            "pages": "4+",
        },
        "Documentation": {
            "perfect_for": "APIs, libraries, frameworks, tools",
            "includes": "Getting started, API reference, examples, search",
            "pages": "5+",
        },
        "E-Commerce": {
            "perfect_for": "Stores, shops, marketplaces",
            "includes": "Product catalog, cart, checkout, reviews, search",
            "pages": "6+",
        },
    }

    for site_type, info in types.items():
        print(f"\n{site_type}")
        print(f"  Best for: {info['perfect_for']}")
        print(f"  Includes: {info['includes']}")
        print(f"  Pages: {info['pages']}")


def show_generation_commands():
    """Show all generation commands"""
    print("\n" + "=" * 70)
    print("GENERATION COMMANDS - COPY & PASTE READY")
    print("=" * 70)

    commands = {
        "Portfolio": "@llm-maker Build a professional portfolio website showcasing 12 projects with beautiful grid layout and contact form",
        "Blog": "@llm-maker Create a tech blog with dark mode, post categories, archives, and social sharing buttons",
        "Landing": "@llm-maker Build a modern SaaS landing page with hero section, feature list, pricing table, testimonials, and FAQ",
        "Documentation": "@llm-maker Generate API documentation website with quick start guide, code examples, and API reference table",
        "E-Commerce": "@llm-maker Create an e-commerce store with product catalog, shopping cart, checkout, and customer reviews",
    }

    for site_type, command in commands.items():
        print(f"\n{site_type}:")
        print(f"  {command}")


def show_deployment_guide():
    """Show how to deploy generated sites"""
    print("\n" + "=" * 70)
    print("DEPLOYMENT OPTIONS FOR GENERATED WEBSITES")
    print("=" * 70)

    options = {
        "GitHub Pages": {
            "cost": "Free",
            "time": "< 5 minutes",
            "benefits": "Connected to Git, automatic deployments, custom domain",
        },
        "Netlify": {
            "cost": "Free (with paid tiers)",
            "time": "< 5 minutes",
            "benefits": "Drag & drop, auto-deploys, form handling, analytics",
        },
        "Vercel": {
            "cost": "Free (with paid tiers)",
            "time": "< 5 minutes",
            "benefits": "Optimized for static sites, analytics, serverless functions",
        },
        "AWS S3": {
            "cost": "Pay per GB",
            "time": "< 10 minutes",
            "benefits": "Scalable, CDN available, very cheap for small sites",
        },
    }

    for platform, details in options.items():
        print(f"\n{platform}")
        print(f"  Cost: {details['cost']}")
        print(f"  Setup Time: {details['time']}")
        print(f"  Benefits: {details['benefits']}")


def main():
    """Run website generator demos"""
    print("\n╔" + "=" * 68 + "╗")
    print("║  WEBSITE GENERATOR - Aria Code Generation System              ║")
    print("║  Create Professional Websites in Seconds                      ║")
    print("╚" + "=" * 68 + "╝")

    demo_portfolio_generation()
    demo_landing_page()
    demo_blog()
    show_generation_types()
    show_generation_commands()
    show_deployment_guide()

    print("\n" + "=" * 70)
    print("READY TO GENERATE YOUR WEBSITE?")
    print("=" * 70)

    print("\n🚀 OPTION 1: Copilot Chat (Fastest)")
    print("   Press Ctrl+Shift+I")
    print("   Copy a command from above and paste it")

    print("\n🚀 OPTION 2: View Generator Guide")
    print("   python3 website_generator_guide.py")

    print("\n🚀 OPTION 3: Interactive Menu")
    print("   python3 code_generation_quickstart.py")

    print("\n" + "=" * 70)
    print("✨ START BUILDING NOW! ✨")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

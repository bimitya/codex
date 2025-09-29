### Google Places Texas Home Builders Scraper

Searches Google Maps Places for businesses in Texas matching prefab/modular/manufactured home builder terms and exports a CSV.

#### Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Set your API key via env var or pass as a flag:

```bash
export GOOGLE_MAPS_API_KEY=YOUR_KEY
```

#### Run

```bash
python places_texas_search.py --out results.csv \
  --grid-step 1.0 --radius 50000 --max-pages 3
```

Flags:
- **--keywords**: Optional list to override default terms.
- **--grid-step**: Degrees between grid points over Texas bounds.
- **--radius**: Meters for Text Search (max 50000 per API).
- **--max-pages**: Up to 3 pages per query.

Output CSV columns:
- business name, Place ID, website URL, phone, full address, average rating, rating count

Notes:
- This uses Text Search + Place Details. Results are de-duplicated by Place ID and filtered to Texas.
- Respect Google Maps Platform Terms of Service and your quota.
# PrefabHub - Modern Prefab Directory

A beautiful, modern homepage for a prefab directory showcasing prefabricated homes and buildings from manufacturers worldwide.

## Features

- **Modern Design**: Clean, professional interface with a contemporary color scheme
- **Hero Section**: Eye-catching introduction with key statistics
- **Featured Prefab**: Highlighted prefab home with specifications and actions
- **Category Browse**: Easy navigation through different prefab types
- **Trending Analytics**: Real-time insights into popular prefabs
- **Customer Testimonials**: Social proof from satisfied customers
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Interactive Elements**: Smooth animations and hover effects

## Sections

1. **Navigation Sidebar**: Easy access to different sections (Browse Prefabs, Manufacturers, Categories, etc.)
2. **Hero Section**: Main call-to-action with key statistics (500+ models, 150+ manufacturers, 25+ countries)
3. **Featured Prefab**: Showcase of the "Modern EcoHouse 120" with specs and pricing
4. **Categories**: Browse by type (Residential, Commercial, Tiny Houses, Modular Offices)
5. **Trending**: Analytics showing weekly views and growth trends
6. **Testimonials**: Customer success stories and reviews

## Technology

- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with CSS Grid, Flexbox, and custom properties
- **Vanilla JavaScript**: Interactive functionality and smooth animations
- **Responsive Design**: Mobile-first approach with breakpoints

## Getting Started

1. Open `index.html` in your web browser
2. Explore the different sections and interactive elements
3. Test the responsive design by resizing your browser window

## Customization

The design uses CSS custom properties (variables) for easy theming:
- Colors can be modified in the `:root` selector
- Layout can be adjusted through the grid system
- Typography uses Google Fonts (DM Sans)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
# 🌅 Sunset Skateboarding Theme

## Overview
A warm, vibrant theme inspired by twilight skateboarding sessions with purple and orange sunset hues.

## Color Palette

### Primary Colors
- **Purple** (`#7C3AED`) - Main brand color, used for buttons, links, and accents
- **Orange** (`#F97316`) - Secondary accent, warm highlights
- **Teal** (`#14B8A6`) - Tertiary accent for special actions

### Gradients
- **Header/Footer**: Linear gradient from purple → orange (135deg)
- **Buttons**: Linear gradient from purple → orange (135deg)
- **Stats**: Text gradient from purple → orange
- **Card Placeholders**: Purple pale → orange → teal light

### Backgrounds
- **Body**: Warm off-white (`#FDF8F3`)
- **Cards**: Pure white (`#FFFFFF`)
- **Borders**: Purple pale (`#EDE9FE`)

## Design System Changes

### Border Radius
- **Buttons**: 24px (pill-shaped)
- **Cards**: 20px (soft rounded)
- **Inputs**: 12px (gentle curves)
- **Badges**: 20px (rounded pills)
- **Modals**: 16px (comfortable corners)

### Shadows
- Softer, purple-tinted shadows
- Elevation increases on hover with purple glow
- Example: `0 4px 12px rgba(124, 58, 237, 0.1)`

### Typography
- Maintained sans-serif system fonts
- White text on gradient headers
- Purple for primary links and actions
- Orange for hover states

## Component Styling

### Header
- **Background**: Purple-to-orange gradient
- **Text**: White with subtle shadow
- **Navigation**: White text with semi-transparent white hover backgrounds

### Buttons
- **Primary**: Purple-to-orange gradient with purple shadow
- **Secondary**: Light gray with purple active state
- **Edit**: Teal solid with lighter teal hover
- **Links**: Purple with orange hover

### Cards (Spot Cards)
- **Border**: 2px solid purple pale
- **Border Radius**: 20px
- **Hover**: Lifts 6px with purple shadow glow
- **Hover Border**: Changes to solid purple

### Forms
- **Inputs**: 12px border-radius with purple focus ring
- **Filter Forms**: White background with purple pale border and soft shadow
- **Focus State**: Purple border with purple pale outer glow

### Badges
- **Shape**: 20px border-radius (pill)
- **Type Badges**: Purple pale background with purple text
- **Difficulty**: Contextual colors (green/orange/red/purple)

### Profile
- **Avatar**: Circular (60px radius) with purple-orange gradient
- **Stats**: White cards with purple borders and gradient text
- **Meta Items**: Purple pale background with rounded corners

### Activity Feed
- **Items**: White cards with purple borders and rounded corners
- **Unread**: Purple left border with purple pale background

### Notifications
- **Badge**: Orange circular badge with white text
- **Panel**: Rounded 16px with purple pale border
- **Actor Links**: Purple text

### Sessions
- **Cards**: White with purple borders, rounded 16px
- **Status Badges**: Purple pale for scheduled
- **Hover**: Lifts with purple shadow

### Footer
- **Background**: Same purple-to-orange gradient as header
- **Text**: White

## Visual Effects

### Hover States
- Cards lift 6px with enhanced purple-tinted shadows
- Buttons translate up 2px
- Links change from purple to orange
- Backgrounds gain subtle purple tint

### Focus States
- 3px purple pale ring around inputs
- Clear visual feedback with purple accent

### Gradient Text
- Used for stat values and attendance counts
- Creates eye-catching focal points
- Linear gradient from purple to orange with background-clip

## Accessibility
- Maintained high contrast ratios
- Clear focus indicators
- Readable text sizes maintained
- Colorblind-friendly with shape + color combinations

## Preview
To see the theme live:
1. Navigate to `http://localhost:8000` in your browser
2. Or open `/theme_preview.html` for a static preview
3. The theme is fully responsive and works across all page types

## Key Changes from Previous Theme
| Element | Old Theme | New Theme |
|---------|-----------|-----------|
| Primary Color | Blue (#2563EB) | Purple (#7C3AED) |
| Accent Color | Yellow (#FCD34D) | Orange (#F97316) |
| Border Radius | 0 (sharp) | 12-24px (rounded) |
| Header | White with blue border | Purple-orange gradient |
| Footer | Gray with blue border | Purple-orange gradient |
| Shadows | Basic black shadows | Purple-tinted glows |
| Background | Pure white | Warm off-white |
| Cards | Sharp with left accent | Rounded with border |
| Buttons | Sharp rectangles | Rounded pills |

## Implementation
All changes are in `/static/style.css` using CSS custom properties for easy theming.

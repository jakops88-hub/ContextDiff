# ContextDiff Frontend Playground

**Next.js 14 Interactive Demo for Semantic Text Analysis**

Modern, enterprise-grade playground frontend for the ContextDiff API with production-ready UI components and advanced features.

## ✨ Features

### Core Functionality
- 🎨 **Enterprise UI** - Tailwind CSS + Shadcn UI components
- 🔍 **3-Column Diff Viewer** - Context-aware highlighting with click-to-inspect
- 📊 **Enterprise Dashboard** - Risk metrics, severity breakdown, status indicators
- 🎯 **Inspector Panel** - Detailed change analysis with JSON/MD export
- ⚡ **Real-time Analysis** - Live progress tracking with streaming effects
- 📱 **Fully Responsive** - Dynamic 4-4-4 grid layout

### Advanced Features
- **Context-Aware Highlighting**: 3-strategy matching algorithm
- **Overlap Detection**: Prevents duplicate highlighting
- **Toast Notifications**: User feedback for all actions
- **Keyboard Shortcuts**: ESC to close inspector
- **Confidence Badges**: Dynamic confidence indicators
- **Copy/Export**: One-click JSON copy and Markdown export

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Your ContextDiff Python backend running on `http://localhost:8000`

### Installation

1. Install dependencies:

```bash
npm install
```

2. Create environment file:

```bash
cp .env.local.example .env.local
```

3. Update `.env.local` with your API URL (default is `http://localhost:8000`).

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

## Deploy to Vercel

The easiest way to deploy is using [Vercel](https://vercel.com):

1. Push your code to GitHub
2. Import the project in Vercel
3. Set the environment variable `NEXT_PUBLIC_API_URL` to your production API URL
4. Deploy!

## Tech Stack

- **Framework:** Next.js 14 (App Router)
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **HTTP Client:** Axios
- **Type Safety:** TypeScript

## Project Structure

```
playground/
├── app/
│   ├── page.tsx          # Main playground page
│   ├── layout.tsx        # Root layout
│   └── globals.css       # Global styles
├── components/
│   ├── ui/               # Reusable UI components
│   ├── AnalysisProgress.tsx
│   ├── ResultsSummary.tsx
│   └── DiffViewer.tsx
├── hooks/
│   └── useSimulatedProgress.ts
├── lib/
│   ├── api.ts            # API client & types
│   └── utils.ts          # Utility functions
└── public/               # Static assets
```

## Customization

### Change API Endpoint

Edit `lib/api.ts`:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
```

### Modify Colors

Edit `tailwind.config.ts` to customize the color scheme.

### Adjust Progress Steps

Edit `hooks/useSimulatedProgress.ts` to change the analysis steps.

## License

MIT

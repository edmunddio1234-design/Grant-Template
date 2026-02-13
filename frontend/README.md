# FOAM Grant Alignment Engine - Frontend

A professional React-based dashboard for managing grant applications and alignment with organizational boilerplate content.

## Features

- **Dashboard**: Overview of RFPs, boilerplate sections, crosswalks, and plans
- **Boilerplate Manager**: Create, edit, and organize reusable content sections
- **RFP Upload & Parse**: Upload and automatically parse grant requirements from PDF/DOCX
- **Crosswalk Engine**: Map RFP requirements to existing boilerplate content with risk scoring
- **Grant Plan Generator**: Generate structured grant application plans from RFPs
- **Gap & Risk Dashboard**: Identify and prioritize gaps and risks in applications
- **AI Draft Framework**: Generate application outlines with AI-powered suggestions

## Tech Stack

- **React 18.2**: UI framework
- **Vite 5.0**: Build tool and dev server
- **Tailwind CSS 3.4**: Styling
- **Zustand 4.4**: State management
- **Recharts 2.10**: Data visualization
- **Lucide React 0.303**: Icon library
- **Axios 1.6**: HTTP client
- **React Router 6.21**: Client-side routing
- **React Hot Toast 2.4**: Notifications
- **React Dropzone 14.2**: File uploads
- **Date-fns 3.2**: Date utilities

## Getting Started

### Prerequisites

- Node.js 16+ and npm/yarn

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:3000` with API proxy to `http://localhost:8000`

### Production Build

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js              # Axios API client with all endpoints
│   ├── components/
│   │   ├── Layout.jsx             # Main layout wrapper
│   │   ├── Sidebar.jsx            # Navigation sidebar
│   │   ├── Header.jsx             # Top header bar
│   │   └── common/
│   │       ├── DataTable.jsx      # Reusable data table
│   │       ├── Modal.jsx          # Reusable modal dialog
│   │       ├── RiskBadge.jsx      # Risk level badge
│   │       ├── TagList.jsx        # Tag display component
│   │       ├── StatusIndicator.jsx # Status badges
│   │       └── FileUpload.jsx     # Drag-drop file upload
│   ├── pages/
│   │   ├── Dashboard.jsx          # Home dashboard
│   │   ├── BoilerplateManager.jsx # Boilerplate management
│   │   ├── RFPUpload.jsx          # RFP upload & parsing
│   │   ├── CrosswalkEngine.jsx    # Requirement mapping
│   │   ├── GrantPlanGenerator.jsx # Plan generation
│   │   ├── GapRiskDashboard.jsx   # Risk analysis
│   │   └── AIDraftFramework.jsx   # AI-assisted drafting
│   ├── stores/
│   │   └── appStore.js            # Zustand state management
│   ├── App.jsx                    # Root component with routing
│   ├── main.jsx                   # React entry point
│   └── index.css                  # Global styles + Tailwind
├── index.html                     # HTML entry point
├── vite.config.js                 # Vite configuration
├── tailwind.config.js             # Tailwind customization
├── postcss.config.js              # PostCSS configuration
└── package.json                   # Dependencies & scripts
```

## Color Scheme

- **Primary**: #0F2C5C (FOAM Blue)
- **Secondary**: #1E4D8C (Darker Blue)
- **Accent**: #3B82F6 (Light Blue)
- **Success**: #22C55E (Green)
- **Warning**: #F59E0B (Amber)
- **Danger**: #EF4444 (Red)

## API Integration

All API calls are made through `/src/api/client.js`. Configure the API base URL in your environment:

```bash
VITE_API_URL=http://localhost:8000/api
```

The client includes:
- Automatic request/response interceptors
- Error handling with toast notifications
- All backend endpoints pre-configured

## State Management

Using Zustand for global state:
- RFP and plan management
- Boilerplate content caching
- Crosswalk results
- Dashboard data
- UI state (sidebar, active module, notifications)

Access state anywhere:
```javascript
import useAppStore from './stores/appStore'

const { currentRFP, setCurrentRFP } = useAppStore()
```

## Components

### Reusable Components

- **DataTable**: Sortable, paginated tables with search and selection
- **Modal**: Dialog component with customizable size and footer
- **FileUpload**: Drag-drop file upload with validation
- **RiskBadge**: Color-coded risk level indicators
- **StatusIndicator**: Status badges with icons
- **TagList**: Editable tag display with color coding

All components accept props for customization and follow consistent styling patterns.

## Responsive Design

- Mobile-first approach
- Tailwind responsive utilities (sm, md, lg, xl, 2xl)
- Collapsible sidebar on mobile devices
- Optimized table layouts for smaller screens
- Touch-friendly button and input sizes

## Development Guidelines

- Use Tailwind CSS classes for styling (avoid inline styles)
- Import and use custom component library
- Follow component naming conventions (PascalCase for components)
- Use Zustand for state that needs to be shared across modules
- Handle loading and error states visually
- Show toast notifications for user feedback
- Keep API calls organized in `/api/client.js`

## Performance Optimizations

- Code splitting by route
- Image optimization
- CSS purging in production
- Lazy loading where appropriate
- Memoized selectors in Zustand

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Contributing

1. Follow the existing code style and patterns
2. Use TypeScript types where applicable
3. Test responsive behavior across devices
4. Keep components small and focused
5. Document complex logic with comments

## License

© 2024 Fathers On A Mission. All rights reserved.

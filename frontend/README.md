# AttendX Frontend

Face recognition attendance system frontend built with vanilla JavaScript and face-api.js.

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Run Development Server
```bash
npm run dev
```

The app will open at `http://localhost:3000`

### 3. Build for Production
```bash
npm run build
```

Output will be in the `dist/` directory.

### 4. Preview Production Build
```bash
npm run preview
```

## Project Structure

```
frontend/
├── startup.html          # Landing page
├── login.html           # Admin login
├── index.html           # Main attendance interface
├── startup.js           # Landing page logic
├── login.js             # Login logic
├── script-fixed.js      # Main app logic
├── authControl.js       # Authentication utilities
├── cameraModule.js      # Camera and face detection
├── supabaseClient.js    # Supabase configuration
├── theme.js             # Theme switcher
├── theme.css            # Theme styles
├── startup.css          # Landing page styles
└── models/              # face-api.js model files
```

## Features

- Face detection and recognition using face-api.js
- Real-time camera feed with face detection
- Admin authentication with Supabase
- Student attendance marking
- Dark/Light theme support
- Responsive design

## Development

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

### API Proxy

The dev server proxies `/api/*` requests to `http://localhost:5000` (backend).

Example:
- Frontend: `fetch('/api/mark_attendance', ...)`
- Proxied to: `http://localhost:5000/mark_attendance`

### Environment Variables

Create a `.env` file if needed:
```env
VITE_SUPABASE_URL=your_supabase_url
VITE_SUPABASE_KEY=your_supabase_key
VITE_API_URL=http://localhost:5000
```

Access in code:
```javascript
const apiUrl = import.meta.env.VITE_API_URL
```

## Browser Requirements

- Modern browser with WebRTC support (Chrome, Firefox, Edge, Safari)
- Camera access permission
- JavaScript enabled

## Troubleshooting

### Camera not working
- Check browser permissions
- Ensure HTTPS or localhost (required for camera access)
- Try a different browser

### Models not loading
- Check that `models/` directory contains all face-api.js model files
- Verify network tab for 404 errors
- Models should be in the public directory

### CORS errors
- Ensure backend is running on port 5000
- Check CORS configuration in backend
- Use the proxy configuration in vite.config.js

## Production Deployment

1. Build the project:
   ```bash
   npm run build
   ```

2. Deploy the `dist/` folder to your hosting service:
   - Netlify
   - Vercel
   - GitHub Pages
   - Any static hosting

3. Update API URL in production environment

## Dependencies

- **Vite**: Fast development server and build tool
- **face-api.js**: Face detection and recognition
- **@supabase/supabase-js**: Supabase client library

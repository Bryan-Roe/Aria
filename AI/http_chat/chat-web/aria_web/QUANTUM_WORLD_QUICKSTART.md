# Quick Start Guide - Quantum World 3D

## Start the Server

```bash
cd /workspaces/AI/aria_web
python server.py
```

Server runs on: `http://localhost:8080`

## Access the 3D World

### Main Quantum World Page
Open in browser: `http://localhost:8080/quantum-world.html`

### Features Available

1. **Generate World Button** (🌍)
   - Select theme from dropdown
   - Set object count (4-16)
   - Optional seed for reproducibility
   - Toggle quantum generation on/off
   - Click to generate

2. **Visualize Circuit Button** (📊)
   - Shows quantum circuit visualization
   - Displays qubits and gates
   - Interactive hover effects

3. **Generated Objects**
   - Click any object to see its details
   - Objects fade in with animation
   - Quantum objects have special glow effect
   - Hover to see scale effect

4. **Info Panel**
   - Shows generation theme
   - Object count
   - Generation method (quantum/classical)
   - Seed value if used
   - Qubit information

## Themes

- ⚛️ **Quantum** - Abstract quantum states
- 🌳 **Nature** - Forest, plants, animals
- 🚀 **Space** - Stars, planets, galaxies
- 🌊 **Ocean** - Water creatures, coral
- 💻 **Tech** - Robots, servers, circuits

## Testing

Run test suite: `http://localhost:8080/test-quantum-world.html`

Tests verify:
- JavaScript functionality
- API endpoint connectivity
- Render function performance
- Object interaction

## Troubleshooting

### Page won't load
- Check server is running: `curl http://localhost:8080/`
- Verify port 8080 is not in use: `lsof -i :8080`

### Objects don't appear
- Check browser console for errors (F12)
- Try different theme
- Clear browser cache (Ctrl+Shift+Del)

### API calls fail
- Verify server is running
- Check network tab in DevTools
- Try test suite first

### Performance issues
- Reduce object count
- Close other browser tabs
- Check GPU usage with `nvidia-smi`

## Advanced Options

### Custom Seed
Enter number in "Seed" field for reproducible worlds
- Same seed + theme = same world layout
- Useful for testing

### Classical Generation
Uncheck "Use Quantum Generation" for faster rendering
- Uses rule-based algorithms instead
- Good for testing without quantum libraries

### Browser DevTools
Press F12 to:
- Check console for errors
- Monitor API responses
- Profile performance
- Test individual functions

## Code Structure

```
aria_web/
├── quantum-world.html          # Main 3D world page
├── server.py                   # Backend server
├── test-quantum-world.html     # Test suite
└── QUANTUM_WORLD_FIXES.md      # This documentation
```

## API Endpoints (Internal)

- `POST /api/aria/world` - Generate world
- `POST /api/aria/quantum/circuit` - Visualize circuit
- `GET /api/aria/state` - Get current state

See `server.py` lines 1086-1220 for implementation.

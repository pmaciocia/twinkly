# Twinkly effects and visualiser 🎄

**Short description**

Generate LED effects for Twinkly-style Christmas lights and preview them locally using a simple Pygame visualiser. The project can also assemble frames into "movies" that can be uploaded to a Twinkly device using the `xled` library.

---

## Requirements 🔧

- Python 3.12+
- See `pyproject.toml` for dependencies (numpy, pygame, colorist, noise, xled, ...)

## Quick start ▶️

using `uv`

This project is managed using `uv` for environment/task management. After installing `uv` you can install dependencies and run commands inside the `uv` environment.

```bash
# install uv (if not already installed)
pip install uv

# install dependencies into the uv-managed environment
uv sync

# run the visualiser inside the uv environment
uv run main.py
```

**Visualizer controls:**
- `+` / `-` to zoom in/out
- Arrow keys to pan
- `ESC` or window close to quit

---

## Streaming to a Twinkly device ⚡

To upload a generated movie to a Twinkly device, set the `ip` and `hw` variables in `main.py` (or use `find_client()` to auto-discover). Use `create_movie()` to assemble frames and `upload_movie()` to send the movie to the device.

Example (in `main.py`):

```py
# set ip, hw
movie = create_movie(frames=600, gen=gen)
# upload_movie(d=get_client(), name="sweep", movie_array=movie, fps=100)
```

---

## Notes / Development 💡

- `gen.py` contains several frame generators (sweeps, rainbow, Perlin noise, random tree layout).
- `display.py` provides a simple Pygame-based visualiser used by `main.py`.
- `points.py` has small helpers used by the frame generators.

Contributions and improvements welcome.

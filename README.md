# AnthroHPK App

This repository contains a FastAPI + Gradio implementation of the AnthroHPK nutritional status calculator for children aged 0–5 years.  It is adapted from the original Colab notebook and packaged as a web app that can be deployed to a platform such as [Render](https://render.com) and wrapped into an Android Trusted Web Activity (TWA) for distribution.

## Features

- Calculate WHO and Indonesian Ministry of Health (Permenkes) z‑scores for weight‑for‑age (WAZ), height/length‑for‑age (HAZ), weight‑for‑length (WHZ), BMI‑for‑age (BAZ), and head circumference‑for‑age (HCZ).
- Detailed PDF report generation with charts and classification.
- Interactive Gradio user interface suitable for parents and health workers.
- FastAPI backend to serve the Gradio UI and required static files (manifest, assetlinks).
- Files for Progressive Web App (PWA) and TWA compatibility.

## Deployment

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Run locally**

   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```

   Then open `http://localhost:8000/` in your browser.  The Gradio interface will appear.

3. **Deploy to Render**

   - Create a new Web Service on Render and connect this repository.
   - Set the Build command to `pip install -r requirements.txt` (Render does this automatically for Python services).
   - Set the Start command to:

     ```
     uvicorn app:app --host 0.0.0.0 --port $PORT
     ```

   - Ensure that the service is running.  The endpoints `/` and `/static/manifest.json` should return the Gradio UI and manifest respectively.  The file `/.well-known/assetlinks.json` must return a 200 OK with the correct SHA‑256 fingerprint once you update the placeholder.

4. **Generate Android APK (TWA)**

   - Install Node.js and the [Bubblewrap CLI](https://github.com/GoogleChromeLabs/bubblewrap).
   - Run `bubblewrap init --manifest=https://your-service.onrender.com/static/manifest.json` and create a new keystore.
   - Update `/.well-known/assetlinks.json` with the SHA‑256 fingerprint of your keystore, commit the change, and redeploy.
   - Build and install the TWA with `bubblewrap build` and `bubblewrap install`.

## License

This project is distributed under the MIT License.  See `LICENSE` for details.

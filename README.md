## SmartLight – Voice‑enabled Smart Home Backend & Frontend

### 1. Backend setup

1. **Create and activate a virtualenv**
   ```bash
   cd DjangoBackLight
   python3 -m venv env
   source env/bin/activate
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` from the example**
   In the project root (`DjangoBackLight/`) create a `.env` file based on this example:

   ```bash
   # .env.example
   DJANGO_SECRET_KEY="change-me"
   DEBUG=True

   # Gemini voice agent configuration
   GEMINI_API_KEY="your-gemini-api-key"
   GEMINI_ENDPOINT="https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent"
   ```

   Copy this into `.env` and fill in real values where needed.

4. **Apply database migrations**
   ```bash
   python3 manage.py migrate
   ```

### 2. Frontend setup

1. **Install Node dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Run the Vite dev server**
   ```bash
   npm run dev
   ```

   The frontend uses `VITE_API_BASE_URL` (defaulting to `http://localhost:8000`) to talk to Django.

### 3. Running backend server and MQTT bridge

In one terminal (with the virtualenv activated):

```bash
python3 manage.py runserver
```

In another terminal:

```bash
python3 manage.py run_mqtt
```

Make sure Redis (or your configured channel layer backend) is running if required by your environment.



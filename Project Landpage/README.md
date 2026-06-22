# LOAN XAI SYSTEM - Project Landing Page

This folder contains a premium, static, responsive landing page for the **LOAN XAI SYSTEM**. It features a project summary, an interactive system architecture modal, a developer directory, and an access portal that integrates with a Supabase database to log entries before granting access to the main underwriting dashboard.

---

## 🛠️ Supabase Database Setup

To capture visitor access logs in real-time, configure a table in your Supabase project:

1. **Create a Table:**
   Go to the **SQL Editor** in your Supabase dashboard and run the following script to create a `logins` table:
   
   ```sql
   create table logins (
     id bigint generated always as identity primary key,
     username text not null,
     email text not null,
     created_at timestamp with time zone default timezone('utc'::text, now()) not null
   );
   
   -- Enable Row Level Security (RLS) if you want to restrict access, 
   -- or configure public insert policies to allow frontend submissions:
   alter table logins enable row level security;
   
   create policy "Allow Public Insert" 
   on logins for insert 
   with check (true);
   ```

2. **Configure API Keys:**
   - In your Supabase dashboard, navigate to **Settings** -> **API**.
   - Copy your **Project URL** and **API Public Anon Key**.
   - Open [app.js](file:///d:/Programming/depi_loan_default_xai/Project%20Landpage/app.js) and substitute the values at lines 9 and 10:
     ```javascript
     const SUPABASE_URL = "https://your-supabase-id.supabase.co";
     const SUPABASE_ANON_KEY = "your-public-anon-key-string";
     ```

*Note: If no Supabase API keys are set, the gateway will gracefully fallback to local mock mode (saving logs inside the browser's `localStorage` and automatically redirecting) to ensure the landing page never breaks.*

---

## 🚀 Separate Deploy on Render (Static Site)

Since this landing page is built using static assets (HTML, CSS, and JS), it can be deployed on Render as a **Static Site** for free.

Follow these steps to deploy:

1. **Sign In to Render:**
   Go to **[https://dashboard.render.com](https://dashboard.render.com)**.

2. **Create a New Static Site:**
   - Click **New +** -> **Static Site**.
   - Choose your GitHub repository (`depi_loan_default_xai`).

3. **Configure Deployment Settings:**
   - **Name:** `loan-xai-landing` (or any custom name)
   - **Branch:** `main`
   - **Build Command:** *Leave empty* (no build step is required for static HTML/CSS/JS)
   - **Publish Directory:** `Project Landpage` *(Crucial: This tells Render to only publish files inside this sub-folder)*

4. **Deploy:**
   - Click **Create Static Site**.
   - Once the deploy completes, Render will provide you with a public URL (e.g., `https://loan-xai-landing.onrender.com`).

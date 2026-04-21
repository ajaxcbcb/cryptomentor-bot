CREATE TABLE IF NOT EXISTS public.testimonials (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name          text NOT NULL,
  role          text NOT NULL DEFAULT '',
  avatar_url    text,
  message       text NOT NULL,
  rating        integer NOT NULL DEFAULT 5 CHECK (rating BETWEEN 1 AND 5),
  is_visible    boolean NOT NULL DEFAULT true,
  display_order integer NOT NULL DEFAULT 0,
  created_at    timestamptz NOT NULL DEFAULT now(),
  updated_at    timestamptz NOT NULL DEFAULT now()
);

-- Index for the public listing query (visible + ordered)
CREATE INDEX IF NOT EXISTS idx_testimonials_visible_order
  ON public.testimonials (is_visible, display_order, created_at DESC);

-- Enable Row Level Security
ALTER TABLE public.testimonials ENABLE ROW LEVEL SECURITY;

-- Make policy creation idempotent for reruns
DROP POLICY IF EXISTS "Public can read visible testimonials" ON public.testimonials;
DROP POLICY IF EXISTS "Service role full access" ON public.testimonials;

-- Public read policy (only visible rows)
CREATE POLICY "Public can read visible testimonials"
  ON public.testimonials FOR SELECT
  USING (is_visible = true);

-- Service role has full access (used by the FastAPI backend with service key)
CREATE POLICY "Service role full access"
  ON public.testimonials FOR ALL
  USING (auth.role() = 'service_role');

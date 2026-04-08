-- ============================================================
-- CortexCart Supabase Schema – AI Decision Engine for Shopping
-- ============================================================

-- Enable pgvector for embedding similarity search
create extension if not exists vector;

-- ─── Products Table ──────────────────────────────────────────
create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  brand text,
  category text,
  department text,
  gender_label text,
  price numeric default 0,
  retail_price numeric default 0,
  discount_pct numeric default 0,
  rating numeric default 0,
  stock_status text default 'IN_STOCK',
  image_url text,
  description_short text,
  description_complete text,
  attributes jsonb default '{}',
  created_at timestamp with time zone default now()
);

-- ─── Product Embeddings (vector similarity) ──────────────────
create table if not exists product_embeddings (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id) on delete cascade unique,
  embedding vector(384),  -- sentence-transformers all-MiniLM-L6-v2 dimension
  created_at timestamp with time zone default now()
);

-- Index for fast vector search
create index if not exists idx_product_embeddings_vector
  on product_embeddings using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

-- ─── Users Table ─────────────────────────────────────────────
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  session_id text unique not null,  -- anonymous session tracking
  email text,
  created_at timestamp with time zone default now()
);

-- ─── User Activity (behavior tracking) ──────────────────────
create table if not exists user_activity (
  id uuid primary key default gen_random_uuid(),
  session_id text not null,
  product_id uuid references products(id) on delete cascade,
  action text not null check (action in ('view', 'like', 'search', 'click_similar')),
  metadata jsonb default '{}',
  created_at timestamp with time zone default now()
);

create index if not exists idx_user_activity_session
  on user_activity(session_id, created_at desc);

create index if not exists idx_user_activity_product
  on user_activity(product_id);

-- ─── Similarity Search Function ──────────────────────────────
create or replace function match_products(
  query_embedding vector(384),
  match_count int default 10,
  filter_category text default null
)
returns table (
  id uuid,
  title text,
  brand text,
  category text,
  department text,
  price numeric,
  retail_price numeric,
  discount_pct numeric,
  rating numeric,
  image_url text,
  description_short text,
  stock_status text,
  gender_label text,
  similarity float
)
language sql stable
as $$
  select
    p.id,
    p.title,
    p.brand,
    p.category,
    p.department,
    p.price,
    p.retail_price,
    p.discount_pct,
    p.rating,
    p.image_url,
    p.description_short,
    p.stock_status,
    p.gender_label,
    1 - (pe.embedding <=> query_embedding) as similarity
  from product_embeddings pe
  join products p on p.id = pe.product_id
  where (filter_category is null or p.category = filter_category)
  order by pe.embedding <=> query_embedding
  limit match_count;
$$;

-- ─── Personalized: Get user embedding from behavior ──────────
create or replace function get_user_product_ids(
  p_session_id text,
  p_limit int default 20
)
returns table (product_id uuid)
language sql stable
as $$
  select distinct ua.product_id
  from user_activity ua
  where ua.session_id = p_session_id
    and ua.action in ('view', 'like')
    and ua.product_id is not null
  order by max(ua.created_at) desc
  limit p_limit;
$$;

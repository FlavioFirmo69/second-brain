BEGIN;
ALTER TABLE sb2_sales ADD COLUMN IF NOT EXISTS from_inventory boolean NOT NULL DEFAULT false;
CREATE TABLE IF NOT EXISTS sb2_stock_purchases (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES sb2_users(id),
 book_id uuid NOT NULL REFERENCES sb2_books(id),
 purchase_date date NOT NULL,
 quantity integer NOT NULL CHECK(quantity>0),
 created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE sb2_stock_purchases ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS sb2_stock_purchases_book ON sb2_stock_purchases(book_id);
COMMIT;

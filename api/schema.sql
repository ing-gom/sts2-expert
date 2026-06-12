-- STS2 Expert community votes (Cloudflare D1 / SQLite)
CREATE TABLE IF NOT EXISTS votes (
  kind  TEXT    NOT NULL,           -- 'cards' | 'relics' | 'potions'
  item  TEXT    NOT NULL,           -- card id (CARD.X) / relic key / potion key
  grade TEXT    NOT NULL,           -- 'S'|'A'|'B'|'C'|'D'
  voter TEXT    NOT NULL,           -- client-generated UUID (localStorage)
  ts    INTEGER NOT NULL,           -- epoch ms of last (re)vote
  PRIMARY KEY (kind, item, voter)   -- one standing vote per voter per item
);
CREATE INDEX IF NOT EXISTS idx_votes_item ON votes (kind, item);

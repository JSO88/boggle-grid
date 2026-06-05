from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import random
import os

app = FastAPI()

# Allow requests from any origin (your game frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

# ── Letter frequencies (from your original script) ──────────────────────────
LETTER_FREQ = {
    'A': 13.268, 'E': 11.122, 'O': 8.691, 'R': 8.659, 'I': 7.670,
    'S': 7.112,  'N': 6.698,  'T': 5.278, 'C': 4.759, 'L': 4.351,
    'D': 4.294,  'M': 3.253,  'U': 2.866, 'P': 2.542, 'B': 1.698,
    'G': 1.667,  'V': 1.265,  'H': 1.109, 'F': 0.981, 'J': 0.547,
    'Y': 0.495,  'Z': 0.468,  'K': 0.354, 'Q': 0.276, 'X': 0.221,
    'W': 0.199,  'Ñ': 0.141,
}

# ── Load word list once at startup ──────────────────────────────────────────
WORD_LIST = []
WORDS_FILE = os.path.join(os.path.dirname(__file__), "words.txt")
if os.path.exists(WORDS_FILE):
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        WORD_LIST = [line.strip().upper() for line in f if line.strip()]
    print(f"✓ Loaded {len(WORD_LIST):,} words")
else:
    print("⚠ words.txt not found — word validation will be empty")


# ── Grid generation (your original function) ─────────────────────────────────
def generate_boggle_grid(frequencies, size=4):
    letters  = list(frequencies.keys())
    weights  = list(frequencies.values())
    pool     = random.choices(letters, weights=weights, k=1000)
    selected = random.sample(pool, size * size)
    return [selected[i:i + size] for i in range(0, size * size, size)]


# ── Trie (your original implementation) ─────────────────────────────────────
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word  = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_word = True


# ── Boggle solver (your original function) ───────────────────────────────────
def solve_boggle(grid, word_list, min_length=3):
    trie = Trie()
    for word in word_list:
        if len(word) >= min_length:
            trie.insert(word.upper())

    rows, cols  = len(grid), len(grid[0])
    found_words = set()
    visited     = [[False] * cols for _ in range(rows)]

    def dfs(r, c, node, current_word):
        if r < 0 or r >= rows or c < 0 or c >= cols or visited[r][c]:
            return
        letter = grid[r][c]
        if letter not in node.children:
            return
        next_node    = node.children[letter]
        current_word = current_word + letter
        if next_node.is_word and len(current_word) >= min_length:
            found_words.add(current_word)
        visited[r][c] = True
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                dfs(r + dr, c + dc, next_node, current_word)
        visited[r][c] = False

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, trie.root, "")

    return sorted(found_words)


# ── API endpoints ─────────────────────────────────────────────────────────────
@app.get("/")

def health():
    return {"status": "ok", "words_loaded": len(WORD_LIST)}


@app.post("/generate")
def generate(min_length: int = 3):
    """
    Generate a new Boggle board and return all valid words on it.
    Query param: min_length (default 3)
    Returns: { board: [[...4 rows of 4 letters...]], valid_words: [...] }
    """
    grid        = generate_boggle_grid(LETTER_FREQ)
    valid_words = solve_boggle(grid, WORD_LIST, min_length=min_length)
    # Flatten grid to a 16-item list for easy Firebase storage
    flat_board  = [letter for row in grid for letter in row]
    return {
        "board":       flat_board,
        "valid_words": valid_words,
        "word_count":  len(valid_words),
    }

# ── Run directly (used by Render via `python main.py`) ────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

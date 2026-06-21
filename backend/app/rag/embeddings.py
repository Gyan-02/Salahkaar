import hashlib
import math
import re


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class DeterministicHashEmbedder:
    """Local deterministic embeddings: no model download, API, or generated text."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        tokens = normalize_tokens(text)
        features = [*tokens, *(f"{a}_{b}" for a, b in zip(tokens, tokens[1:]))]
        vector = [0.0] * self.dimensions
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            value = int.from_bytes(digest, "big")
            index = value % self.dimensions
            sign = 1.0 if value & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


def normalize_tokens(text: str) -> list[str]:
    return [_normalize_token(token) for token in TOKEN_PATTERN.findall(text.casefold())]


def _normalize_token(token: str) -> str:
    aliases = {
        "portability": "portable",
        "eligibility": "eligible",
        "exclusions": "exclusion",
        "excluded": "exclusion",
        "documents": "document",
        "criteria": "criterion",
        "scholarships": "scholarship",
        "pensioners": "pensioner",
    }
    if token in aliases:
        return aliases[token]
    if len(token) > 4 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


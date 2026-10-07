import hashlib
import hmac
import secrets

# Slow on purpose. A person or a program that reads the database sees the hash, not the password.
ITERATIONS = 200_000
LEGACY_ITERATIONS = 200_000
MAX_ITERATIONS = 1_000_000


def hash_password(password: str, salt: str | None = None, iterations: int = ITERATIONS) -> str:
    if salt is None:
        salt = secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    ).hex()
    return f"pbkdf2_sha256${iterations}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4:
        algo, raw_iterations, salt, _digest = parts
        try:
            iterations = int(raw_iterations)
        except ValueError:
            return False
    elif len(parts) == 3:
        # Seed rows were stored before the iteration count was written into the hash.
        algo, salt, _digest = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    if algo != "pbkdf2_sha256" or not salt or iterations < 1 or iterations > MAX_ITERATIONS:
        return False
    candidate = hash_password(password, salt=salt, iterations=iterations)
    return hmac.compare_digest(candidate, _with_iterations(stored, iterations))


# Used when the email is not in the table, so the check still takes one slow hash.
DUMMY_HASH = hash_password("missing-account", salt="notauseraccount1")


def _with_iterations(stored: str, iterations: int) -> str:
    parts = stored.split("$")
    if len(parts) == 4:
        return stored
    algo, salt, digest = parts
    return f"{algo}${iterations}${salt}${digest}"

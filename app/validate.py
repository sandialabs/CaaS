import os

#  Hard coded limits and defaults for resources. May need to be modified if some users
#  are allowed to request above the limits
DEFAULT_CPU = os.getenv("CAAS_API_CPU_REQUEST_DEFAULT", "0.25")
MAX_CPU = os.getenv("CAAS_API_CPU_MAX", "4")

DEFAULT_MEM = os.getenv("CAAS_API_MEM_REQUEST_DEFAULT", "61Mi")
MAX_MEM_REQUEST = os.getenv("CAAS_API_MEM_LIMIT_DEFAULT", "32Gi")
MAX_MEM = os.getenv("CAAS_API_MEM_MAX", "32Gi")

DEFAULT_GPU = os.getenv("CAAS_API_GPU_REQUEST_DEFAULT", "0")
MAX_GPU_REQUEST = os.getenv("CAAS_API_GPU_LIMIT_DEFAULT", "2")
MAX_GPU = os.getenv("CAAS_API_GPU_MAX", "2")


def set_none_if_empty(form_datum):
    """Set form input to None if it comes in as an empty string from the client.

    Additional side effect is that if the form input is "valid" then runs it
    through the `.strip()` method to get rid of any unwanted space, tab and new
    line characters, if the input is a string.
    """
    if form_datum == "":
        return None
    if isinstance(form_datum, str):
        form_datum = form_datum.strip().strip("\n")
    return form_datum


def validate_cpu(cpu):
    if cpu is None or cpu == "":
        return float(DEFAULT_CPU)
    if isinstance(cpu, str) and cpu.endswith("m"):
        try:
            value = float(cpu[:-1]) / 1000
            if not (0 <= value <= float(MAX_CPU)):
                raise ValueError(
                    f"Invalid CPU value. Must request between 0 and {MAX_CPU} CPU."
                )
            return value
        except ValueError:
            raise ValueError(
                "Invalid CPU value. Must request between 0 and 4 CPU."
            ) from None
    try:
        value = int(cpu)
        if not (0 <= value <= int(MAX_CPU)):
            raise ValueError(
                f"Invalid CPU value. Must request between 0 and {MAX_CPU} CPU."
            )
        return value
    except ValueError:
        raise ValueError(
            "Invalid CPU value. Must request between 0 and 4 CPU."
        ) from None


def validate_memory(memory):
    if memory is None or memory == "":
        return DEFAULT_MEM
    if not isinstance(memory, str):
        raise ValueError(f"Invalid memory value. Must request between 0 and {MAX_MEM}.")
    if not memory.endswith(("G", "M", "k", "Gi", "Mi", "Ki")):
        raise ValueError(f"Invalid memory value. Must request between 0 and {MAX_MEM}.")

    suffixes = {
        "G": 1024**3,
        "M": 1024**2,
        "k": 1024,
        "Gi": 1024**3,
        "Mi": 1024**2,
        "Ki": 1024,
    }
    for suffix, multiplier in suffixes.items():
        if memory.endswith(suffix):
            value = float(memory[: -len(suffix)])
            max = float(MAX_MEM_REQUEST[:-2])
            if value * multiplier > max * (1024**3) or value < 0:
                raise ValueError(
                    f"Invalid memory value. Must request between 0 and {MAX_MEM}."
                )
            return memory

    raise ValueError(f"Invalid memory value. Must request between 0 and {MAX_MEM}.")


def validate_gpu(gpu):
    if gpu is None or gpu == "":
        return int(DEFAULT_GPU)
    if isinstance(gpu, str):
        try:
            return int(gpu)
        except ValueError:
            raise ValueError("Invalid GPU value. Must be a valid integer.") from None
    if not isinstance(gpu, int):
        raise ValueError("Invalid GPU value. Must be a valid integer.")
    if not (0 <= gpu <= int(MAX_GPU)):
        raise ValueError(
            f"Invalid GPU value. Must request between 0 and {MAX_GPU} GPU."
        )
    return gpu


def validate_secret(username, token, secret_name):
    """Returns True if the secret belongs to the user, False otherwise.

    The methods validates the secret by ensuring the username is allowed to use
    the input secret, determined by the secret's name. It relies on the
    convention that secret names for Secrets belonging to users follow the
    following convention:

        f"{username}-{token}-{uuid.uuid4().hex[:5]}"

    Args:
        username: string, required.
        token: string, required.
        secret_name: string, required.
    Returns:
        bool
    """
    if (
        type(username) is not str
        or type(token) is not str
        or type(secret_name) is not str
    ):
        return False
    return secret_name.startswith(f"{username}-{token}-")

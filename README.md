# CaaS API

> Computing-as-a-Service API

<br>
The Computing-as-a-Service API provides a common environment for executing containerized workloads. It supports multi-tenant, CPU and GPU jobs.

## Development

Steps for bringing up CaaS API for local development

1. Generate a salt
    ```bash
    # salt should be about 16 or more bytes from a proper source, e.g. os.urandom()
    import os
    print(os.urandom(16).hex())  # use bytes.fromhex() to convert back to bytes
    ```

1. Create a file named under the `scripts` directory named `set_salt.sh`. Make sure to make it executable, via the `chmod u+x` command.
    ```bash
    #!/bin/bash

    export CAAS_API_SALT=badsalt # replace badsalt with the salt generated in Step 1
    ```

1. Initialize the database `sqlite3 app/data/caas.db < schema.sql`

1. In the Makefile, be sure to replace the appropriate `CAAS_API_NAMESPACE` and `CAAS_API_KUBERNETES_URL`

1. Create a virtual environment and install requirements
    ```bash
    python3 -m venv .venv --prompt caas-api
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

1. Export your salt and token
    ```bash
    bash scripts/set_salt.sh
    bash scripts/set_kubernetes.sh
    ```

1. Build and run
    ```bash
    make build # Run this command only for the first time
    make run

    # Note make defaults to podman. If running on a system using docker, use:
    make CONTAINER_CMD=docker build
    make CONTAINER_CMD=docker run
    ```
1. Go to `localhost:8000/api` on your browser

### Additional development tools

```bash
source .venv/bin/activate
pip install -r dev_requirements.txt
pip install -r lint_requirements.txt
```

Use `isort` and `black`, in that order, to format your code before committing
and pushing to the repository.

```bash
make lint
```

### Testing

```bash
source .venv/bin/activate
pip install -r test_requirements.txt
make test
```

## Contributing

1. Branch off `main` for the new feature branch
1. Naming convention for new branches is `##-branch-name`, where `##` is the issue number and `branch-name` is a short description
1. _(Optional) `##` can be omitted if work isn't tied to a specific issue_
1. When done, run `git rebase main` from feature branch
1. __Important: if collaborating on feature branch or it is the source for other branches, use `git merge main` instead__
1. _(Optional) resolve any conflicts_
1. Submit pull request into `main` when ready

## Copyright

Copyright 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

## License

Copyright 2026 National Technology & Engineering Solutions of Sandia, LLC (NTESS). Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains certain rights in this software.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

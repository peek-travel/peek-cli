# **Peek CLI**

A Python-based CLI for interacting with the Peek API. This tool allows you to create publishers, list apps, and perform other actions via an easy-to-use command-line interface.

---

## **Table of Contents**

- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Using the CLI](#using-the-cli)
- [Development and Packaging](#development-and-packaging)
- [Shipping with Homebrew](#shipping-with-homebrew)

---

## **Prerequisites**

1. **Python 3.6+**

   - Ensure you have Python 3.6 or later installed.
   - Check your Python version:
     ```bash
     python --version
     python3 --version
     ```

2. **`tool-versions` Setup (if applicable)**

   - If you’re managing multiple Python environments, ensure your project’s Python version is set:
     ```bash
     asdf local python 3.10.7
     ```

3. **Virtual Environment Setup**
   - Use `venv` for isolating project dependencies:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

---

## **Setup Instructions**

### Clone the Repository

```bash
git clone https://github.com/peek-travel/peek-cli.git
cd peek-cli
```

### Install Dependencies

1. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```
2. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```

### Add Environment Variables

1. Create a `.env` file in the project directory:
   ```bash
   touch .env
   ```
2. Add server URLs for different environments:
   ```dotenv
   SANDBOX_URL=http://sandbox.peek.stack
   LOCAL_URL=http://localhost:8000
   PROD_URL=http://prod.peek.stack
   ```

---

## **Using the CLI**

### Activate the Virtual Environment

```bash
source .venv/bin/activate
```

### Run the CLI

```bash
python cli.py --help
```

### Example Commands

1. **Create a Publisher**

   ```bash
   python cli.py apps publishers create --name "My Publisher" --email "test@example.com" --website-url "https://example.com"
   ```

2. **Create an App**
  ```bash
  python cli.py --api-token PEEK_API_TOKEN apps create --name "My App"
  ```

3. **List Apps**
   ```bash
   python cli.py --api-token PEEK_API_TOKEN apps list
   ```

4. **List Extendables**
  ```bash
  python cli.py --api-token PEEK_API_TOKEN apps extendables list
  ```
  

5. **Add a new Extendable**
   ```bash
   python cli.py apps extendables new --name "webhook_on_booking_created@v1" --app-id APP_ID --version VERSION_ID
   ```
---

## **Development and Packaging**

### Run Tests

Use `pytest` to run tests for the CLI:

```bash
pytest tests/
```

### Bundle the CLI

1. Generate a Python package:

   ```bash
   python setup.py sdist bdist_wheel
   ```

2. Check the generated distribution files in the `dist/` directory.

3. Test the package installation locally:
   ```bash
   pip install dist/peek_cli-0.1-py3-none-any.whl
   peek --help
   ```

---

## **Shipping with Homebrew**

### Step 1: Publish to GitHub

1. Push the repository to a public GitHub repo.
2. Tag the release:
   ```bash
   git tag -a v0.1 -m "Initial release"
   git push origin v0.1
   ```

### Step 2: Generate Homebrew Formula

1. Create a formula file (`peek-cli.rb`):

   ```ruby
   class PeekCli < Formula
     desc "CLI for interacting with the Peek API"
     homepage "https://github.com/peek-travel/peek-cli"
     url "https://github.com/peek-travel/peek-cli/archive/refs/tags/v0.1.tar.gz"
     sha256 "CHECKSUM_OF_TARBALL"
     license "MIT"

     depends_on "python@3.9"

     def install
       virtualenv_install_with_resources
     end
   end
   ```

2. Test the formula locally:
   ```bash
   brew install --build-from-source ./peek-cli.rb
   peek --help
   ```

### Step 3: Create a Tap

1. Create a Homebrew Tap for your repository:
   ```bash
   brew tap peek-travel/peek
   ```
2. Install via the Tap:
   ```bash
   brew install peek-travel/peek/peek-cli
   ```

---

## **Tips for Updating the CLI**

1. Update the version in `setup.py` and `requirements.txt`.
2. Rebuild the package:
   ```bash
   python setup.py sdist bdist_wheel
   ```
3. Push changes and retag the release:
   ```bash
   git add .
   git commit -m "Updated CLI to version 0.2"
   git tag -a v0.2 -m "Updated version"
   git push origin v0.2
   ```

---

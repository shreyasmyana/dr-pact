"""
DR-PACT AI Agent: Contract Test Generator

This is the "brain" of the demo - an AI agent that:
1. Reads TypeScript Consumer source code
2. Reads Python Provider source code to understand validation requirements
3. Analyzes HTTP client interactions and provider constraints
4. Generates Pact contract tests that satisfy provider validation rules

The agent intelligently detects:
- Minimum array length requirements (e.g., len(array) < N checks)
- Required fields and their types
- Error conditions to avoid in happy path tests

Supports multiple LLM providers:
- Google Gemini (FREE - recommended)
- Groq (FREE - fast)
- Ollama (FREE - runs locally)
- OpenAI (paid)
- Anthropic (paid)

Usage:
    python generator.py [--provider gemini|groq|ollama|openai|anthropic] [--verify]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
CONSUMER_DIR = PROJECT_ROOT / "consumer-ts"
PROVIDER_DIR = PROJECT_ROOT / "provider-py"
SOURCE_FILE = CONSUMER_DIR / "src" / "insulinClient.ts"
PROVIDER_FILE = PROVIDER_DIR / "app.py"
OUTPUT_FILE = CONSUMER_DIR / "tests" / "contract.spec.ts"
PROMPT_FILE = SCRIPT_DIR / "prompt.txt"


def load_system_prompt() -> str:
    """Load the system prompt from file."""
    with open(PROMPT_FILE, 'r') as f:
        return f.read()


def load_source_code() -> str:
    """Load the TypeScript source code to analyze."""
    with open(SOURCE_FILE, 'r') as f:
        return f.read()


def load_provider_code() -> str:
    """Load the Python provider code to analyze validation requirements."""
    if PROVIDER_FILE.exists():
        with open(PROVIDER_FILE, 'r') as f:
            return f.read()
    return ""


def call_openai(system_prompt: str, source_code: str, provider_code: str) -> str:
    """Call OpenAI API to generate contract tests."""
    try:
        from openai import OpenAI
    except ImportError:
        print("❌ OpenAI package not installed. Run: pip install openai")
        sys.exit(1)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    client = OpenAI(api_key=api_key)
    
    print("🤖 Calling OpenAI GPT-4o...")
    
    # Get the actual filename (without full path) for the import statement
    consumer_filename = SOURCE_FILE.stem  # e.g., "insulinClient" (without .ts)
    
    user_content = f"""Analyze these files and generate Pact contract tests.

=== CONSUMER (TypeScript Client) ===
FILENAME: {consumer_filename}.ts
IMPORT PATH: ../src/{consumer_filename}

{source_code}

=== PROVIDER (Python API) ===
{provider_code}

Generate contract tests that satisfy the provider's validation requirements.
IMPORTANT: Use the EXACT import path provided above: '../src/{consumer_filename}'"""
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2,  # Low temperature for consistent code generation
        max_tokens=4000
    )
    
    return response.choices[0].message.content


def call_anthropic(system_prompt: str, source_code: str, provider_code: str) -> str:
    """Call Anthropic Claude API to generate contract tests."""
    try:
        import anthropic
    except ImportError:
        print("❌ Anthropic package not installed. Run: pip install anthropic")
        sys.exit(1)
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not set in environment")
        sys.exit(1)
    
    client = anthropic.Anthropic(api_key=api_key)
    
    print("🤖 Calling Anthropic Claude 3.5 Sonnet...")
    
    # Get the actual filename (without full path) for the import statement
    consumer_filename = SOURCE_FILE.stem  # e.g., "insulinClient" (without .ts)
    
    user_content = f"""Analyze these files and generate Pact contract tests.

=== CONSUMER (TypeScript Client) ===
FILENAME: {consumer_filename}.ts
IMPORT PATH: ../src/{consumer_filename}

{source_code}

=== PROVIDER (Python API) ===
{provider_code}

Generate contract tests that satisfy the provider's validation requirements.
IMPORTANT: Use the EXACT import path provided above: '../src/{consumer_filename}'"""
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_content}
        ]
    )
    
    return response.content[0].text


def call_gemini(system_prompt: str, source_code: str, provider_code: str) -> str:
    """Call Google Gemini API to generate contract tests. FREE TIER AVAILABLE!"""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("❌ Google GenAI package not installed. Run: pip install google-genai")
        sys.exit(1)
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set in environment")
        print("💡 Get a FREE API key at: https://aistudio.google.com/app/apikey")
        sys.exit(1)
    
    client = genai.Client(api_key=api_key)
    
    print("🤖 Calling Google Gemini 2.0 Flash (FREE)...")
    
    # Get the actual filename (without full path) for the import statement
    consumer_filename = SOURCE_FILE.stem  # e.g., "insulinClient" (without .ts)
    
    prompt = f"""{system_prompt}

Analyze these files and generate Pact contract tests.

=== CONSUMER (TypeScript Client) ===
FILENAME: {consumer_filename}.ts
IMPORT PATH: ../src/{consumer_filename}

{source_code}

=== PROVIDER (Python API) ===
{provider_code}

Generate contract tests that satisfy the provider's validation requirements.
IMPORTANT: Use the EXACT import path provided above: '../src/{consumer_filename}'"""
    
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=4000,
        )
    )
    
    return response.text


def call_groq(system_prompt: str, source_code: str, provider_code: str) -> str:
    """Call Groq API to generate contract tests. FREE TIER AVAILABLE!"""
    try:
        from groq import Groq
    except ImportError:
        print("❌ Groq package not installed. Run: pip install groq")
        sys.exit(1)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ GROQ_API_KEY not set in environment")
        print("💡 Get a FREE API key at: https://console.groq.com/keys")
        sys.exit(1)
    
    # Create httpx client with SSL verification disabled (for corporate proxies)
    import httpx
    http_client = httpx.Client(verify=False)
    client = Groq(api_key=api_key, http_client=http_client)
    
    print("🤖 Calling Groq Llama 3.3 70B (FREE)...")
    print("⚠️  SSL verification disabled (required for corporate proxies)")
    
    # Get the actual filename (without full path) for the import statement
    consumer_filename = SOURCE_FILE.stem  # e.g., "insulinClient" (without .ts)
    
    user_content = f"""Analyze these files and generate Pact contract tests.

=== CONSUMER (TypeScript Client) ===
FILENAME: {consumer_filename}.ts
IMPORT PATH: ../src/{consumer_filename}

{source_code}

=== PROVIDER (Python API) ===
{provider_code}

Generate contract tests that satisfy the provider's validation requirements.
IMPORTANT: Use the EXACT import path provided above: '../src/{consumer_filename}'"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2,
        max_tokens=4000
    )
    
    return response.choices[0].message.content


def call_ollama(system_prompt: str, source_code: str, provider_code: str) -> str:
    """Call Ollama local API to generate contract tests. COMPLETELY FREE - runs locally!"""
    try:
        import requests
    except ImportError:
        print("❌ Requests package not installed. Run: pip install requests")
        sys.exit(1)
    
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    print(f"🤖 Calling Ollama {model} (LOCAL - FREE)...")
    print(f"   URL: {ollama_url}")
    
    # Check if Ollama is running
    try:
        requests.get(f"{ollama_url}/api/tags", timeout=5)
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running!")
        print("💡 Start Ollama with: ollama serve")
        print("💡 Then pull a model: ollama pull llama3.2")
        sys.exit(1)
    
    # Get the actual filename (without full path) for the import statement
    consumer_filename = SOURCE_FILE.stem  # e.g., "insulinClient" (without .ts)
    
    prompt = f"""{system_prompt}

Analyze these files and generate Pact contract tests.

=== CONSUMER (TypeScript Client) ===
FILENAME: {consumer_filename}.ts
IMPORT PATH: ../src/{consumer_filename}

{source_code}

=== PROVIDER (Python API) ===
{provider_code}

Generate contract tests that satisfy the provider's validation requirements.
IMPORTANT: Use the EXACT import path provided above: '../src/{consumer_filename}'"""
    
    response = requests.post(
        f"{ollama_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 4000
            }
        },
        timeout=300  # 5 min timeout for local generation
    )
    
    if response.status_code != 200:
        print(f"❌ Ollama error: {response.text}")
        sys.exit(1)
    
    return response.json()["response"]


def clean_response(response: str) -> str:
    """Clean up the LLM response to get pure TypeScript code."""
    import re
    
    # Try to extract code from markdown code blocks first
    # Match ```typescript or ``` followed by code
    code_block_pattern = r'```(?:typescript|ts)?\s*\n(.*?)```'
    matches = re.findall(code_block_pattern, response, re.DOTALL)
    
    if matches:
        # Return the first (or longest) code block
        code = max(matches, key=len)
        return code.strip()
    
    # If no code blocks found, try to extract just the TypeScript code
    lines = response.strip().split('\n')
    
    # Find where the actual code starts (import statement)
    start_idx = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import '):
            start_idx = i
            break
    
    # Find where the code ends (last closing brace or semicolon)
    end_idx = len(lines)
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line == '});' or line == '}' or line.endswith(';'):
            end_idx = i + 1
            break
    
    # Extract the code portion
    code_lines = lines[start_idx:end_idx]
    
    # Remove any remaining markdown artifacts
    cleaned_lines = []
    for line in code_lines:
        if line.strip().startswith('```'):
            continue
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)


def validate_and_fix_code(code: str) -> tuple[str, list[str]]:
    """
    Validate generated code and fix common LLM mistakes.
    Returns (fixed_code, list_of_fixes_applied).
    
    This catches patterns that LLMs hallucinate but don't exist in Pact V3.
    """
    import re
    
    fixes = []
    fixed_code = code
    
    # ═══════════════════════════════════════════════════════════════════
    # FORBIDDEN PATTERNS - Things LLMs hallucinate that don't exist
    # ═══════════════════════════════════════════════════════════════════
    
    forbidden_patterns = [
        # Matchers that don't exist in Pact V3
        (r'MatchersV3\.oneOf\s*\([^)]+\)', 'MatchersV3.oneOf() does not exist'),
        (r'MatchersV3\.anyOf\s*\([^)]+\)', 'MatchersV3.anyOf() does not exist'),
        (r'MatchersV3\.enum\s*\([^)]+\)', 'MatchersV3.enum() does not exist'),
        (r'MatchersV3\.regex\s*\([^)]+\)', 'MatchersV3.regex() - use MatchersV3.term() instead'),
        (r'MatchersV3\.uuid\s*\([^)]*\)', 'MatchersV3.uuid() does not exist'),
        (r'MatchersV3\.date\s*\([^)]+\)', 'MatchersV3.date() does not exist'),
        (r'MatchersV3\.timestamp\s*\([^)]+\)', 'MatchersV3.timestamp() does not exist'),
        (r'MatchersV3\.datetime\s*\([^)]+\)', 'MatchersV3.datetime() does not exist'),
        (r'MatchersV3\.nullValue\s*\([^)]*\)', 'MatchersV3.nullValue() does not exist'),
        (r'MatchersV3\.integer\s*\([^)]*\)', 'MatchersV3.integer() - use MatchersV3.number() instead'),
        (r'MatchersV3\.decimal\s*\([^)]*\)', 'MatchersV3.decimal() - use MatchersV3.number() instead'),
        (r'MatchersV3\.float\s*\([^)]*\)', 'MatchersV3.float() - use MatchersV3.number() instead'),
        
        # Jest assertions that don't exist
        (r'\.toBeOneOf\s*\([^)]+\)', 'toBeOneOf() does not exist in Jest'),
        (r'\.toBeAnyOf\s*\([^)]+\)', 'toBeAnyOf() does not exist in Jest'),
        (r'\.toMatchOneOf\s*\([^)]+\)', 'toMatchOneOf() does not exist in Jest'),
        
        # Wrong Pact config options
        (r'pactDir\s*:', 'pactDir should be "dir"'),
        (r'pactfileWriteMode\s*:', 'pactfileWriteMode should be "pactFilesWriteMode"'),
    ]
    
    errors = []
    for pattern, message in forbidden_patterns:
        if re.search(pattern, fixed_code):
            errors.append(f"❌ FORBIDDEN: {message}")
    
    if errors:
        print("\n⚠️  LLM generated invalid patterns:")
        for error in errors:
            print(f"   {error}")
        print("\n   Attempting automatic fixes...")
    
    # ═══════════════════════════════════════════════════════════════════
    # AUTO-FIXES - Replace bad patterns with correct ones
    # ═══════════════════════════════════════════════════════════════════
    
    # Fix: oneOf() with strings → use string() with first value as example
    oneOf_string_pattern = r"MatchersV3\.oneOf\s*\(\s*\[(.*?)\]\s*\)"
    matches = re.findall(oneOf_string_pattern, fixed_code)
    for match in matches:
        # Extract first value from the array
        values = [v.strip().strip("'\"") for v in match.split(',')]
        if values:
            first_value = values[0]
            old_pattern = f"MatchersV3.oneOf([{match}])"
            new_pattern = f"MatchersV3.string('{first_value}')"
            fixed_code = fixed_code.replace(old_pattern, new_pattern)
            fixes.append(f"Replaced oneOf() → string('{first_value}')")
    
    # Fix: pactDir → dir
    if 'pactDir:' in fixed_code or 'pactDir :' in fixed_code:
        fixed_code = re.sub(r'pactDir\s*:', 'dir:', fixed_code)
        fixes.append("Replaced pactDir → dir")
    
    # Fix: integer() → number()
    fixed_code = re.sub(r'MatchersV3\.integer\(\)', 'MatchersV3.number()', fixed_code)
    if 'integer()' in code and 'integer()' not in fixed_code:
        fixes.append("Replaced integer() → number()")
    
    # Fix: decimal()/float() → number()
    fixed_code = re.sub(r'MatchersV3\.decimal\(\)', 'MatchersV3.number()', fixed_code)
    fixed_code = re.sub(r'MatchersV3\.float\(\)', 'MatchersV3.number()', fixed_code)
    
    # Fix: toBeOneOf([...]) → toContain() or custom check
    toBeOneOf_pattern = r'expect\(([^)]+)\)\.toBeOneOf\(\[([^\]]+)\]\)'
    matches = re.findall(toBeOneOf_pattern, fixed_code)
    for var, values in matches:
        old = f"expect({var}).toBeOneOf([{values}])"
        # Replace with a check that the value is one of the expected values
        new = f"expect([{values}]).toContain({var})"
        fixed_code = fixed_code.replace(old, new)
        fixes.append(f"Replaced toBeOneOf() → toContain() pattern")
    
    # Fix: eachLike('') or eachLike("") for empty arrays → []
    fixed_code = re.sub(r"MatchersV3\.eachLike\s*\(\s*['\"]['\"]?\s*\)", '[]', fixed_code)
    if "eachLike('')" in code or 'eachLike("")' in code:
        fixes.append("Replaced eachLike('') → [] for empty arrays")
    
    return fixed_code, fixes


def validate_code_strict(code: str) -> list[str]:
    """
    Strict validation that returns errors for patterns that cannot be auto-fixed.
    Returns list of error messages.
    """
    import re
    
    errors = []
    
    # Check for remaining forbidden patterns that couldn't be auto-fixed
    remaining_forbidden = [
        (r'MatchersV3\.oneOf', 'MatchersV3.oneOf() still present after fix attempt'),
        (r'MatchersV3\.anyOf', 'MatchersV3.anyOf() does not exist'),
        (r'MatchersV3\.enum', 'MatchersV3.enum() does not exist'),
        (r'\.toBeOneOf', 'toBeOneOf() still present after fix attempt'),
        (r'\.toBeAnyOf', 'toBeAnyOf() does not exist'),
    ]
    
    for pattern, message in remaining_forbidden:
        if re.search(pattern, code):
            errors.append(message)
    
    return errors


def write_contract_test(code: str):
    """Write the generated contract test to file."""
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        f.write(code)
    
    print(f"✅ Contract test written to: {OUTPUT_FILE}")


def run_tests() -> bool:
    """Run the generated contract tests."""
    print("\n🧪 Running contract tests...")
    print("-" * 50)
    
    result = subprocess.run(
        ["npm", "test"],
        cwd=CONSUMER_DIR,
        capture_output=False
    )
    
    return result.returncode == 0


def print_banner():
    """Print the demo banner."""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🏥 DR-PACT: AI-Driven Contract Test Generator              ║
║                                                               ║
║   Medical Device Safety through Intelligent Testing          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def main():
    parser = argparse.ArgumentParser(description="Generate Pact contract tests using AI")
    parser.add_argument(
        "--provider", 
        choices=["gemini", "groq", "ollama", "openai", "anthropic"],
        default="gemini",
        help="LLM provider to use (default: gemini - FREE)"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run tests after generating"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated code without writing to file"
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Step 1: Load inputs
    print("📖 Loading system prompt...")
    system_prompt = load_system_prompt()
    
    print(f"📄 Loading consumer source code from: {SOURCE_FILE}")
    source_code = load_source_code()
    
    print(f"📄 Loading provider source code from: {PROVIDER_FILE}")
    provider_code = load_provider_code()
    if provider_code:
        print("   ✅ Provider code loaded - will analyze validation requirements")
    else:
        print("   ⚠️ No provider code found - using consumer-only analysis")
    
    # Step 2: Call LLM
    print(f"\n🧠 AI Provider: {args.provider.upper()}")
    print("-" * 50)
    
    if args.provider == "gemini":
        generated_code = call_gemini(system_prompt, source_code, provider_code)
    elif args.provider == "groq":
        generated_code = call_groq(system_prompt, source_code, provider_code)
    elif args.provider == "ollama":
        generated_code = call_ollama(system_prompt, source_code, provider_code)
    elif args.provider == "openai":
        generated_code = call_openai(system_prompt, source_code, provider_code)
    elif args.provider == "anthropic":
        generated_code = call_anthropic(system_prompt, source_code, provider_code)
    else:
        print(f"❌ Unknown provider: {args.provider}")
        sys.exit(1)
    
    # Step 3: Clean and output
    clean_code = clean_response(generated_code)
    
    # Step 3.5: Validate and fix LLM hallucinations
    print("\n🔍 Validating generated code...")
    fixed_code, fixes = validate_and_fix_code(clean_code)
    
    if fixes:
        print(f"   🔧 Applied {len(fixes)} automatic fix(es):")
        for fix in fixes:
            print(f"      • {fix}")
    else:
        print("   ✅ No issues detected")
    
    # Check for remaining errors that couldn't be fixed
    remaining_errors = validate_code_strict(fixed_code)
    if remaining_errors:
        print("\n❌ VALIDATION FAILED - Cannot auto-fix these issues:")
        for error in remaining_errors:
            print(f"   • {error}")
        print("\n💡 Please update the prompt.txt with more specific instructions")
        print("   or manually fix the generated code.")
        if not args.dry_run:
            # Still write the file but warn user
            print("\n⚠️  Writing file anyway - manual fixes may be needed")
    
    if args.dry_run:
        print("\n📝 Generated Contract Test (dry run):")
        print("=" * 50)
        print(fixed_code)
        print("=" * 50)
        return
    
    # Step 4: Write to file
    write_contract_test(fixed_code)
    
    # Step 5: Optionally run tests
    if args.verify:
        success = run_tests()
        if success:
            print("\n✅ All contract tests passed!")
            print("📦 Pact file generated in: ../pacts/")
        else:
            print("\n❌ Contract tests failed!")
            sys.exit(1)
    else:
        print("\n💡 Run 'npm test' in consumer-ts/ to execute the tests")
        print("   Or run this script with --verify flag")


if __name__ == "__main__":
    main()

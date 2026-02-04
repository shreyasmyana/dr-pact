"""
Pact Provider Verification Tests

This test verifies that the Python Provider (RiskAlgoService) 
fulfills all contracts published by consumers.

The Pact file is the SINGLE SOURCE OF TRUTH - it defines the contract
that the provider must satisfy.

Provider verification works by:
1. Starting the provider application
2. Pact Verifier replays ALL interactions from the Pact file
3. Verifier checks that provider responses match the contract

Run with: pytest tests/test_pact.py -v
"""

import pytest
import subprocess
import time
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
PROVIDER_HOST = "localhost"
PROVIDER_PORT = 7001
PROVIDER_URL = f"http://{PROVIDER_HOST}:{PROVIDER_PORT}"
PROJECT_ROOT = Path(__file__).parent.parent.parent
PACTS_DIR = PROJECT_ROOT / "pacts"


class TestProviderVerification:
    """
    Provider contract verification using Pact Verifier.
    
    The Pact file is the ONLY source of truth.
    This test does NOT make any manual HTTP requests.
    All interactions are replayed from the Pact file by the Verifier.
    """
    
    provider_process = None
    
    @classmethod
    def setup_class(cls):
        """Start the provider before running tests."""
        import requests
        
        # Check if provider is already running
        try:
            response = requests.get(f"{PROVIDER_URL}/health", timeout=2)
            if response.status_code == 200:
                print("\n✅ Provider already running")
                cls.provider_process = None
                return
        except requests.exceptions.ConnectionError:
            pass
        
        # Start the provider
        print("\n🚀 Starting provider for verification...")
        provider_app = Path(__file__).parent.parent / "app.py"
        
        cls.provider_process = subprocess.Popen(
            [sys.executable, str(provider_app)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(provider_app.parent)
        )
        
        # Wait for provider to start
        max_retries = 10
        for i in range(max_retries):
            time.sleep(1)
            try:
                response = requests.get(f"{PROVIDER_URL}/health", timeout=2)
                if response.status_code == 200:
                    print(f"✅ Provider started successfully on {PROVIDER_URL}")
                    return
            except requests.exceptions.ConnectionError:
                if i < max_retries - 1:
                    print(f"   Waiting for provider... ({i + 1}/{max_retries})")
        
        pytest.fail("Failed to start provider")
    
    @classmethod
    def teardown_class(cls):
        """Stop the provider after tests complete."""
        if cls.provider_process:
            print("\n🛑 Stopping provider...")
            cls.provider_process.terminate()
            try:
                cls.provider_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.provider_process.kill()
            print("✅ Provider stopped")
    
    def test_provider_satisfies_pact_contract(self):
        """
        Verify provider satisfies ALL consumer contracts.
        
        This is the ONLY test needed for provider verification.
        The Pact Verifier will:
        1. Read ALL interactions from the Pact file
        2. Replay each request against the running provider
        3. Verify responses match the contract expectations
        
        NO manual HTTP requests are made - everything comes from the Pact file.
        """
        from pact import Verifier
        
        # Find all pact files
        pact_files = [f for f in PACTS_DIR.glob("*.json") if not f.name.startswith(".")]
        
        if not pact_files:
            pytest.skip("No pact files found - run consumer tests first to generate them")
        
        print(f"\n📋 Found {len(pact_files)} pact file(s) to verify")
        
        # Verify against each pact file
        # The verifier replays ALL interactions from the pact file
        all_passed = True
        for pact_file in pact_files:
            print(f"\n{'='*60}")
            print(f"📄 Verifying: {pact_file.name}")
            print(f"{'='*60}")
            
            try:
                # Create verifier with pact-python v2 API
                # - name: Provider name
                # - add_source: Path to pact file (source of truth)
                # - add_transport: Provider URL to verify against
                verifier = (
                    Verifier('RiskAlgoService')
                    .add_source(str(pact_file))
                    .add_transport(url=PROVIDER_URL)
                )
                
                # This is where the magic happens:
                # - Verifier reads interactions from pact file
                # - Sends requests to provider
                # - Compares responses against contract expectations
                verifier.verify()
                
                print(f"✅ {pact_file.name}: All interactions verified!")
                    
            except Exception as e:
                print(f"❌ {pact_file.name}: Verification failed: {e}")
                all_passed = False
        
        print(f"\n{'='*60}")
        if all_passed:
            print("✅ PROVIDER VERIFICATION PASSED")
            print("   Provider satisfies all consumer contracts!")
            print("   The Pact file was the source of truth.")
        else:
            print("❌ PROVIDER VERIFICATION FAILED")
            print("   Provider does not satisfy consumer contracts.")
            print("   Fix the provider to match the Pact contract.")
        print(f"{'='*60}\n")
        
        assert all_passed, "Provider verification failed - see output above"


class TestPactFileValidation:
    """
    Validates that Pact files exist and are properly formatted.
    These tests only read the Pact file - no server interaction.
    """
    
    def test_pact_files_exist(self):
        """Verify that pact files have been generated."""
        pact_files = list(PACTS_DIR.glob("*.json"))
        pact_files = [f for f in pact_files if not f.name.startswith(".")]
        
        assert len(pact_files) > 0, (
            "No pact files found in pacts/ directory.\n"
            "Run consumer tests first: cd consumer-ts && npm test"
        )
        
        print(f"\n✅ Found {len(pact_files)} pact file(s):")
        for pact_file in pact_files:
            print(f"   - {pact_file.name}")
    
    def test_pact_file_structure(self):
        """Verify pact files have valid structure."""
        import json
        
        pact_files = [f for f in PACTS_DIR.glob("*.json") if not f.name.startswith(".")]
        
        if not pact_files:
            pytest.skip("No pact files to validate")
        
        for pact_file in pact_files:
            with open(pact_file) as f:
                pact = json.load(f)
            
            # Verify required fields
            assert "consumer" in pact, f"{pact_file.name}: Missing 'consumer' field"
            assert "provider" in pact, f"{pact_file.name}: Missing 'provider' field"
            assert "interactions" in pact, f"{pact_file.name}: Missing 'interactions' field"
            
            # Verify interactions
            interactions = pact["interactions"]
            assert len(interactions) > 0, f"{pact_file.name}: No interactions defined"
            
            print(f"\n✅ {pact_file.name}:")
            print(f"   Consumer: {pact['consumer']['name']}")
            print(f"   Provider: {pact['provider']['name']}")
            print(f"   Interactions: {len(interactions)}")
            
            for interaction in interactions:
                desc = interaction.get("description", "Unknown")
                method = interaction.get("request", {}).get("method", "?")
                path = interaction.get("request", {}).get("path", "?")
                print(f"     - {method} {path}: {desc}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

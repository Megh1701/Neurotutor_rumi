import subprocess
import sys


# List of packages to check
packages = [
    'streamlit',
    'langgraph',
    'langchain',
    'langchain-ollama',
    'langchain-community',
    'chromadb',
    'networkx',
    'pandas',
    'numpy',
    'torch',
    'ollama',
    'faiss-cpu',
    'requests',
    'python-dotenv',
    'pypdf',
    'python-multipart',
    'plotly',
    'matplotlib',
    'seaborn',
    'typing-extensions',
    'pydantic'
]

print("\n" + "="*60)
print("📦 CHECKING INSTALLED PACKAGES")
print("="*60)

installed = []
missing = []

for package in packages:
    try:
        # Try to import the package
        __import__(package.replace('-', '_'))
        installed.append(package)
    except ImportError:
        missing.append(package)

print(f"\n✅ Installed: {len(installed)}")
for pkg in installed:
    print(f"  ✓ {pkg}")

print(f"\n❌ Missing: {len(missing)}")
for pkg in missing:
    print(f"  ✗ {pkg}")

if missing:
    print("\n💡 To install missing packages:")
    print(f"pip install {' '.join(missing)}")
else:
    print("\n🎉 All packages are installed!")
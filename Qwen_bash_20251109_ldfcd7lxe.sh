# Clone the repository
git clone https://github.com/yourusername/sworms-lite.git
cd sworms-lite

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the system
python -c "import asyncio; from src.sworms_lite import main; asyncio.run(main())"